
import cv2
import easyocr
import numpy as np
import re
import string
from .bq_db import SmashDatabase
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from os.path import dirname, join
from .yt_obj import GetYoutube
JST = timezone(timedelta(hours=+9), 'JST')

# 画像処理結果を入れるデータクラス
@dataclass
class GameData:
    id: int = -1
    fighter_id_1p: int = -1
    fighter_name_1p: str = None
    fighter_name_1p_en: str = None
    fighter_id_2p: int = -1
    fighter_name_2p: str = None
    fighter_name_2p_en: str = None
    target_player_name: str = None
    target_player_is_1p: bool = None
    target_player_is_win: str = None
    game_start_datetime: datetime = None
    game_start_url: str = None
    game_finish_datetime: datetime = None
    game_finish_url: str = None
    title: str = None
    category: str = None
    
    def __init__(self, inputs, index, categories={'smashmate':['めいと', 'メイト','レート', 'レーティング'], 'VIP':['VIP']}):
        self.target_player_name = inputs["yt_infos"][index]["channel"] if inputs["target_player_name"]=="auto" else inputs["target_player_name"]
        self.title = inputs["yt_infos"][index]["title"]
        self.category = self.get_category(categories) if inputs["target_category"]=="auto" else inputs["target_category"]
        
    def get_category(self, categories): 
        for k,V in categories.items():
            for v in V:
                if v in self.title: return k
        return 'other'

