# import os
# import sys
# os.environ['TF_CPP_MIN_LOG_LEVEL']='2'
# sys.path.append(os.path.split(__file__)[0])
#import tensorflow as tf
#tf.get_logger().setLevel("ERROR")

from os.path import dirname, join
# from sys import path
# path.append(join(dirname('__file__')))

import cv2
import easyocr
#import kerasocr
import numpy as np
import re
#import streamlit as st
import string
# import threading # https://qiita.com/Toyo_m/items/992b0dcf765ad3082d0b
import time

from .bq_db import BigqueryDatabase, SmashDatabase
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import wraps
# from google.cloud import vision
from google.oauth2 import service_account
# from streamlit import session_state as ss
# from streamlit.runtime.scriptrunner import add_script_run_ctx
# from tqdm import tqdm
from threading import Thread
from .yt_obj import YoutubeInformation, GetYoutube
JST = timezone(timedelta(hours=+9), 'JST')

# def init_ss(key,value=None):
#     if key not in ss: ss[key] = value

# def set_ss(key, value=None):
#     if key in ss: ss[key] = value

# def del_ss(key):
#     if key in ss: del ss[key]

# def app_stop():
#     ss.app_stop_clicked = True

def stop_watch(func):
    @wraps(func)
    def wrapper(*args, **kargs) :
        start = time.perf_counter()
        result = func(*args,**kargs)
        elapsed_time =  time.perf_counter() - start
        print(f"{func.__name__}は{elapsed_time}秒かかりました")
        return result
    return wrapper

# class NewThread(Thread):
#     def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
#         Thread.__init__(self, group, target, name, args, kwargs)

#     def run(self):
#         if self._target != None:
#             self._return = self._target(*self._args, **self._kwargs)

#     def join(self, *args):
#         Thread.join(self, *args)
#         return self._return

# pythonで並行処理を実行させて、それぞれの結果の値を取得する https://qiita.com/fumihiko-hidaka/items/5745468e1588b39fbf5f
class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        # if self._Thread__target is not None:
        if self._target is not None:
            # self._return = self._Thread__target(
            self._return = self._target(
                # *self._Thread__args,
                *self._args,
                # **self._Thread__kwargs
                **self._kwargs
            )

    def join(self, timeout=None):
        Thread.join(self, timeout)
        return self._return

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

# 空辞書、空リストを用意する場合はfiled(default_factory)を使用 https://qiita.com/plumfield56/items/5794170fae2c4cabc5be
@dataclass
class Parameter:
    # target_player_name: str = None
    # target_category: str = None
    # target_1p_fighters: str = None
    inputs: dict = field(default_factory=dict)
    fighter_lists: list = field(default_factory=list)
    # yt_info: dict = field(default_factory=dict)
    # crop: dict = field(default_factory=dict)
    img: dict = field(default_factory=dict)
    # start_sec: int = 0
    # interval_sec: int = 28
    # game_sec: int = 56
    # sec: dict = {"start":0, "interval":28, "game":56}
    sec: dict = field(default_factory=dict)
    # edge: dict = {"sigma":0.33, "kernel":0}
    edge: dict = field(default_factory=dict)
    # line: dict = {
    #     "rho":1, "theta":np.pi/180, "threshold":200,
    #     "target_rho_list":[[17.0,17.0],[33.0,33.0], [86.0,87.0], [90.0,90.0], [104.0,104.0]], 
    #     "target_theta":1.535889744758606, "error_range":10**-14, "target_line_num":[1,4]
    # }
    line: dict = field(default_factory=dict)
    # recog_txt: dict = {"start":[-4,-5], "end":[None,-1], "range":3}
    recog_txt: dict = field(default_factory=dict)
    # easyocr: dict = {
    #     "name_allowlist": string.ascii_uppercase, "num_allowlist":string.digits, 
    #     "detail":0, "lang_list": ['en'], "verbose":False
    # }
    easyocr: dict = field(default_factory=dict)
    
    # def __init__(self, inputs, img_dict, category_dict, sec=dict(), edge=dict()):
    def __init__(
            self, inputs, img, category,
            sec = {"interval":28, "game":56},
            edge = {"sigma":0.33, "kernel":0},
            line = {
                "rho":1, "theta":np.pi/180, "threshold":200,
                "target_rho_list":[[17.0,17.0],[33.0,33.0], [86.0,87.0], [90.0,90.0], [104.0,104.0]], 
                "target_theta":1.535889744758606, "error_range":10**-14, "target_line_num":[1,4]
            },
            recog_txt = {"start":[-4,-5], "end":[None,-1], "range":3},
            easyocr = {
                "name_allowlist": string.ascii_uppercase, "num_allowlist":string.digits, 
                "detail":0, "lang_list": ['en'], "verbose":False
            }
        ):
        # self.target_player_name = inputs["target_player_name"]
        # self.target_category = inputs["target_category"]
        # self.target_1p_fighters = inputs["target_1p_fighters"]
        # inputs["crop"] = inputs["crop"].to_dict()
        # print(type(inputs["crop"]))
        self.inputs = inputs
        self.yt_infos = inputs["yt_infos"]
        # self.category_dict = category_dict
        self.get_fighterlists()
        # self.crop = inputs["crop"]
        img["g_start"]["temp_img"] = cv2.imread(join(dirname(__file__),f'./images/{img["g_start"]["temp_img"]}'), 0) if img["g_start"]["temp_img"]!=None else None
        self.img = img
        self.df = SmashDatabase('ssbu_dataset').select_analysis_data()
        # for k in self.sec.keys():
        #     if k in sec.keys(): self.sec[k] = sec[k]
        # for k in self.edge.keys():
        #     if k in edge.keys(): self.edge[k] = edge[k]
        # for k in self.line.keys():
        #     if k in line.keys(): self.line[k] = line[k]
        # for k in self.recog_txt.keys():
        #     if k in recog_txt.keys(): self.recog_txt[k] = recog_txt[k]
        # for k in self.easyocr.keys():
        #     if k in easyocr.keys(): self.easyocr[k] = easyocr[k]
        self.sec = sec
        self.edge = edge
        self.line = line
        self.recog_txt = recog_txt
        self.easyocr = easyocr
        # crop = self.inputs["crop"] | self.img['g_fighter']['crop_1p'] 
        # print(crop.keys())
        self.category = category
    
    # def get_fighterlists(fighter_df):
    def get_fighterlists(self):
        # df_sorted = fighter_df.sort_values(by='id')
        df = self.inputs["fighter_df"]
        # return [df_sorted['recog_name'].to_list(), df_sorted['fighter_id'].to_list(), df_sorted['fighter_name'].to_list()]
        self.fighter_lists = [df['recog_name'].to_list(), df['fighter_id'].to_list(), df['fighter_name'].to_list()]
                
