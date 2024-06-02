
import cv2
import easyocr
import numpy as np
import pandas as pd
import re
import string

from .bq_db import SmashDatabase
# from bq_db import SmashDatabase
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from os.path import dirname, join
from threading import Thread
from tqdm import tqdm
from .yt_obj import GetYoutube
# from yt_obj import GetYoutube
JST = timezone(timedelta(hours=+9), 'JST')

@dataclass
class GameData:
    id: int = -1
    fighter_id_1p: int = -1
    fighter_name_1p: str = None
    fighter_id_2p: int = -1
    fighter_name_2p: str = None
    target_player_name: str = None
    target_player_is_1p: bool = None
    target_player_is_win: str = None
    game_start_datetime: datetime = None
    game_start_url: str = None
    game_finish_datetime: datetime = None
    game_finish_url: str = None
    title: str = None
    category: str = None
    
    def __init__(self, inputs, index, categories={'VIP':['VIP'], 'smashmate':['めいと', 'メイト','レート', 'レーティング']},):
        self.target_player_name = inputs["yt_infos"][index]["channel"] if inputs["target_player_name"]=="auto" else inputs["target_player_name"]
        self.title = inputs["yt_infos"][index]["title"]
        self.category = self.get_category(categories) if inputs["target_category"]=="auto" else inputs["target_category"]
        
    def get_category(self, categories): 
        for k,V in categories.items():
            for v in V:
                if v in self.title: return k
        return 'other'

# 空辞書、空リストを用意する場合はfiled(default_factory)を使用 https://qiita.com/plumfield56/items/5794170fae2c4cabc5be
@dataclass
class Parameter:
    yt_info: list = field(default_factory=list)
    crop: dict = field(default_factory=dict)
    target_1p_fighters: list = field(default_factory=list)
    fighter_lists: list = field(default_factory=list)
    
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
                # ↓絶対に消さないこと
                # "target_rho_list":[[17.0,17.0],[33.0,33.0], [86.0,87.0], [90.0,90.0], [104.0,104.0]], 
                "target_rho_list":[[17.0,17.0],[33.0,33.0], [85.0,87.0], [90.0,90.0], [104.0,104.0]], 
                "target_theta":1.535889744758606, "error_range":10**-14, "target_line_num":[1,4]
            },
            # ↓絶対に消さないこと
            # recog_txt = {"start":[-4,-5,-5,-3,-4], "end":[None,-1,-2,None,-1], "range":3},
            recog_txt={"start":[-4,-5,-3,-5,-4], "end":[None,-1,None,-2,-1], "range":3},
            easyocr={
                "name_allowlist": 'irt'+string.ascii_uppercase, "num_allowlist":string.digits, 
                "detail":0, "lang_list": ['en'], "verbose":False
            }
        ):
        self.yt_info = inputs["yt_infos"][index]
        self.crop = inputs["crop"]
        self.target_1p_fighters = inputs["target_1p_fighters"]
        self.fighter_lists = [inputs["fighter_df"]['recog_name'].to_list(), inputs["fighter_df"]['fighter_id'].to_list(), inputs["fighter_df"]['fighter_name'].to_list()]
        
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
                    "crop_1p": {"crop1": {'pt1': [int(dsize[1][0]*0.10),int(dsize[1][1]*0.02)], 'pt2': [int(dsize[1][0]*0.43),int(dsize[1][1]*0.13)]}},
                    "crop_2p": {"crop1": {'pt1':[int(dsize[1][0]*0.60),int(dsize[1][1]*0.02)], 'pt2':[int(dsize[1][0]*0.93),int(dsize[1][1]*0.13)]}}
                },
                "g_finish": {
                    "img": None, "temp_img": "gameset.png", "temp_match_val": 0.474, "dsize": dsize[2],
                    "crop": {"crop1": {'pt1':[int(dsize[2][0]*0.21),int(dsize[2][1]*0.16)], 'pt2':[int(dsize[2][0]*0.79),int(dsize[2][1]*0.64)]}}
                },
                "g_result": {
                    "img_1p": None, "img_2p": None, "img_rs": None, "dsize": dsize[3],
                    "crop_1p": {"crop1": {'pt1':[int(dsize[3][0]*0.266),int(dsize[3][1]*0.847)], 'pt2':[int(dsize[3][0]*0.343),int(dsize[3][1]*0.927)]}},
                    "crop_2p": {"crop1": {'pt1':[int(dsize[3][0]*0.651),int(dsize[3][1]*0.847)], 'pt2':[int(dsize[3][0]*0.728),int(dsize[3][1]*0.927)]}},
                    "crop_rs": {"crop1": {'pt1':[int(dsize[3][0]*0.000),int(dsize[3][1]*0.600)], 'pt2':[int(dsize[3][0]*0.500),int(dsize[3][1]*1.000)]}}
                },
                "imw_path": imw_path if imw_path==None else dirname(__file__)
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
                