# 画像処理パラメータを入れるデータクラス
@dataclass
class Parameter:
    # 空辞書、空リストを用意する場合はfiled(default_factory)を使用 https://qiita.com/plumfield56/items/5794170fae2c4cabc5be
    # Web UI からの入力パラメータ
    yt_info: list = field(default_factory=list)
    crop: dict = field(default_factory=dict)
    target_1p_fighters: list = field(default_factory=list)
    target_lang: str = None
    fighter_lists: list = field(default_factory=list)
    # 画像処理パラメータ
    initial: int = 0
    duration: int = 0
    img: dict = field(default_factory=dict)
    edge: dict = field(default_factory=dict)
    line: dict = field(default_factory=dict)
    recog_txt: dict = field(default_factory=dict)
    easyocr: dict = field(default_factory=dict)
    
    def __init__(
            self, inputs, index,
            initial=0, duration=0,
            img=None, imw_path=None, dsize=[(1024,576), (448*2,252*2), (448,252), (1280,720)],
            edge={"sigma":0.33, "kernel":0},
            line={
                "rho":1, "theta":np.pi/180, "threshold":200,
                "target_rho_list":[[17.0,17.0],[33.0,33.0], [85.0,87.0], [90.0,90.0], [104.0,104.0]], 
                "target_theta":1.535889744758606, "error_range":10**-14, "target_line_num":[1,4]
            },
            recog_txt={"start":[-4,-5,-3,-5,-4], "end":[None,-1,None,-2,-1], "range":3},
            easyocr={
                "name_allowlist": 'irt'+string.ascii_uppercase, "num_allowlist":string.digits, 
                "detail":0, "lang_list": ['en'], "verbose":False
            }
        ):
        self.yt_info = inputs["yt_infos"][index]
        self.crop = inputs["crop"]
        self.target_1p_fighters = inputs["target_1p_fighters"]
        self.target_lang = inputs["target_lang"]
        lang_suf = '' if self.target_lang=="jp" else '_en'
        lang_suf2 = '' if self.target_lang=="en" else '_en'
        self.fighter_lists = [
            inputs["fighter_df"][f'recog_name{lang_suf}'].to_list(),
            inputs["fighter_df"]['fighter_id'].to_list(),
            inputs["fighter_df"][f'fighter_name{lang_suf}'].to_list(),
            inputs["fighter_df"][f'fighter_name{lang_suf2}'].to_list()
        ]
        
        self.initial = self.get_start_sec(initial) if initial==0 else initial
        self.duration = self.yt_info["duration"] if duration==0 else duration
        self.get_img(img, imw_path, dsize)
        self.edge = edge
        self.line = line
        self.recog_txt = recog_txt
        self.easyocr = easyocr
        
    def get_start_sec(self, initial):
        for game_end_url in SmashDatabase().select_analysis_data()['game_end_url'].to_list():
            if self.yt_info['original_url'] in game_end_url:
                initial = max([initial, int(re.findall(r'\d+',game_end_url)[-1])])
        return initial
        
    def get_img(self, img, imw_path, dsize):
        if img==None:
            img = {
                "g_start": {
                    "img": None, "temp_img": None, "temp_match_val": -1, "dsize": dsize[0],
                    "crop": {"crop1": {'pt1': [0,0], 'pt2': [dsize[0][0],int(dsize[0][1]*0.2)]}}
                },
                "g_fighter": {
                    "img_1p": None, "img_2p": None, "dsize": dsize[1],
                    "crop_1p": {"crop1": {'pt1': [int(dsize[1][0]*0.10),int(dsize[1][1]*0.02)], 'pt2': [int(dsize[1][0]*0.43),int(dsize[1][1]*0.15)]}},
                    "crop_2p": {"crop1": {'pt1':[int(dsize[1][0]*0.60),int(dsize[1][1]*0.02)], 'pt2':[int(dsize[1][0]*0.93),int(dsize[1][1]*0.15)]}}
                },
                "g_finish": {
                    "img": None, "temp_img": "gameset.png" if self.target_lang=="jp" else "game.png", "temp_match_val": 0.463, "dsize": dsize[2], #match_val=0.474
                    "crop": {
                        "crop1": {
                            'pt1':[int(dsize[2][0]*0.21), int(dsize[2][1]*0.16)] if self.target_lang=="jp" else [int(dsize[2][0]*0.18),int(dsize[2][1]*0.27)], 
                            'pt2':[int(dsize[2][0]*0.79), int(dsize[2][1]*0.64)] if self.target_lang=="jp" else [int(dsize[2][0]*0.81),int(dsize[2][1]*0.52)]
                        }
                    }
                },
                "g_result": {
                    "img_1p": None, "img_2p": None, "img_rs": None, "dsize": dsize[3],
                    "crop_1p": {"crop1": {'pt1':[int(dsize[3][0]*0.266),int(dsize[3][1]*0.847)], 'pt2':[int(dsize[3][0]*0.343),int(dsize[3][1]*0.927)]}},
                    "crop_2p": {"crop1": {'pt1':[int(dsize[3][0]*0.651),int(dsize[3][1]*0.847)], 'pt2':[int(dsize[3][0]*0.728),int(dsize[3][1]*0.927)]}},
                    "crop_rs": {"crop1": {'pt1':[int(dsize[3][0]*0.000),int(dsize[3][1]*0.600)], 'pt2':[int(dsize[3][0]*0.500),int(dsize[3][1]*1.000)]}}
                },
                "imw_path": dirname(__file__) if imw_path==None else imw_path
            }
        img["g_start"]["temp_img"] = self.get_templater(
            join(dirname(__file__),f'./images/{img["g_start"]["temp_img"]}'), img["g_start"]["dsize"]
        ) if img["g_start"]["temp_img"]!=None else None
        img["g_finish"]["temp_img"] = self.get_templater(
            join(dirname(__file__),f'./images/{img["g_finish"]["temp_img"]}'), img["g_finish"]["dsize"]
        ) if img["g_finish"]["temp_img"]!=None else None
        self.img = img
    
    def get_templater(self, temp_img_path, dsize=None):
        temp_img = cv2.imread(temp_img_path, 0)
        if dsize!=None:
            h,w = temp_img.shape
            temp_img = cv2.resize(temp_img, (int(w*(dsize[0]/1920)), int(h*(dsize[1]/1080))))
        return temp_img