class EsportsAnalysis:
    def __init__(self, index, param:Parameter):
        self.param = param
        self.yt_info = param.yt_infos[index]
        self.count = 0
        self.states = {'skip_interval':True, 'skip_game':False, 'find_game_start':False, 'get_fighter_name':False, 'find_game_finish': False, 'get_game_result':False}
        # self.target_category = self.get_category() if param.target_category=='auto' else param.target_category
        self.img = None
        # self.yt_info["id"] = index
        if self.param.inputs["target_category"]=='auto': self.param.inputs["target_category"] = self.get_category()
        self.get_start_sec()
        
    def get_category(self): 
        for k,V in self.param.category.items():
            for v in V:
                if v in self.yt_info['title']: return k
        return 'other'
    
    def get_start_sec(self):
        df = self.param.df
        self.initial = 0
        for game_start_url in df['game_start_url'].to_list():
            if self.yt_info['original_url'] in game_start_url:
                self.initial = max([self.initial, int(re.findall(r'\d+',game_start_url)[-1])])

    def set_game_data(self):
        self.game_data = GameData()
        self.game_data.target_player_name = self.param.inputs["target_player_name"]
        self.game_data.title = self.yt_info["title"]
        self.game_data.category = self.param.inputs["target_category"]

    # def get_category(self): 
    #     for k,V in self.param.category_dict.items():
    #         for v in V:
    #             if v in self.yt_info['title']: return k
    #     return 'other'
    
    # def trans(states, next_state):
    def trans(self, next_state):
        # for state in states.keys():
        for state in self.states.keys():
            # if state==next_state: states[state] = True
            if state==next_state: self.states[state] = True
            # else: states[state] = False
            else: self.states[state] = False
        # return states
        
    # def skip_proc(count, count_end=28, interval=True):
    def skip_proc(self, count_end, state):
        # if not interval: count_end*=2
        # count+=1
        self.count+=1
        # if count==count_end: return True, count
        if self.count==count_end: self.states[state] = True
        # else: return False, count
        else: self.states[state] = False
        
    #def find_game(img, temp_img=None, detector=None, target_des=None, match_ret=-1):
    def find_game(self):
        img = self.param.img["g_start"]["img"] if self.states["find_game_start"] else self.param.img["g_finish"]["img"]
        temp_img = self.param.img["g_start"]["temp_img"] if self.states["find_game_start"] else self.param.img["g_finish"]["temp_img"]
        temp_match_val = self.param.img["g_start"]["temp_match_val"] if self.states["find_game_start"] else self.param.img["g_finish"]["temp_match_val"]
        # if temp_img is None and detector==None and target_des==None and match_ret==-1: return detect_line(img, detect_edge(img))
        if temp_img is None: return self.detect_line(img, self.detect_edge(img))
        # elif not temp_img is None: return temp_match(img, temp_img)
        else: return self.temp_match(img, temp_img, temp_match_val)
        # else: return feat_match(img, detector, target_des, match_ret)
        
    # def detect_edge(img_gray, sigma = 0.33, kernel = 0):
    def detect_edge(self, img):
        # img_blur = cv2.GaussianBlur(img_gray, (kernel, kernel), sigma)
        img_blur = cv2.GaussianBlur(img, (self.param.edge["kernel"], self.param.edge["kernel"]), self.param.edge["sigma"])

        # Automatic Thresholds Finding
        med_val = np.median(img_blur)
        # min_val = int(max(0, (1.0 - sigma) * med_val))
        min_val = int(max(0, (1.0 - self.param.edge["sigma"]) * med_val))
        # max_val = int(max(255, (1.0 + sigma) * med_val))
        max_val = int(max(255, (1.0 + self.param.edge["sigma"]) * med_val))
    
        return cv2.Canny(img_blur, threshold1=min_val, threshold2=max_val, L2gradient=True)

    def detect_line(self, img, img_edges):
        # Hough変換で直線を検出
        # img_lines = cv2.HoughLines(img_edges, rho=1, theta=np.pi/180, threshold=200)
        img_lines = cv2.HoughLines(img_edges, rho=self.param.line["rho"], theta=self.param.line["theta"], threshold=self.param.line["threshold"])
        if not img_lines is None:
            # if is_start(img, img_lines):
            if self.is_start(img_lines):
                #st.image(draw_line(img,img_lines))
                return True
        #else: st.image(img, caption='line_count: 0')
        return False
    
    # 対戦開始のタイミングならTrue
    # target_rho_list=[[17.0,17.0], [38.0,38.0], [40.0,40.0], [86.0,86.0], [90.0,90.0], [104.0,104.0]], target_theta=1.535897, error_range=10**-2, target_line_num=[2,6]
    # def is_start(self, img, img_lines, target_rho_list=[[17.0,17.0],[33.0,33.0], [86.0,87.0], [90.0,90.0], [104.0,104.0]], target_theta=1.535889744758606, error_range=10**-14, target_line_num=[1,4]):
    def is_start(self, img_lines):
        # for d in range(256):
        #     # if d**3 >= target_line_num[1]: break
        #     if d**3 >= self.param.line["target_line_num"][1]: break
        # colors = [(r,g,b) for r in range(0,256,int(255/(d-1))) for g in range(0,256,int(255/(d-1))) for b in range(0,256,int(255/(d-1)))]
        # img_copy = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        # いい感じの直線の数
        line_count = 0
        for line in img_lines:
            rho, theta = line[0]
            # いい感じの角度の直線ならカウントして描画する
            # if np.abs(theta - target_theta) < error_range:
            if np.abs(theta - self.param.line["target_theta"]) < self.param.line["error_range"]:
                # for target_rho in target_rho_list:
                for target_rho in self.param.line["target_rho_list"]:
                    if target_rho[0]<=rho and rho<=target_rho[1]:
                        line_count += 1            
                        # if line_count <= target_line_num[1]:
                        # if line_count <= self.param.line["target_line_num"][1]:
                            # st.write(f'theta: {theta}, rho: {rho}')
                            # print(f'{rho},',end='')
                            # img_copy = draw_target_line(img_copy, rho, theta, colors[line_count-1])
                        break
        # 2～6本あれば対戦開始のタイミング
        # if target_line_num[0]<=line_count and line_count<=target_line_num[1]:
        if self.param.line["target_line_num"][0]<=line_count and line_count<=self.param.line["target_line_num"][1]:
            #print()
            #st.image(img_copy, caption=f'line_count: {line_count}')
            return True
        else: return False
    
    def temp_match(img, temp_img, match_val): #match_val=0.474
        result = cv2.matchTemplate(img, temp_img, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if(match_val<max_val and max_val<1.0):
            return True
        else:
            return False
    
    # def get_fighter_name(txt, fighterlists, slice_start=[-4,-5], slice_end=[None,-1], str_num=3):
    def get_fighter_name(self, img):
        # for recog_name, fighter_id, fighter_name in zip(fighterlists[0], fighterlists[1], fighterlists[2]):
        #     for start,end in zip(slice_start, slice_end):
        #         if (len(recog_name[start:end])>=str_num) and (recog_name[start:end] in txt): return fighter_id, fighter_name, txt
        # return 0, 'other', txt
        # for start,end in zip(slice_start, slice_end):
        #     for recog_name, fighter_id, fighter_name in zip(fighterlists[0], fighterlists[1], fighterlists[2]):
        #         if (len(recog_name[start:end])>=str_num) and (recog_name[start:end] in txt): return fighter_id, fighter_name, txt
        # return 0, 'other', txt
        txt = self.easyOCR(img, self.param.easyocr["name_allowlist"])
        for start,end in zip(self.param.recog_txt["start"], self.param.recog_txt["end"]):
            for recog_name, fighter_id, fighter_name in zip(self.param.fighter_lists[0], self.param.fighter_lists[1], self.param.fighter_lists[2]):
                if (len(recog_name[start:end])>=self.param.recog_txt["num"]) and (recog_name[start:end] in txt): return fighter_id,
                fighter_name, txt
        return 0, 'other', txt
    
    # def get_game_result(img_1p, img_2p, data, target_1p_fighters):
    def get_game_result(self):
        # damage_1p = easyOCR(img_1p, allowlist=string.digits)
        damage_1p = self.easyOCR(self.param.img["g_result"]["img_1p"], self.param.easyocr["num_allowlist"])
        # damage_2p = self.easyOCR(img_2p, self.param.easyocr["num_allowlist"])
        damage_2p = self.easyOCR(self.param.img["g_result"]["img_2p"], self.param.easyocr["num_allowlist"])
        #st.write(f'easyOCR: 1P:{damage_1p} | 2P:{damage_2p}')
        # if damage_1p=='' and damage_2p=='':
            # damage_1p = kerasOCR(cv2.cvtColor(img_1p, cv2.COLOR_GRAY2RGB), blocklist='\D')
            #st.write(f'kerasOCR: 1P:{damage_1p}')
            # damage_1p = gcvOCR(img_1p, blocklist='\D') # '\D'='[^0-9]'：すべての数字以外の文字
            # st.write(f'gcvOCR: 1P:{damage_1p}')
            # if damage_1p=='': 
                # damage_2p = kerasOCR(cv2.cvtColor(img_2p, cv2.COLOR_GRAY2RGB), blocklist='\D')
                #st.write(f'kerasOCR: 2P:{damage_2p}')
                # damage_2p = gcvOCR(img_2p, blocklist='\D') # '\D'='[^0-9]'：すべての数字以外の文字
                # st.write(f'gcvOCR: 2P:{damage_2p}')
        # st.image(img_1p)
        # st.image(img_2p)
        # if data.fighter_name_1p in target_1p_fighters:
        if self.game_data.fighter_name_1p in self.param.inputs["target_1p_fighters"]:
            # data.target_player_is_1p = True
            self.game_data.target_player_is_1p = True
            # if re.compile('\d').search(damage_1p) and damage_2p=='': data.target_player_is_win = True
            if re.compile('\d').search(damage_1p) and damage_2p=='': self.game_data.target_player_is_win = True
            # elif re.compile('\d').search(damage_2p) and damage_1p=='': data.target_player_is_win = False
            elif re.compile('\d').search(damage_2p) and damage_1p=='': self.game_data.target_player_is_win = False
            # else: data.target_player_is_win = None
            else: self.game_data.target_player_is_win = None
        else:
            # data.target_player_is_1p = False
            self.game_data.target_player_is_1p = False
            # if re.compile('\d').search(damage_1p) and damage_2p=='': data.target_player_is_win = False
            if re.compile('\d').search(damage_1p) and damage_2p=='': self.game_data.target_player_is_win = False
            # elif re.compile('\d').search(damage_2p) and damage_1p=='': data.target_player_is_win = True
            elif re.compile('\d').search(damage_2p) and damage_1p=='': self.game_data.target_player_is_win = True
            # else: data.target_player_is_win = None
            else: self.game_data.target_player_is_win = None
        # return data
        
    def get_game_result2(self):
        #allowlist = re.sub('[.& ]','', target_fighter)
        # allowlist = re.sub('[.& ]','', data.fighter_name_1p+data.fighter_name_2p)
        allowlist = re.sub('[.& ]', '', self.game_data.fighter_name_1p+self.game_data.fighter_name_2p)
        # target_fighter = data.fighter_name_1p if data.fighter_name_1p in inputs['target_1p_fighters'] else data.fighter_name_2p #if data.fighter_name_2p in target_1p_fighters else ''.join(target_1p_fighters)
        target_fighter = self.game_data.fighter_name_1p if self.game_data.fighter_name_1p in self.param.inputs['target_1p_fighters'] else self.game_data.fighter_name_2p
        # easyOCR_txt = set(easyOCR(img_btmL2,allowlist=allowlist))
        #stc[1].image(img_btmL2, caption=f'easyOCR_txt: {easyOCR_txt}')
        str_cnt=0
        for ocr_str in set(self.easyOCR(self.param.img["g_result"]["img_rs"], allowlist)):
            if ocr_str in target_fighter: str_cnt+=1
            # if str_cnt==3: data.target_player_is_win = True
            if str_cnt==3: self.game_data.target_player_is_win = True
        # if str_cnt<3: data.target_player_is_win = False
        if str_cnt<3: self.game_data.target_player_is_win = False
        # fighter_name, easyOCR_txt = get_fighter_name(easyOCR(img_btmL2,allowlist=allowlist), fighterlists)[1:]
        # if fighter_name in inputs['target_1p_fighters']: data.target_player_is_win = True
        # else : data.target_player_is_win = False
        # data.game_finish_datetime = datetime.fromtimestamp(info.release_timestamp+sec+7, JST).strftime('%Y-%m-%d %T')
        # data.game_finish_url = f'{info.original_url}&t={sec2}s'
        # stc[1].image(cv2.resize(img2, dsize=dsize_temp), caption=f'{data.game_finish_url}: {"WIN" if data.target_player_is_win else "LOSE"}')
    
    # def easyOCR(img, lang_list=['en'], allowlist=string.ascii_letters+string.digits, verbose=False):
    def easyOCR(self, img, allowlist=string.ascii_letters+string.digits):
        reader = easyocr.Reader(lang_list=self.param.easyocr["lang_list"], verbose=self.param.easyocr["verbose"])
        txt = ''
        for ocr_res in reader.readtext(img, allowlist=allowlist, detail=self.param.easyocr["detail"]):
            txt+=ocr_res
        return re.sub(' ', '', txt)
    
    def execute_analysis(self, sec):
        # st_bar_text = f"Image processing in progress. Please wait. | {info.original_url[-11:]}: {int((sec+1)/total*100)}% ({sec+1}/{total} sec)"
        # my_bar.progress((sec+1)/total, text=st_bar_text)
        # bar.set_description(bar_text)
        # bar.update(1)
        # if ss.app_stop_clicked: break
        # if game_num==len(game_data_list): break
        # if states['skip_interval']:
        if self.states['skip_interval']:
            # states['find_game_start'], count = skip_proc(count, count_end)
            self.skip_proc(self.param.sec["interval"], 'find_game_start')
            # if not states['find_game_start']: continue
            if not self.states['find_game_start']: return 0
            # else: states = trans(states, 'find_game_start')
            else: self.trans('find_game_start')
        # if states['find_game_start']:
        if self.states['find_game_start']:
            # bar_text = f'{info.original_url[-11:]} -> find_game_start'
            # info,img = GetYoutube.get_yt_image(info, sec*info.fps, ydl_opts=inputs['ydl_opts'], dsize=inputs['dsize'], crop=inputs['crop'], gray=True)
            self.img = GetYoutube.get_yt_image(self.yt_info, sec, self.param.img["g_start"]["dsize"], True)
            # img_576p = img = cv2.resize(img, dsize=(1024,576))
            # img_top = img_576p[0:int(img_576p.shape[0]*0.2),:]
            self.param.img["g_start"]["img"] = GetYoutube.set_yt_image(
                self.param.inputs["crop"] | self.param.img['g_start']['crop'],
                self.img, crop=True, dsize=self.param.img["g_start"]["dsize"]
            )
            # with stc[0]:
            #     if find_game(img_top): states = trans(states, 'get_fighter_name')
            if self.find_game():
                GetYoutube.get_yt_image(self.yt_info, sec, imw_path=join(dirname(__file__), f'static/image{self.yt_info["id"]}_{sec}.jpg'))
                self.trans('get_fighter_name')
        #if states['get_fighter_name']:
        if self.states['get_fighter_name']:
            # bar_text = f'{info.original_url[-11:]} -> get_fighter_name'
            # img_252p = cv2.resize(img, dsize=(448,252))
            # img = GetYoutube.get_yt_image(self.yt_info, sec, self.param.img["g_fighter"]["dsize"], True)
            # h,w = img_252p.shape[0],img_252p.shape[1]
            # img_topL = img_252p[int(h*0.02):int(h*0.13), int(w*0.10):int(w*0.43)]
            # img_topR = img_252p[int(h*0.02):int(h*0.13), int(w*0.60):int(w*0.93)]
            self.param.img["g_fighter"]["img_1p"] = GetYoutube.set_yt_image(
                self.param.inputs["crop"] | self.param.img['g_fighter']['crop_1p'],
                self.img, crop=True, dsize=self.param.img["g_fighter"]["dsize"]
            )
            self.param.img["g_fighter"]["img_2p"] = GetYoutube.set_yt_image(
                self.param.inputs["crop"] | self.param.img['g_fighter']['crop_2p'],
                self.img, crop=True, dsize=self.param.img["g_fighter"]["dsize"]
            )
            # data = GameData()
            # allowlist='irt'+string.ascii_uppercase
            # data.fighter_id_1p, data.fighter_name_1p, easyOCR_txt_1p = get_fighter_name(easyOCR(img_topL,allowlist=allowlist), fighterlists)
            self.game_data.fighter_id_1p, self.game_data.fighter_name_1p, easyOCR_txt_1p = self.get_fighter_name(self.param.img["g_fighter"]["img_1p"], self.param.fighter_lists)
            # data.fighter_id_2p, data.fighter_name_2p, easyOCR_txt_2p = get_fighter_name(easyOCR(img_topR,allowlist=allowlist), fighterlists)
            self.game_data.fighter_id_2p, self.game_data.fighter_name_2p, easyOCR_txt_2p = self.get_fighter_name(self.param.img["g_fighter"]["img_2p"], self.param.fighter_lists)
            #stc[0].write(f'easyOCR_txt: {easyOCR_txt_1p} vs {easyOCR_txt_2p}')
            # if data.fighter_id_1p==0:
            #     data.fighter_id_1p, data.fighter_name_1p, kerasOCR_txt_1p = get_fighter_name(
            #         # kerasOCR(cv2.cvtColor(img_topL, cv2.COLOR_GRAY2RGB), blocklist=f'[^{allowlist}]'), fighterlists, 
            #         #slice_start=[-4], slice_end=[None]
            #     )
            #     #stc[0].write(f'kerasOCR_txt_1p: {kerasOCR_txt_1p}')
            # if data.fighter_id_2p==0:
            #     #img_topR = img_252p[int(h*0.02):int(h*0.13), int(w*0.60):int(w*0.93)]
            #     data.fighter_id_2p, data.fighter_name_2p, kerasOCR_txt_2p = get_fighter_name(
            #         # kerasOCR(cv2.cvtColor(img_topR,cv2.COLOR_GRAY2RGB),blocklist=f'[^{allowlist}]'), fighterlists, 
            #         #slice_start=[-4], slice_end=[None]
            #     )
                #stc[0].write(f'kerasOCR_txt_2p: {kerasOCR_txt_2p}')
            # if (data.fighter_name_1p in inputs['target_1p_fighters'] and data.fighter_id_2p!=0) or (data.fighter_id_1p!=0 and data.fighter_name_2p in inputs['target_1p_fighters']):
            if (self.game_data.fighter_name_1p in self.param.inputs['target_1p_fighters'] and self.game_data.fighter_id_2p!=0) or (self.game_data.fighter_id_1p!=0 and self.game_data.fighter_name_2p in self.param.inputs['target_1p_fighters']):
                # count=0
                self.count=0
                # states = trans(states, 'skip_game')
                self.trans('skip_game')
                # data.game_start_datetime = datetime.fromtimestamp(info.release_timestamp+sec, JST).strftime('%Y-%m-%d %T')
                self.game_data.game_start_datetime = datetime.fromtimestamp(self.yt_info["release_timestamp"]+sec, JST).strftime('%Y-%m-%d %T')
                # data.game_start_url = f'{info.original_url}&t={sec}s'
                self.game_data.game_start_url = f'{self.yt_info["original_url"]}&t={sec}s'
                # stc[0].image(img_252p, caption=f'{data.game_start_url}: {data.fighter_name_1p} vs {data.fighter_name_2p}')
            else:
                # states = trans(states, 'find_game_start')
                self.trans('find_game_start')
        # if states['skip_game']:
        if self.states['skip_game']:
            # states['find_game_finish'], count = skip_proc(count, count_end, interval=False)
            self.skip_proc(self.param.sec["game"], 'find_game_finish')
            # if not states['find_game_finish']: continue
            if not self.states['find_game_start']: return 0
            # else: states = trans(states, 'find_game_finish')
            else: self.trans('find_game_start')
        # if states['find_game_finish']:
        if self.states['find_game_finish']:
            # bar_text = f'{info.original_url[-11:]} -> find_game_finish'
            # info,img = GetYoutube.get_yt_image(info, sec*info.fps, ydl_opts=inputs['ydl_opts'], dsize=inputs['dsize'], crop=inputs['crop'], gray=True)
            self.img = GetYoutube.get_yt_image(self.yt_info, sec, self.param.img["g_finish"]["dsize"], True)
            # img_252p = cv2.resize(img, dsize=dsize_temp)
            # h,w = img_252p.shape[0],img_252p.shape[1]
            # img_cent = img_252p[int(h*0.16):int(h*0.64),int(w*0.21):int(w*0.79)]
            self.param.img["g_finish"]["img"] = GetYoutube.set_yt_image(
                self.param.inputs["crop"] | self.param.img['g_finish']['crop'],
                self.img, crop=True, dsize=self.param.img["g_finish"]["dsize"]
            )
            # if find_game(img_cent, temp_img=temp_img, detector=detector, target_des=target_des, match_ret=match_ret): states = trans(states, 'get_game_result')
            if self.find_game():
                GetYoutube.get_yt_image(self.yt_info, sec, imw_path=join(dirname(__file__), f'static/image{self.yt_info["id"]}_{sec}.jpg'))
                self.trans('get_fame_result')
        # if states['get_game_result']:
        if self.states['get_game_result']:
            sec_buf = sec
            # bar_text = f'{info.original_url[-11:]} -> get_game_result'
            # img_720p = cv2.resize(img, dsize=(1280,720))
            # h,w = img_720p.shape[0],img_720p.shape[1]
            # img_btmL = img_720p[int(h*0.847):int(h*0.927),int(w*0.266):int(w*0.343)] # 100～1の位
            # img_btmR = img_720p[int(h*0.847):int(h*0.927),int(w*0.651):int(w*0.728)] # 100～1の位
            self.param.img["g_result"]["img_1p"] = GetYoutube.set_yt_image(
                self.param.inputs["crop"] | self.param.img['g_result']['crop_1p'],
                self.img, crop=True, dsize=self.param.img["g_result"]["dsize"]
            )
            self.param.img["g_result"]["img_2p"] = GetYoutube.set_yt_image(
                self.param.inputs["crop"] | self.param.img['g_result']['crop_2p'],
                self.img, crop=True, dsize=self.param.img["g_result"]["dsize"]
            )
            # with stc[1]:
            #     data = get_game_result(img_btmL, img_btmR, data, inputs['target_1p_fighters'])
            self.get_game_result()
            # if data.target_player_is_win==None:
            target_player_is_win = self.game_data.target_player_is_win
            if target_player_is_win==None:
                sec_buf+=7
                # info,img2 = GetYoutube.get_yt_image(info, sec2*info.fps, ydl_opts=inputs['ydl_opts'], dsize=inputs['dsize'], crop=inputs['crop'], gray=True)
                self.img = GetYoutube.get_yt_image(self.yt_info, sec_buf, self.param.img["g_start"]["dsize"], True)
                # h,w = img2.shape[:2]
                # img_btmL2 = img2[int(h*0.6):int(h),int(0):int(w*0.5)]
                self.param.img["g_result"]["img_rs"] = GetYoutube.set_yt_image(
                    self.param.inputs["crop"] | self.param.img['g_result']['crop_rs'],
                    self.img, crop=True, dsize=self.param.img["g_result"]["dsize"]
                )
                self.get_game_result2()
            # else:
                # data.game_finish_datetime = datetime.fromtimestamp(info.release_timestamp+sec, JST).strftime('%Y-%m-%d %T')
                # data.game_finish_url = f'{info.original_url}&t={sec}s'
                # stc[1].image(img_252p, caption=f'{data.game_finish_url}: {"WIN" if data.target_player_is_win else "LOSE"}')
            self.game_data.game_finish_datetime = datetime.fromtimestamp(self.yt_info['release_timestamp']+sec_buf, JST).strftime('%Y-%m-%d %T')
            self.game_data.game_finish_url = f"{self.yt_info['original_url']}&t={sec_buf}s"
            # data.target_player_name = info.channel #if info.channel in inputs['target_players'] else 'other'
            # data.title = info.title
            # data.category = target_category
            # game_data_list.append(data)
            # count=0
            self.count=0
            # states = trans(states, 'skip_interval')
            self.trans('skip_interval')
        # return game_data_list
        return 0

def trans(states, next_state):
    for state in states.keys():
        if state==next_state: states[state] = True
        else: states[state] = False
    return states

def ssbu_each_analysis(info, inputs, fighterlists, dsize_temp, temp_img, detector, target_des, match_ret, initial=0, total=43200, count_end=28, game_num=-1):
    #game_sec_list, interval_sec_list = get_game_interval_sec(test1(), test2())
    game_data_list = []
    count = 0
    #stc = st.columns([5,5])
    # 対戦カテゴリを自動選択
    if inputs['target_category']=='auto': target_category = get_category(info.title, {'VIP':['VIP'], 'smashmate':['めいと', 'メイト','レート', 'レーティング']})
    else: target_category = inputs['target_category']
    states = {'skip_interval':True, 'skip_game':False, 'find_game_start':False, 'get_fighter_name':False, 'find_game_finish': False, 'get_game_result':False}
    # bar = tqdm(total=total, leave=False, disable=False, initial=initial)
    # my_bar = st.progress(0)
    bar_text = f'{info.original_url[-11:]} -> find_game_start'
    # with st.expander("See results of the image processing", expanded=True):
    #     stc = st.columns([5,5])
    for sec in range(initial, total): 
        st_bar_text = f"Image processing in progress. Please wait. | {info.original_url[-11:]}: {int((sec+1)/total*100)}% ({sec+1}/{total} sec)"
        # my_bar.progress((sec+1)/total, text=st_bar_text)
        # bar.set_description(bar_text)
        # bar.update(1)
        # if ss.app_stop_clicked: break
        if game_num==len(game_data_list): break
        if states['skip_interval']:
            states['find_game_start'], count = skip_proc(count, count_end)
            if not states['find_game_start']: continue
            else:
                states = trans(states, 'find_game_start')
        if states['find_game_start']:
            bar_text = f'{info.original_url[-11:]} -> find_game_start'
            info,img = GetYoutube.get_yt_image(info, sec*info.fps, ydl_opts=inputs['ydl_opts'], dsize=inputs['dsize'], crop=inputs['crop'], gray=True)
            img_576p = img = cv2.resize(img, dsize=(1024,576))
            img_top = img_576p[0:int(img_576p.shape[0]*0.2),:]
            # with stc[0]:
            #     if find_game(img_top): states = trans(states, 'get_fighter_name')
        if states['get_fighter_name']:
            bar_text = f'{info.original_url[-11:]} -> get_fighter_name'
            img_252p = cv2.resize(img, dsize=(448,252))
            h,w = img_252p.shape[0],img_252p.shape[1]
            img_topL = img_252p[int(h*0.02):int(h*0.13), int(w*0.10):int(w*0.43)]
            img_topR = img_252p[int(h*0.02):int(h*0.13), int(w*0.60):int(w*0.93)]
            data = GameData()
            allowlist='irt'+string.ascii_uppercase
            data.fighter_id_1p, data.fighter_name_1p, easyOCR_txt_1p = get_fighter_name(easyOCR(img_topL,allowlist=allowlist), fighterlists)
            data.fighter_id_2p, data.fighter_name_2p, easyOCR_txt_2p = get_fighter_name(easyOCR(img_topR,allowlist=allowlist), fighterlists)
            #stc[0].write(f'easyOCR_txt: {easyOCR_txt_1p} vs {easyOCR_txt_2p}')
            if data.fighter_id_1p==0:
                data.fighter_id_1p, data.fighter_name_1p, kerasOCR_txt_1p = get_fighter_name(
                    # kerasOCR(cv2.cvtColor(img_topL, cv2.COLOR_GRAY2RGB), blocklist=f'[^{allowlist}]'), fighterlists, 
                    #slice_start=[-4], slice_end=[None]
                )
                #stc[0].write(f'kerasOCR_txt_1p: {kerasOCR_txt_1p}')
            if data.fighter_id_2p==0:
                #img_topR = img_252p[int(h*0.02):int(h*0.13), int(w*0.60):int(w*0.93)]
                data.fighter_id_2p, data.fighter_name_2p, kerasOCR_txt_2p = get_fighter_name(
                    # kerasOCR(cv2.cvtColor(img_topR,cv2.COLOR_GRAY2RGB),blocklist=f'[^{allowlist}]'), fighterlists, 
                    #slice_start=[-4], slice_end=[None]
                )
                #stc[0].write(f'kerasOCR_txt_2p: {kerasOCR_txt_2p}')
            if (data.fighter_name_1p in inputs['target_1p_fighters'] and data.fighter_id_2p!=0) or (data.fighter_id_1p!=0 and data.fighter_name_2p in inputs['target_1p_fighters']):
                count=0
                states = trans(states, 'skip_game')
                data.game_start_datetime = datetime.fromtimestamp(info.release_timestamp+sec, JST).strftime('%Y-%m-%d %T')
                data.game_start_url = f'{info.original_url}&t={sec}s'
                # stc[0].image(img_252p, caption=f'{data.game_start_url}: {data.fighter_name_1p} vs {data.fighter_name_2p}')
            else:
                states = trans(states, 'find_game_start')
        if states['skip_game']:
            states['find_game_finish'], count = skip_proc(count, count_end, interval=False)
            if not states['find_game_finish']: continue
            else:
                states = trans(states, 'find_game_finish')
        if states['find_game_finish']:
            bar_text = f'{info.original_url[-11:]} -> find_game_finish'
            info,img = GetYoutube.get_yt_image(info, sec*info.fps, ydl_opts=inputs['ydl_opts'], dsize=inputs['dsize'], crop=inputs['crop'], gray=True)
            img_252p = cv2.resize(img, dsize=dsize_temp)
            h,w = img_252p.shape[0],img_252p.shape[1]
            img_cent = img_252p[int(h*0.16):int(h*0.64),int(w*0.21):int(w*0.79)]
            if find_game(img_cent, temp_img=temp_img, detector=detector, target_des=target_des, match_ret=match_ret): states = trans(states, 'get_game_result')
        if states['get_game_result']:
            bar_text = f'{info.original_url[-11:]} -> get_game_result'
            img_720p = cv2.resize(img, dsize=(1280,720))
            h,w = img_720p.shape[0],img_720p.shape[1]
            img_btmL = img_720p[int(h*0.847):int(h*0.927),int(w*0.266):int(w*0.343)] # 100～1の位
            img_btmR = img_720p[int(h*0.847):int(h*0.927),int(w*0.651):int(w*0.728)] # 100～1の位
            # with stc[1]:
            #     data = get_game_result(img_btmL, img_btmR, data, inputs['target_1p_fighters'])
            if data.target_player_is_win==None:
                sec2 = sec+7
                info,img2 = GetYoutube.get_yt_image(info, sec2*info.fps, ydl_opts=inputs['ydl_opts'], dsize=inputs['dsize'], crop=inputs['crop'], gray=True)
                h,w = img2.shape[:2]
                img_btmL2 = img2[int(h*0.6):int(h),int(0):int(w*0.5)]
                #allowlist = re.sub('[.& ]','', target_fighter)
                allowlist = re.sub('[.& ]','', data.fighter_name_1p+data.fighter_name_2p)
                target_fighter = data.fighter_name_1p if data.fighter_name_1p in inputs['target_1p_fighters'] else data.fighter_name_2p #if data.fighter_name_2p in target_1p_fighters else ''.join(target_1p_fighters)
                easyOCR_txt = set(easyOCR(img_btmL2,allowlist=allowlist))
                #stc[1].image(img_btmL2, caption=f'easyOCR_txt: {easyOCR_txt}')
                str_cnt=0
                for ocr_str in easyOCR_txt:
                    if ocr_str in target_fighter: str_cnt+=1
                    if str_cnt==3: data.target_player_is_win = True
                if str_cnt<3: data.target_player_is_win = False
                # fighter_name, easyOCR_txt = get_fighter_name(easyOCR(img_btmL2,allowlist=allowlist), fighterlists)[1:]
                # if fighter_name in inputs['target_1p_fighters']: data.target_player_is_win = True
                # else : data.target_player_is_win = False
                data.game_finish_datetime = datetime.fromtimestamp(info.release_timestamp+sec+7, JST).strftime('%Y-%m-%d %T')
                data.game_finish_url = f'{info.original_url}&t={sec2}s'
                # stc[1].image(cv2.resize(img2, dsize=dsize_temp), caption=f'{data.game_finish_url}: {"WIN" if data.target_player_is_win else "LOSE"}')
            else:
                data.game_finish_datetime = datetime.fromtimestamp(info.release_timestamp+sec, JST).strftime('%Y-%m-%d %T')
                data.game_finish_url = f'{info.original_url}&t={sec}s'
                # stc[1].image(img_252p, caption=f'{data.game_finish_url}: {"WIN" if data.target_player_is_win else "LOSE"}')
            data.target_player_name = info.channel #if info.channel in inputs['target_players'] else 'other'
            data.title = info.title
            data.category = target_category
            game_data_list.append(data)
            count=0
            states = trans(states, 'skip_interval')
    return game_data_list

# 対戦している2キャラとその勝敗結果を取得し、それらに応じて対戦開始画面に飛べるURLをbigqueryに保存する
#@stop_watch
def ssbu_analysis(inputs):
    
    # init_ss('app_stop_clicked', False)
    yt = inputs['yt']
    #yt = select_analysis_target(inputs['yt'])

    # 認識用とデータベース登録用のキャラ名のリストを取得
    fighterlists = get_fighterlists(inputs['fighter_df'])
    dsize_temp = (448,252) # temp_match | (288,162) # feat_match_AKAZE | (352,198) # feat_match_ORB
    detector = None # cv2.AKAZE_create() # cv2.ORB_create()
    match_ret = -1 # 144 # feat_match_AKAZE | 72 # feat_match_ORB
    temp_img, target_des = get_templater('./images/gameset3.png', dsize=dsize_temp, detector=detector)
    
    # 動画毎に並行(並列)処理
    info_list = []
    info_lists = []
    # k = int(len(yt.infos)/2) if len(yt.infos)%2==0 else int(len(yt.infos)/2)+1
    # numThreads = os.cpu_count() - threading.active_count() # 最大スレッド数 - 使用中のスレッド数
    # k = k if k < numThreads  else numThreads
    k = 12
    thresults = []
    for i,info in enumerate(yt.infos):
        if i%k<k: 
            info_list.append(info)
        if i%k==(k-1) or i==(len(yt.infos)-1):
            info_lists.append(info_list)
            info_list = []
    #for i,info_list in enumerate(info_lists):
    for i,info_list in enumerate(info_lists):
        for j,info in enumerate(info_list):
            if '&t=' in info.original_url:
                end_count=51 #61
                initial = int(info.original_url[46:-1])-end_count
                total = initial+end_count*6#*4
                info.original_url = info.original_url[:43]
            else: 
                end_count=28
                initial = 0
                total = info.duration
            # thread = NewThread(
            #     target=ssbu_each_analysis, 
            #     args=(info, inputs, fighterlists, dsize_temp, temp_img, detector, target_des, match_ret),
            #     kwargs=dict(initial=initial, total=total, count_end=end_count)
            # )
        #     init_ss(f't{i}{j}', add_script_run_ctx(thread))
        # for j in range(len(info_list)):
        #     ss[f't{i}{j}'].start()
        # for j in range(len(info_list)):
        #     thresults += ss[f't{i}{j}'].join()
        # for j in range(len(info_list)):
        #     del_ss(f't{i}{j}')
    #st.write(thresults)
    # ssbu_db = BigqueryDatabase(st.secrets['gcp_service_account'], 'ssbu_dataset')
    # data_id = len(ssbu_db.select_my_data('analysis_table', ('*',)))+1
    # for i in range(len(thresults)):
    #     thresults[i].id = data_id+i
    insert_item = tuple(vars(thresults[0]).keys())
    insert_data = [tuple(vars(data).values()) for data in thresults]
    print(insert_item)
    print(insert_data)
    # ssbu_db.insert_my_data('analysis_table', insert_item, insert_data, 9)

def select_analysis_target(yt):
    # ssbu_db = BigqueryDatabase(st.secrets['gcp_service_account'], 'ssbu_dataset')
    # df = ssbu_db.select_my_data('analysis_table', ('*',))
    # df_sort = df.sort_values('id')
    # url_list = [url[:43] for url in df_sort['url'].to_list()]
    info_list = [info for info in yt.infos]
    # for info in info_list:
    #     if info.original_url in url_list:
    #         yt.infos.remove(info)
    return yt

def get_fighterlists(fighter_df):
    df_sorted = fighter_df.sort_values(by='id')
    return [df_sorted['recog_name'].to_list(), df_sorted['fighter_id'].to_list(), df_sorted['fighter_name'].to_list()]

def get_templater(temp_img_path, dsize=None, detector=None):
    temp_img = cv2.imread(temp_img_path, 0)
    if dsize!=None:
        h,w = temp_img.shape
        temp_img = cv2.resize(temp_img, (int(w*(dsize[0]/1920)), int(h*(dsize[1]/1080))))
    if detector!=None: return None, detector.detectAndCompute(temp_img, None)[1]
    else: return temp_img, None

def get_category(title, category): 
    for k,V in category.items():
        for v in V:
            if v in title: return k
    return 'other'

def skip_proc(count, count_end=28, interval=True):
    if not interval: count_end*=2
    count+=1
    if count==count_end: return True, count
    else: return False, count

def find_game(img, temp_img=None, detector=None, target_des=None, match_ret=-1):
    if temp_img is None and detector==None and target_des==None and match_ret==-1: return detect_line(img, detect_edge(img))
    elif not temp_img is None: return temp_match(img, temp_img)
    # else: return feat_match(img, detector, target_des, match_ret) 

def get_fighter_name(txt, fighterlists, slice_start=[-4,-5], slice_end=[None,-1], str_num=3):
    # for recog_name, fighter_id, fighter_name in zip(fighterlists[0], fighterlists[1], fighterlists[2]):
    #     for start,end in zip(slice_start, slice_end):
    #         if (len(recog_name[start:end])>=str_num) and (recog_name[start:end] in txt): return fighter_id, fighter_name, txt
    # return 0, 'other', txt
    for start,end in zip(slice_start, slice_end):
        for recog_name, fighter_id, fighter_name in zip(fighterlists[0], fighterlists[1], fighterlists[2]):
            if (len(recog_name[start:end])>=str_num) and (recog_name[start:end] in txt): return fighter_id, fighter_name, txt
    return 0, 'other', txt

def get_game_result(img_1p, img_2p, data, target_1p_fighters):
    damage_1p = easyOCR(img_1p, allowlist=string.digits)
    damage_2p = easyOCR(img_2p, allowlist=string.digits)
    #st.write(f'easyOCR: 1P:{damage_1p} | 2P:{damage_2p}')
    # if damage_1p=='' and damage_2p=='':
        # damage_1p = kerasOCR(cv2.cvtColor(img_1p, cv2.COLOR_GRAY2RGB), blocklist='\D')
        #st.write(f'kerasOCR: 1P:{damage_1p}')
        # damage_1p = gcvOCR(img_1p, blocklist='\D') # '\D'='[^0-9]'：すべての数字以外の文字
        # st.write(f'gcvOCR: 1P:{damage_1p}')
        # if damage_1p=='': 
            # damage_2p = kerasOCR(cv2.cvtColor(img_2p, cv2.COLOR_GRAY2RGB), blocklist='\D')
            #st.write(f'kerasOCR: 2P:{damage_2p}')
            # damage_2p = gcvOCR(img_2p, blocklist='\D') # '\D'='[^0-9]'：すべての数字以外の文字
            # st.write(f'gcvOCR: 2P:{damage_2p}')
    # st.image(img_1p)
    # st.image(img_2p)
    if data.fighter_name_1p in target_1p_fighters:
        data.target_player_is_1p = True
        if re.compile('\d').search(damage_1p) and damage_2p=='': data.target_player_is_win = True
        elif re.compile('\d').search(damage_2p) and damage_1p=='': data.target_player_is_win = False
        else: data.target_player_is_win = None
    else:
        data.target_player_is_1p = False
        if re.compile('\d').search(damage_1p) and damage_2p=='': data.target_player_is_win = False
        elif re.compile('\d').search(damage_2p) and damage_1p=='': data.target_player_is_win = True
        else: data.target_player_is_win = None
    return data

def detect_edge(img_gray, sigma = 0.33, kernel = 0):
    img_blur = cv2.GaussianBlur(img_gray, (kernel, kernel), sigma)

    # Automatic Thresholds Finding
    med_val = np.median(img_blur)
    min_val = int(max(0, (1.0 - sigma) * med_val))
    max_val = int(max(255, (1.0 + sigma) * med_val))
    
    return cv2.Canny(img_blur, threshold1 = min_val, threshold2 = max_val, L2gradient = True)

def detect_line(img, img_edges):
    # Hough変換で直線を検出
    img_lines = cv2.HoughLines(img_edges, rho=1, theta=np.pi/180, threshold=200)
    if not img_lines is None:
        if is_start(img, img_lines):
            #st.image(draw_line(img,img_lines))
            return True
    #else: st.image(img, caption='line_count: 0')
    return False

def draw_line(img, img_lines):
    img_copy = img.copy()
    for line in img_lines:
        rho, theta = line[0]
        h, w = img.shape[:2]
        # 直線が垂直のとき
        if np.isclose(np.sin(theta), 0):
            x1, y1 = rho, 0
            x2, y2 = rho, h
        # 直線が垂直じゃないとき
        else:
            # 直線の式を式変形すればcalc_yの式がもとまる
            calc_y = lambda x: rho / np.sin(theta) - x * np.cos(theta) / np.sin(theta)
            x1, y1 = 0, calc_y(0)
            x2, y2 = w, calc_y(w)
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
        # 直線を描画
        img_copy = cv2.line(img_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
    return img_copy

def draw_target_line(img_copy, rho, theta, color):
    h, w = img_copy.shape[:2]
    # 直線の式を式変形すればcalc_yの式がもとまる
    calc_y = lambda x: rho / np.sin(theta) - x * np.cos(theta) / np.sin(theta)
    x1, y1 = 0, calc_y(0)
    x2, y2 = w, calc_y(w)
    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
    # 直線を描画
    return cv2.line(img_copy, (x1, y1), (x2, y2), color, 2)

# 対戦開始のタイミングならTrue
# target_rho_list=[[17.0,17.0], [38.0,38.0], [40.0,40.0], [86.0,86.0], [90.0,90.0], [104.0,104.0]], target_theta=1.535897, error_range=10**-2, target_line_num=[2,6]
def is_start(img, img_lines, target_rho_list=[[17.0,17.0],[33.0,33.0], [86.0,87.0], [90.0,90.0], [104.0,104.0]], target_theta=1.535889744758606, error_range=10**-14, target_line_num=[1,4]):
    for d in range(256):
        if d**3 >= target_line_num[1]: break
    colors = [(r,g,b) for r in range(0,256,int(255/(d-1))) for g in range(0,256,int(255/(d-1))) for b in range(0,256,int(255/(d-1)))]
    img_copy = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    # いい感じの直線の数
    line_count = 0
    for line in img_lines:
        rho, theta = line[0]
        # いい感じの角度の直線ならカウントして描画する
        if np.abs(theta - target_theta) < error_range:
            for target_rho in target_rho_list:
                if target_rho[0]<=rho and rho<=target_rho[1]:
                    line_count += 1            
                    if line_count <= target_line_num[1]:
                        #st.write(f'theta: {theta}, rho: {rho}')
                        #print(f'{rho},',end='')
                        img_copy = draw_target_line(img_copy, rho, theta, colors[line_count-1])
                    break
    # 2～6本あれば対戦開始のタイミング
    if target_line_num[0]<=line_count and line_count<=target_line_num[1]:
        #print()
        #st.image(img_copy, caption=f'line_count: {line_count}')
        return True
    else: return False

def easyOCR(img, lang_list=['en'], allowlist=string.ascii_letters+string.digits, verbose=False):
    reader = easyocr.Reader(lang_list=lang_list, verbose=verbose)
    txt = ''
    for ocr_res in reader.readtext(img, allowlist=allowlist, detail=0):
        txt+=ocr_res
    return re.sub(' ', '', txt)

# GCP Cloud Vision APIでテキスト抽出やーる（Python3.6）# https://qiita.com/SatoshiGachiFujimoto/items/2ff2777ccdbc74c1c5bb
# Google CloudのCloud Vision APIで画像から日本語の文字抽出をしてみた # https://dev.classmethod.jp/articles/google-cloud_vision-api/
# def gcvOCR(img, lang_list=['en'], blocklist='\W', account=st.secrets["gcp_service_account"]): # '\W'=[^a-zA-Z_0-9]:英字、＿、数字以外の文字
#     # Instantiates a client
#     if type(account) in [dict, st.runtime.secrets.AttrDict]:
#         credentials = service_account.Credentials.from_service_account_info(account)
#     else:
#         credentials = service_account.Credentials.from_service_account_file(account)
#     client = vision.ImageAnnotatorClient(credentials=credentials)

#     # Loads the image into memory (bytes)
#     content = cv2.imencode(".png", img)[1].tostring()
#     image = vision.Image(content=content)

#     # Performs text detection on the image
#     response = client.text_detection(image=image, image_context={'language_hints':lang_list})
#     txt = response.full_text_annotation.text
#     return re.sub(blocklist, '', txt)

# def kerasOCR(img, blocklist='\W'):
#     # keras-ocr will automatically download pretrained
#     # weights for the detector and recognizer.
#     pipeline = kerasocr.pipeline.Pipeline()

#     # Get a set of the example image
#     img_keras = kerasocr.tools.read(img)

#     #st.image(img_keras)

#     # Each list of predictions in prediction_groups is a list of
#     # (word, box) tuples.
#     prediction_groups = pipeline.recognize([img_keras], detection_kwargs=dict(verbose=0), recognition_kwargs=dict(verbose=0))

#     # fig, ax = plt.subplots(figsize=(20, 20))
#     # kerasocr.tools.drawAnnotations(
#     #     image=img_keras, predictions=prediction_groups[0], ax=ax
#     # )
#     # st.pyplot(fig)
#     #print('test_kerasocr:',re.sub(blocklist, '', prediction_groups[0][0][0].upper()))
#     txt = ''.join([prediction[0] for prediction in prediction_groups[0]])
#     #os.system('cls')
#     return re.sub(blocklist, '', txt.upper())

def temp_match(img, temp_img, match_val=0.474): #match_val=0.474
    result = cv2.matchTemplate(img, temp_img, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if(match_val<max_val and max_val<1.0):
        return True
    else:
        return False

# Python + OpenCVで画像の類似度を求める # https://qiita.com/best_not_best/items/c9497ffb5240622ede01
# def feat_match(img, detector, target_des, match_ret):
#     (comparing_kp, comparing_des) = detector.detectAndCompute(img, None)
#     bf = cv2.BFMatcher(cv2.NORM_HAMMING)
#     try:
#         matches = bf.match(target_des, comparing_des)
#         dist = [m.distance for m in matches]
#         ret = sum(dist) / len(dist)
#     except cv2.error:
#         ret = match_ret
#     if ret<match_ret:
#         return True
#     else:
#         return False
    
def test1(): #vs時の動画秒数（https://www.youtube.com/watch?v=6aUsPo83Rsw）
            #267    
    return [263,    607,    843,    1067,   1287,   1597,   1918,   2183,   2667,   2928, 
            3208,   3550,   3892,   4114,   4359,   4564,   4961,   5175,   5449,   5623, 
            5904,   6328,   6571,   6756,   7115,   7375,   7673,   8002,   8300,   8556, 
            8750,   8937,   9188,   9553,   9828,   10099,  10404,  10620,  10837,  11202, 
            11416,  11725,  11925,  12046,  12402,  12751,  13086,  13498,  13766,  14053, 
            14467,  14828,  15137,  15397,  15996,  16335,  16590,  16946,  17229,  17562, 
            17922,  18176,  18442,  18748,  19119,  19519,  19746,  20030,  20124,  20282, 
            20509,  20817,  21170,  21492,  21739,  22096,  22376]

def test2(): #GAMESET時の動画秒数（https://www.youtube.com/watch?v=6aUsPo83Rsw）
    return [569,    799,    989,    1237,   1553,   1838,   2143,   2483,   2892,   3082,
            3503,   3759,   4073,   4298,   4534,   4772,   5139,   5388,   5589,   5858, 
            6165,   6531,   6718,   6968,   7335,   7542,   7952,   8215,   8516,   8662, 
            8891,   9142,   9391,   9791,   10012,  10365,  10498,  10790,  11074,  11375, 
            11684,  11856,  12010,  12289,  12715,  13046,  13388,  13732,  14015,  14328, 
            14787,  15029,  15354,  15640,  16280,  16551,  16730,  17196,  17523,  17800, 
            18135,  18401,  18593,  19076,  19338,  19713,  19927,  20087,  20247,  20416, 
            20782,  21061,  21446,  21703,  21969,  22335,  22620]

def get_game_interval_sec(game_start, game_finish):
    return [e-s for s,e in zip(game_start, game_finish)], [s-e for s,e in zip(game_start[1:], game_finish[:-1])]

def test_find_game_start():
    ydl_opts = {'verbose':True, 'format':'best', 'cookiesfrombrowser':('chrome',)}
    url_list = [
        #'https://www.youtube.com/watch?v=6aUsPo83Rsw',
        'https://www.youtube.com/watch?v=_pYOceaWgUE'
    ]
    for i,url in enumerate(url_list):
            if i==0: all_yt = GetYoutube(url, ydl_opts=ydl_opts)
            else: all_yt.infos += GetYoutube(url, ydl_opts=ydl_opts).infos
    inputs = {
            'ydl_opts':ydl_opts,
            #'url':url,
            'target_category':'auto',
            'target_1p_fighters':['KAMUI','BYLETH'],
            #'fighter_df':fighter_df,
            'yt':all_yt,
            'crop':None,
            #'crop':{"left": 0, "top": 0, "width": 1580, "height": 889},
            'dsize':(1920,1080)
        }
    sec_list = range(5173,5174)
    #sec_list = test1()
    for info in inputs['yt'].infos:
        for sec in sec_list: 
            info,img = GetYoutube.get_yt_image(info, sec*info.fps, ydl_opts=inputs['ydl_opts'], dsize=inputs['dsize'], crop=inputs['crop'], gray=True)
            img_576p = img = cv2.resize(img, dsize=(1024,576))
            img_top = img_576p[0:int(img_576p.shape[0]*0.2),:]
            #img_top = img_576p[0:int(img_576p.shape[0]*0.15),:]
            # if find_game(img_top): st.image(img, caption=f'sec: {sec}')

if __name__=="__main__":
    #print(len('https://www.youtube.com/watch?v=RAtI3Hl4weU&t='))
    #print(len('https://www.youtube.com/watch?v=RAtI3Hl4weU'))
    # ssbu_db = BigqueryDatabase(st.secrets['gcp_service_account'], 'ssbu_dataset')
    # df = ssbu_db.select_my_data('analysis_table', ('url',), ('target_player_name = "Ly"', 'target_player_is_win_lose_draw = "draw"',))
    # df_sort = df.sort_values('url')
    # url_list = df_sort['url'].to_list()
    # print(url_list)
    # game_sec_list, interval_sec_list = get_game_interval_sec(test1(), test2())
    # print(game_sec_list, min(game_sec_list))
    # print(interval_sec_list, min(interval_sec_list))
    test_find_game_start()