class EsportsAnalysis:
    def __init__(self, param:Parameter, sec={"interval":28, "game":56}):
        self.param = param
        self.count = 0
        self.states = {'skip_interval':True, 'skip_game':False, 'find_game_start':False, 'get_fighter_name':False, 'find_game_finish': False, 'get_game_result':False}
        self.state = 'skip_interval'
        self.img = None
        self.sec = sec

    def set_game_data(self, inputs, index):
        self.game_data = GameData(inputs, index)
        self.sec_buf = 0

    def trans(self, next_state):
        for state in self.states.keys():
            if state==next_state: self.states[state] = True
            else: self.states[state] = False
        
    def find_game(self):
        img = self.param.img["g_start"]["img"] if self.states["find_game_start"] else self.param.img["g_finish"]["img"]
        temp_img = self.param.img["g_start"]["temp_img"] if self.states["find_game_start"] else self.param.img["g_finish"]["temp_img"]
        temp_match_val = self.param.img["g_start"]["temp_match_val"] if self.states["find_game_start"] else self.param.img["g_finish"]["temp_match_val"]
        if temp_img is None: return self.detect_line(img, self.detect_edge(img))
        else: return self.temp_match(img, temp_img, temp_match_val)
        
    def detect_edge(self, img):
        img_blur = cv2.GaussianBlur(img, (self.param.edge["kernel"], self.param.edge["kernel"]), self.param.edge["sigma"])

        # Automatic Thresholds Finding
        med_val = np.median(img_blur)
        min_val = int(max(0, (1.0 - self.param.edge["sigma"]) * med_val))
        max_val = int(max(255, (1.0 + self.param.edge["sigma"]) * med_val))
    
        return cv2.Canny(img_blur, threshold1=min_val, threshold2=max_val, L2gradient=True)

    def detect_line(self, img, img_edges):
        # Hough変換で直線を検出
        img_lines = cv2.HoughLines(img_edges, rho=self.param.line["rho"], theta=self.param.line["theta"], threshold=self.param.line["threshold"])
        if not img_lines is None:
            if self.is_start(img, img_lines):
                return True
        return False
    
    # 対戦開始のタイミングならTrue
    def is_start(self, img, img_lines):
        for d in range(256):
            if d**3 >= self.param.line["target_line_num"][1]: break
        colors = [(r,g,b) for r in range(0,256,int(255/(d-1))) for g in range(0,256,int(255/(d-1))) for b in range(0,256,int(255/(d-1)))]
        img_copy = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        # いい感じの直線の数
        line_count = 0
        print(f"img_lines = {img_lines}")
        for line in img_lines:
            rho, theta = line[0]
            # いい感じの角度の直線ならカウントして描画する
            if np.abs(theta - self.param.line["target_theta"]) < self.param.line["error_range"]:
                for target_rho in self.param.line["target_rho_list"]:
                    if target_rho[0]<=rho and rho<=target_rho[1]:
                        line_count += 1
                        if line_count <= self.param.line["target_line_num"][1]:
                            img_copy = self.draw_target_line(img_copy, rho, theta, colors[line_count-1])      
                        break
        # 2～6本あれば対戦開始のタイミング
        if self.param.line["target_line_num"][0]<=line_count and line_count<=self.param.line["target_line_num"][1]:
            self.param.img["g_start"]["img"] = img_copy
            return True
        else: return False
        
    def draw_target_line(self, img_copy, rho, theta, color):
        h, w = img_copy.shape[:2]
        # 直線の式を式変形すればcalc_yの式がもとまる
        calc_y = lambda x: rho / np.sin(theta) - x * np.cos(theta) / np.sin(theta)
        x1, y1 = 0, calc_y(0)
        x2, y2 = w, calc_y(w)
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
        # 直線を描画
        return cv2.line(img_copy, (x1, y1), (x2, y2), color, 2)

    def temp_match(self, img, temp_img, match_val): #match_val=0.474
        result = cv2.matchTemplate(img, temp_img, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if(match_val<max_val and max_val<1.0):
            return True
        else:
            return False
    
    def get_fighter_name(self, img):
        txt = self.easyOCR(img, self.param.easyocr["name_allowlist"])
        name_lists_copy = []
        for start, end in zip(self.param.recog_txt["start"], self.param.recog_txt["end"]):
            name_lists = []
            for recog_name, fighter_id, fighter_name in zip(self.param.fighter_lists[0], self.param.fighter_lists[1], self.param.fighter_lists[2]):
                if (len(recog_name[start:end])>=self.param.recog_txt["range"]) and (recog_name[start:end] in txt): 
                    # print("fighter_id, fighter_name, txt =", fighter_id, fighter_name, txt)
                    # return fighter_id, fighter_name, txt
                    name_lists.append([fighter_id, fighter_name, txt])
            print(f"start, end = {start}, {end}")
            print(f"name_lists = {name_lists}")
            if len(name_lists)==1 and name_lists[0][1] in self.param.target_1p_fighters:
                return name_lists[0]
            # for id, name, t in name_lists:
            #     if name in self.param.inputs['target_1p_fighters'] and self.game_data.fighter_name_1p==None:
            #         print(f"start, end = {start}, {end}")
            #         return id, name, t
            if len(name_lists)>0 and len(name_lists_copy)==0:
                name_lists_copy = name_lists
        print(f"name_lists_copy = {name_lists_copy}")
        if len(name_lists_copy)==0: name_lists_copy = [[0, 'other', txt]]
        name_max = max([name for id, name, t in name_lists_copy])
        for name_list in name_lists_copy:
            if name_max in name_list:
                print(f"name_list = {name_list}")
                return name_list
        # print("fighter_id, fighter_name, txt = 0 other", txt)
        # return 0, 'other', txt
    
    def get_game_result(self):
        damage_1p = self.easyOCR(self.param.img["g_result"]["img_1p"], self.param.easyocr["num_allowlist"])
        damage_2p = self.easyOCR(self.param.img["g_result"]["img_2p"], self.param.easyocr["num_allowlist"])
        print("damage_1p:", damage_1p)
        print("damage_2p:", damage_2p)
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
        
    def get_game_result2(self):
        allowlist = re.sub('[.& ]', '', self.game_data.fighter_name_1p+self.game_data.fighter_name_2p)
        target_fighter = self.game_data.fighter_name_1p if self.game_data.fighter_name_1p in self.param.target_1p_fighters else self.game_data.fighter_name_2p
        str_cnt=0
        ocr_txt = set(self.easyOCR(self.param.img["g_result"]["img_rs"], allowlist))
        print(ocr_txt)
        for ocr_str in ocr_txt:
            if ocr_str in target_fighter: str_cnt+=1
            if str_cnt==2:
                self.game_data.target_player_is_win = True
                break
        if str_cnt<2: self.game_data.target_player_is_win = False
    
    def easyOCR(self, img, allowlist=string.ascii_letters+string.digits):
        reader = easyocr.Reader(lang_list=self.param.easyocr["lang_list"], verbose=self.param.easyocr["verbose"])
        txt = ''
        for ocr_res in reader.readtext(img, allowlist=allowlist, detail=self.param.easyocr["detail"]):
            txt+=ocr_res
        return re.sub(' ', '', txt)
    
    def execute_analysis(self, index, sec):
        if self.states['skip_interval']:
            self.count += 1
            if self.count==self.sec["interval"]: self.trans('find_game_start')
            else: return 0
        if self.states['find_game_start']:
            print(f"sec = {sec}")
            self.img = GetYoutube.get_yt_image(self.param.yt_info, sec, gray=True)
            self.param.img["g_start"]["img"] = GetYoutube.set_yt_image(
                self.param.crop | self.param.img['g_start']['crop'], self.img, crop=True,
                pre_dsize=self.param.img["g_start"]["dsize"],
                # imw_path=join(dirname(__file__), f'image{index}_{sec}_top.jpg')
            )
            # print(f"sec = {sec}")
            if self.find_game():
                # GetYoutube.set_yt_image(
                #     img=self.param.img["g_start"]["img"],
                #     imw_path=join(dirname(__file__), f'image{index}_{sec}_top.jpg')
                # )
                self.trans('get_fighter_name')
        if self.states['get_fighter_name']:
            self.param.img["g_fighter"]["img_1p"] = GetYoutube.set_yt_image(
                self.param.crop | self.param.img['g_fighter']['crop_1p'], self.img, crop=True,
                pre_dsize=self.param.img["g_fighter"]["dsize"],
                # imw_path=join(dirname(__file__), f'image{index}_{sec}_topL.jpg')
            )
            self.param.img["g_fighter"]["img_2p"] = GetYoutube.set_yt_image(
                self.param.crop | self.param.img['g_fighter']['crop_2p'], self.img, crop=True,
                pre_dsize=self.param.img["g_fighter"]["dsize"],
                # imw_path=join(dirname(__file__), f'image{index}_{sec}_topR.jpg')
            )
            self.game_data.fighter_id_1p, self.game_data.fighter_name_1p, easyOCR_txt_1p = self.get_fighter_name(self.param.img["g_fighter"]["img_1p"])
            self.game_data.fighter_id_2p, self.game_data.fighter_name_2p, easyOCR_txt_2p = self.get_fighter_name(self.param.img["g_fighter"]["img_2p"])
            if ((self.game_data.fighter_name_1p in self.param.target_1p_fighters and self.game_data.fighter_id_2p>0) or 
                (self.game_data.fighter_id_1p>0 and self.game_data.fighter_name_2p in self.param.target_1p_fighters)):
                self.count=0
                self.trans('skip_game')
                self.game_data.game_start_datetime = datetime.fromtimestamp(self.param.yt_info["release_timestamp"]+sec, JST).strftime('%Y-%m-%d %T')
                self.game_data.game_start_url = f'{self.param.yt_info["original_url"]}&t={sec}s'
                yt_id = self.param.yt_info['original_url'].split('=')[1]
                print(f"success get_fighter_name in {sec}s in with {yt_id}")
                GetYoutube.get_yt_image(self.param.yt_info, sec, (480,270), imw_path=join(self.param.img["imw_path"], f'static/image{index}_{yt_id}_{sec}.jpg'))
            else:
                self.trans('find_game_start')
        if self.states['skip_game']:
            self.count += 1
            if self.count==self.sec["game"]: self.trans('find_game_finish')
            else: return 0
        if self.states['find_game_finish']:
            self.img = GetYoutube.get_yt_image(self.param.yt_info, sec, gray=True)
            self.param.img["g_finish"]["img"] = GetYoutube.set_yt_image(
                self.param.crop | self.param.img['g_finish']['crop'], self.img, crop=True,
                pre_dsize=self.param.img["g_finish"]["dsize"],
            )
            if self.find_game():
                # GetYoutube.set_yt_image(
                #     img=self.param.img["g_finish"]["img"],
                #     imw_path=join(dirname(__file__), f'image{index}_{sec}_center.jpg')
                # )
                self.trans('get_game_result')
        if self.states['get_game_result']:
            self.sec_buf = sec
            self.param.img["g_result"]["img_1p"] = GetYoutube.set_yt_image(
                self.param.crop | self.param.img['g_result']['crop_1p'], self.img, crop=True,
                pre_dsize=self.param.img["g_result"]["dsize"],
                # imw_path=join(dirname(__file__), f'image{index}_{sec}_btmL.jpg')
            )
            self.param.img["g_result"]["img_2p"] = GetYoutube.set_yt_image(
                self.param.crop | self.param.img['g_result']['crop_2p'], self.img, crop=True,
                pre_dsize=self.param.img["g_result"]["dsize"],
                # imw_path=join(dirname(__file__), f'image{index}_{sec}_btmR.jpg')
            )
            self.get_game_result()
            if self.game_data.target_player_is_win==None:
                self.sec_buf+=1
                self.img = GetYoutube.get_yt_image(self.param.yt_info, self.sec_buf, gray=True)
                self.param.img["g_result"]["img_1p"] = GetYoutube.set_yt_image(
                    self.param.crop | self.param.img['g_result']['crop_1p'], self.img, crop=True,
                    pre_dsize=self.param.img["g_result"]["dsize"],
                    # imw_path=join(dirname(__file__), f'image{index}_{sec}_btmL.jpg')
                )
                self.param.img["g_result"]["img_2p"] = GetYoutube.set_yt_image(
                    self.param.crop | self.param.img['g_result']['crop_2p'], self.img, crop=True,
                    pre_dsize=self.param.img["g_result"]["dsize"],
                    # imw_path=join(dirname(__file__), f'image{index}_{sec}_btmR.jpg')
                )
                self.get_game_result()
            if self.game_data.target_player_is_win==None:
                # self.sec_buf+=6
                self.sec_buf+=6.5
                self.img = GetYoutube.get_yt_image(self.param.yt_info, self.sec_buf, gray=True)
                self.param.img["g_result"]["img_rs"] = GetYoutube.set_yt_image(
                    self.param.crop | self.param.img['g_result']['crop_rs'], self.img, crop=True,
                    pre_dsize=self.param.img["g_result"]["dsize"],
                    # imw_path=join(dirname(__file__), f'image{index}_{self.sec_buf}_btmLL.jpg')
                )
                self.get_game_result2()
            if self.game_data.target_player_is_win!=None:
                self.game_data.game_finish_datetime = datetime.fromtimestamp(self.param.yt_info['release_timestamp']+self.sec_buf, JST).strftime('%Y-%m-%d %T')
                self.game_data.game_finish_url = f"{self.param.yt_info['original_url']}&t={self.sec_buf}s"
                self.count=0
                self.trans('skip_interval')
                yt_id = self.param.yt_info['original_url'].split('=')[1]
                print(f"success get_game_result in {self.sec_buf}s in with {yt_id}")
                GetYoutube.get_yt_image(self.param.yt_info, self.sec_buf, (480,270), imw_path=join(self.param.img["imw_path"], f'static/image{index}_{yt_id}_{self.sec_buf}.jpg'))
            else:
                self.trans('get_game_result')
        for k,v in self.states.items():
            if v==True: self.state = k
            
    def test_get_yt_image(self, index, sec):
        yt_id = self.param.yt_info['original_url'].split('=')[1]
        GetYoutube.get_yt_image(self.param.yt_info, sec, (480,270), imw_path=join(self.param.img["imw_path"], f'static/image{index}_{yt_id}_{sec}.jpg'))

def test_generate_insert_data(inputs):
    category = {'VIP':['VIP'], 'smashmate':['めいと', 'メイト','レート', 'レーティング']}
    img = {
        "g_start": {
            "img": None,
            "temp_img": None,
            "temp_match_val": -1,
            "dsize": (1024,576),
            "crop": {"crop1": {'pt1': [0,0], 'pt2': [1024,int(576*0.2)]}}
        },
        "g_fighter": {
            "img_1p": None,
            "img_2p": None,
            "dsize": (448,252),
            "crop_1p": {"crop1": {'pt1': [int(448*0.10),int(252*0.02)], 'pt2': [int(448*0.43),int(252*0.13)]}},
            "crop_2p": {"crop1": {'pt1':[int(448*0.60),int(252*0.02)], 'pt2':[int(448*0.93),int(252*0.13)]}}
        },
        "g_finish": {
            "img": None,
            "temp_img": "gameset.png",
            "temp_match_val": 0.474,
            "dsize": (448,252),
            "crop": {"crop1": {'pt1':[int(448*0.21),int(252*0.16)], 'pt2':[int(448*0.79),int(252*0.64)]}}
        },
        "g_result": {
            "img_1p": None,
            "img_2p": None,
            "img_rs": None,
            "dsize": (1280,720),
            "crop_1p": {"crop1": {'pt1':[int(1280*0.266),int(720*0.847)], 'pt2':[int(1280*0.343),int(720*0.927)]}},
            "crop_2p": {"crop1": {'pt1':[int(1280*0.651),int(720*0.847)], 'pt2':[int(1280*0.728),int(720*0.927)]}},
            "crop_rs": {"crop1": {'pt1':[int(1280*0.000),int(720*0.600)], 'pt2':[int(1280*0.500),int(720*1.000)]}}
        },
        "imw_path": dirname(__file__)
    }
    # 動画毎に並行(並列)処理
    param = Parameter(inputs, img, category)

    tasks = []
    for i in range(len(inputs["yt_infos"])):
        tasks.append(Thread(target=test_generate_analysis_data, args=(i,param,)))
    for t in tasks:
        t.start()
    for t in tasks:
        t.join()

def test_generate_analysis_data(index, param: Parameter):
    analysis = EsportsAnalysis(index, param)
    analysis.set_game_data()
    # initial = 0 
    # total = 40 
    initial = 130
    total = 560
    bar = tqdm(total=total, leave=False, disable=False, initial=initial)
    game_data_list = []
    for sec in range(initial, total):
        analysis.execute_analysis(index, sec)
        bar_text = f"Image processing in progress. Please wait. | {analysis.param.yt_info['original_url'].split('=')[1]} -> {analysis.state}"
        bar.set_description(bar_text)
        bar.update(1)
        if analysis.game_data.fighter_id_1p>-1 and analysis.game_data.fighter_id_2p>-1:
            if analysis.game_data.target_player_is_win in [True, False]:
                game_data_list.append(analysis.game_data)
                analysis.set_game_data()
    # time.sleep(0.1*(1+index))
    smash_db = SmashDatabase()
    data_id = len(smash_db.select_analysis_data()) + 1
    for i in range(len(game_data_list)): game_data_list[i].id = data_id+i
    print(f"game_data_list = {game_data_list}")
    # smash_db.insert_analysis_data([tuple(vars(data).values()) for data in game_data_list])

def main_test():
    full_gs = True
    if full_gs:
        target_1p_fighters = ['KAMUI', 'BYLETH']
        yt_infos = GetYoutube("https://www.youtube.com/watch?v=wxySmIhgtnI&list=PLxWXI3TDg12xwVJxNCYpNBG0s3l4-3inZ").infos
        crop = {'crop0': {'pt1': [0,0], 'pt2': [1920,1080]}}
    else:
        target_1p_fighters = ['KAMUI']
        yt_infos = GetYoutube("https://www.youtube.com/watch?v=xU1BLJ9gZ7I&list=PLxWXI3TDg12ynGyOqMitigy6a8JgkyYwY").infos
        # yt_infos = GetYoutube("https://www.youtube.com/watch?v=xU1BLJ9gZ7I").infos
        crop = {'crop0': {'pt1': [0, 0], 'pt2': [1585, 891]}}
    inputs = {
        "target_player_name": 'auto',
        "target_category": 'auto',
        "target_1p_fighters": target_1p_fighters,
        "fighter_df": SmashDatabase().select_fighter_data(),
        "yt_infos": yt_infos,
        "crop": crop
    }
    test_generate_insert_data(inputs)

if __name__=="__main__":
    main_test()
    