# ゲーム画面解析クラス
class EsportsAnalysis:
    def __init__(self, param:Parameter, sec={"interval":10, "game":40}):
        self.param = param
        self.count = 0
        self.states = {'skip_interval':False, 'skip_game':False, 'find_game_start':True, 'get_fighter_name':False, 'find_game_finish': False, 'get_game_result':False}
        self.state = None
        self.img = None
        self.sec = sec

    # GameDataインスタンス生成
    def set_game_data(self, inputs, index):
        self.game_data = GameData(inputs, index)
        self.sec_buf = 0

    # 処理状態遷移
    def trans(self, next_state):
        for state in self.states.keys():
            if state==next_state: self.states[state] = True
            else: self.states[state] = False
    
    # ゲーム開始画面とゲーム終了画面の検出解析：https://qiita.com/kenshin-627/items/6c3f07b8c2d7c72ee706
    def find_game(self):
        img = self.param.img["g_start"]["img"] if self.states["find_game_start"] else self.param.img["g_finish"]["img"]
        temp_img = self.param.img["g_start"]["temp_img"] if self.states["find_game_start"] else self.param.img["g_finish"]["temp_img"]
        temp_match_val = self.param.img["g_start"]["temp_match_val"] if self.states["find_game_start"] else self.param.img["g_finish"]["temp_match_val"]
        if temp_img is None: return self.detect_line(img, self.detect_edge(img))
        else: return self.temp_match(img, temp_img, temp_match_val)
    
    # エッジ検出：cv2.Canny(): Canny法によるエッジ検出の自動化 https://qiita.com/kotai2003/items/662c33c15915f2a8517e
    def detect_edge(self, img):
        img_blur = cv2.GaussianBlur(img, (self.param.edge["kernel"], self.param.edge["kernel"]), self.param.edge["sigma"])

        # Automatic Thresholds Finding
        med_val = np.median(img_blur)
        min_val = int(max(0, (1.0 - self.param.edge["sigma"]) * med_val))
        max_val = int(max(255, (1.0 + self.param.edge["sigma"]) * med_val))
    
        return cv2.Canny(img_blur, threshold1=min_val, threshold2=max_val, L2gradient=True)

    # 直線検出(ゲーム開始画面検出)
    def detect_line(self, img, img_edges):
        # Hough変換で直線を検出
        img_lines = cv2.HoughLines(img_edges, rho=self.param.line["rho"], theta=self.param.line["theta"], threshold=self.param.line["threshold"])
        # 直線が検出されたときだけ，このフレームが対戦開始タイミングかどうかを判定する
        if not img_lines is None:
            if self.is_start(img, img_lines):
                return True
        return False
    
    # 対戦開始のタイミングならTrue
    def is_start(self, img, img_lines):
        # いい感じの直線の数
        line_count = 0
        for line in img_lines:
            rho, theta = line[0]
            # いい感じの角度と位置の直線ならカウントする
            if np.abs(theta - self.param.line["target_theta"]) < self.param.line["error_range"]:
                for target_rho in self.param.line["target_rho_list"]:
                    # 直線が画面の上部かどうか(上部でないなら次の線)
                    if target_rho[0]<=rho and rho<=target_rho[1]:
                        line_count += 1
                        break
        # 1～4本あれば対戦開始のタイミング
        if self.param.line["target_line_num"][0]<=line_count and line_count<=self.param.line["target_line_num"][1]:
            return True
        else: return False
    
    # テンプレートマッチング(ゲーム終了画面検出)：対戦終了のタイミングならTrue
    def temp_match(self, img, temp_img, match_val): 
        result = cv2.matchTemplate(img, temp_img, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        self.temp_match_max_val = max_val
        if(match_val<max_val and max_val<1.0):
            return True
        else:
            return False
    
    # ファイター名取得
    def get_fighter_name(self, img):
        txt = self.easyOCR(img, self.param.easyocr["name_allowlist"])
        for recog_name, fighter_id, fighter_name, fighter_name_en in zip(self.param.fighter_lists[0], self.param.fighter_lists[1], self.param.fighter_lists[2], self.param.fighter_lists[3]):
            if txt==recog_name: return fighter_id, fighter_name, fighter_name_en, txt
        name_lists = []
        for recog_name, fighter_id, fighter_name, fighter_name_en in zip(self.param.fighter_lists[0], self.param.fighter_lists[1], self.param.fighter_lists[2], self.param.fighter_lists[3]):
            st_cnt = 0
            name_txt = recog_name[:len(txt)]
            for st, nst in zip(txt, name_txt):
                if st==nst: st_cnt+=1
            if abs(len(txt)-st_cnt)<=1: return fighter_id, fighter_name, fighter_name_en, txt
            st_rcnt = 0
            for rst, rnst in zip(txt[::-1], name_txt[::-1]):
                if rst==rnst: st_rcnt+=1
            if abs(len(txt)-st_rcnt)<=1: return fighter_id, fighter_name, fighter_name_en, txt
            name_lists.append([st_cnt+st_rcnt, fighter_id, fighter_name, fighter_name_en, txt])
        # 2次元リストを降順にソートする方法 https://af-e.net/python-two-dimensional-list-sort/#index_id4
        return sorted(name_lists, key=lambda x: x[0], reverse=True)[0][1:]
    
    # ゲーム結果取得
    def get_game_result(self):
        damage_1p = self.easyOCR(self.param.img["g_result"]["img_1p"], self.param.easyocr["num_allowlist"])
        damage_2p = self.easyOCR(self.param.img["g_result"]["img_2p"], self.param.easyocr["num_allowlist"])
        if self.game_data.fighter_name_1p in self.param.target_1p_fighters:
            self.game_data.target_player_is_1p = True
            if re.compile('\d').search(damage_1p) and damage_2p=='': self.game_data.target_player_is_win = True
            elif re.compile('\d').search(damage_2p) and damage_1p=='': self.game_data.target_player_is_win = False
            else: self.game_data.target_player_is_win = None
        else:
            self.game_data.target_player_is_1p = False
            if re.compile('\d').search(damage_1p) and damage_2p=='': self.game_data.target_player_is_win = False
            elif re.compile('\d').search(damage_2p) and damage_1p=='': self.game_data.target_player_is_win = True
            else: self.game_data.target_player_is_win = None
    
    # ゲーム結果取得2
    def get_game_result2(self):
        allowlist = re.sub('[.&/ -]', '', self.game_data.fighter_name_1p+self.game_data.fighter_name_2p)
        txt = self.easyOCR(self.param.img["g_result"]["img_rs"], allowlist)
        target_fighter = re.sub('[.&/ -]', '', self.game_data.fighter_name_1p if self.game_data.fighter_name_1p in self.param.target_1p_fighters else self.game_data.fighter_name_2p)
        st_cnt=0
        for st, tst in zip(txt, target_fighter[:len(txt)]):
            if st==tst: st_cnt+=1
        self.game_data.target_player_is_win = True if abs(len(target_fighter)-st_cnt)<=3 else False
    
    # OCRでファイター名検出
    def easyOCR(self, img, allowlist=string.ascii_letters+string.digits):
        reader = easyocr.Reader(lang_list=self.param.easyocr["lang_list"], verbose=self.param.easyocr["verbose"])
        txt = ''
        for ocr_res in reader.readtext(img, allowlist=allowlist, detail=self.param.easyocr["detail"]):
            txt+=ocr_res
        return re.sub(' ', '', txt)
    
    # 画像処理実行
    def execute_analysis(self, index, sec):
        # ゲーム終了画面～次のゲーム開始画面までの間隔をスキップ
        if self.states['skip_interval']:
            self.count += 1
            if self.count==self.sec["interval"]: self.trans('find_game_start')
            else: return 0
        # ゲーム開始画面検出処理
        if self.states['find_game_start']:
            self.img = GetYoutube.get_yt_image(self.param.yt_info, sec, gray=True)
            if self.img is None: return 1
            self.param.img["g_start"]["img"] = GetYoutube.set_yt_image(
                self.param.crop | self.param.img['g_start']['crop'], self.img, crop=True,
                pre_dsize=self.param.img["g_start"]["dsize"],
            )
            if self.find_game(): self.trans('get_fighter_name')
        # ファイター名取得処理
        if self.states['get_fighter_name']:
            self.param.img["g_fighter"]["img_1p"] = GetYoutube.set_yt_image(
                self.param.crop | self.param.img['g_fighter']['crop_1p'], self.img, crop=True,
                pre_dsize=self.param.img["g_fighter"]["dsize"],
            )
            self.param.img["g_fighter"]["img_2p"] = GetYoutube.set_yt_image(
                self.param.crop | self.param.img['g_fighter']['crop_2p'], self.img, crop=True,
                pre_dsize=self.param.img["g_fighter"]["dsize"],
            )
            self.game_data.fighter_id_1p, self.game_data.fighter_name_1p, self.game_data.fighter_name_1p_en, easyOCR_txt_1p = self.get_fighter_name(self.param.img["g_fighter"]["img_1p"])
            self.game_data.fighter_id_2p, self.game_data.fighter_name_2p, self.game_data.fighter_name_2p_en, easyOCR_txt_2p = self.get_fighter_name(self.param.img["g_fighter"]["img_2p"])
            if ((self.game_data.fighter_name_1p in self.param.target_1p_fighters and self.game_data.fighter_id_2p>0) or 
                (self.game_data.fighter_id_1p>0 and self.game_data.fighter_name_2p in self.param.target_1p_fighters)):
                self.count=0
                self.trans('skip_game')
                self.game_data.game_start_datetime = datetime.fromtimestamp(self.param.yt_info["release_timestamp"]+sec, JST).strftime('%Y-%m-%d %T')
                self.game_data.game_start_url = f'{self.param.yt_info["original_url"]}&t={sec}s'
                yt_id = self.param.yt_info['original_url'].split('=')[1]
                inside_vs = f"{self.game_data.fighter_name_1p} vs {self.game_data.fighter_name_2p}"
                GetYoutube.get_yt_image(
                    self.param.yt_info, sec, (480,270), 
                    imw_path=join(self.param.img["imw_path"], f"static/image{index}_{yt_id}_{sec}_{re.sub('[.&/ -]', '', inside_vs)}.jpg")
                )
                if self.img is None: return 1
            else:
                self.trans('find_game_start')
        # ゲーム開始画面～ゲーム終了画面までの間隔をスキップ
        if self.states['skip_game']:
            self.count += 1
            if self.count==self.sec["game"]: self.trans('find_game_finish')
            else: return 0
        # ゲーム終了画面検出処理
        if self.states['find_game_finish']:
            self.img = GetYoutube.get_yt_image(self.param.yt_info, sec, gray=True)
            if self.img is None: return 1
            yt_id = self.param.yt_info['original_url'].split('=')[1]
            self.param.img["g_finish"]["img"] = GetYoutube.set_yt_image(
                self.param.crop | self.param.img['g_finish']['crop'], self.img, crop=True,
                pre_dsize=self.param.img["g_finish"]["dsize"],
            )
            if self.find_game(): self.trans('get_game_result')
        # ゲーム結果取得処理
        if self.states['get_game_result']:
            self.sec_buf = sec
            self.param.img["g_result"]["img_1p"] = GetYoutube.set_yt_image(
                self.param.crop | self.param.img['g_result']['crop_1p'], self.img, crop=True,
                pre_dsize=self.param.img["g_result"]["dsize"],
            )
            self.param.img["g_result"]["img_2p"] = GetYoutube.set_yt_image(
                self.param.crop | self.param.img['g_result']['crop_2p'], self.img, crop=True,
                pre_dsize=self.param.img["g_result"]["dsize"],
            )
            self.get_game_result()
            if self.game_data.target_player_is_win==None:
                self.sec_buf+=1
                self.img = GetYoutube.get_yt_image(self.param.yt_info, self.sec_buf, gray=True)
                if self.img is None: return 1
                self.param.img["g_result"]["img_1p"] = GetYoutube.set_yt_image(
                    self.param.crop | self.param.img['g_result']['crop_1p'], self.img, crop=True,
                    pre_dsize=self.param.img["g_result"]["dsize"],
                )
                self.param.img["g_result"]["img_2p"] = GetYoutube.set_yt_image(
                    self.param.crop | self.param.img['g_result']['crop_2p'], self.img, crop=True,
                    pre_dsize=self.param.img["g_result"]["dsize"],
                )
                self.get_game_result()
            if self.game_data.target_player_is_win==None:
                self.sec_buf+=6.25
                self.img = GetYoutube.get_yt_image(self.param.yt_info, self.sec_buf, gray=True)
                if self.img is None: return 1
                self.param.img["g_result"]["img_rs"] = GetYoutube.set_yt_image(
                    self.param.crop | self.param.img['g_result']['crop_rs'], self.img, crop=True,
                    pre_dsize=self.param.img["g_result"]["dsize"],
                )
                self.get_game_result2()
            if self.game_data.target_player_is_win!=None:
                self.game_data.game_finish_datetime = datetime.fromtimestamp(self.param.yt_info['release_timestamp']+self.sec_buf, JST).strftime('%Y-%m-%d %T')
                self.game_data.game_finish_url = f"{self.param.yt_info['original_url']}&t={self.sec_buf}s"
                if self.param.target_lang=="en":
                    tmp = self.game_data.fighter_name_1p
                    self.game_data.fighter_name_1p = self.game_data.fighter_name_1p_en
                    self.game_data.fighter_name_1p_en = tmp
                    tmp = self.game_data.fighter_name_2p
                    self.game_data.fighter_name_2p = self.game_data.fighter_name_2p_en
                    self.game_data.fighter_name_2p_en = tmp
                self.count=0
                self.trans('skip_interval')
                yt_id = self.param.yt_info['original_url'].split('=')[1]
                inside_res = "WIN" if self.game_data.target_player_is_win else "LOSE"
                GetYoutube.get_yt_image(
                    self.param.yt_info, self.sec_buf, (480,270), 
                    imw_path=join(self.param.img["imw_path"], f"static/image{index}_{yt_id}_{self.sec_buf}_{inside_res}.jpg")
                )
                if self.img is None: return 1
            else:
                self.trans('get_game_result')
        # 現在の処理状態を更新
        for k,v in self.states.items():
            if v==True: self.state = k

if __name__=="__main__":
    pass
    