import pandas as pd
import streamsync as ss
import re
import sys
import webbrowser
from glob import glob as _glob
from os.path import join as _join
from os.path import dirname as _dirname
from os import remove as _remove
from os import rename as _rename
sys.path.append(_join(_dirname('__file__'), '..'))
from module.bq_db import SmashDatabase
from module.yt_obj import GetYoutube

# EVENT HANDLERS

def yt_url(state):
    _update_yt_url(state)
    _check_yt_url(state)

def start_game_screen(state):
    state["game_screen"]["button"]["disabled"] = "yes"
    _set_visibility(state, "yt_url", state["yt_url"].to_dict(), False)
    _get_game_screen(state)
    
def change_game_screen(state, payload):
    if type(payload)==float: _disable_game_screen(state)
    else: _update_game_screen(state)

def start_crop(state):
    _set_visibility(state, "crop", state["crop"].to_dict(), True)
    for i in range(state["sub_yt_num"]): 
        imr_file = state["game_screen"][f"html{i}"]["image_source"]
        imw_file = state["game_screen"][f"html{i}"]["image_source"][:-4]+"_1rect.jpg"
        if "1rect" not in imr_file:
            _rename(_join(_dirname('__file__'), imr_file), _join(_dirname('__file__'), imw_file))
            state["game_screen"][f"html{i}"]["image_source"] = imw_file

def crop(state, payload):
    if type(payload)==float: _update_cropper(state)
    else: _update_game_screen(state, False)
    
def crop_button(state):
    _update_game_screen(state, True)
    
    
# LOAD / GENERATE DATA

def _get_main_df():
    return SmashDatabase('ssbu_dataset').select_chara_data()

def _get_main_yt(url):
    return GetYoutube(url).infos
    
def _get_game_screen(state):
    yt = state["main_yt"] = _get_main_yt(state["yt_url"]["text_input"]["state_element"])
    if len(yt)>state["sub_yt_num"]: state["main_yt_num"] = len(yt)
    else: state["sub_yt_num"] = state["main_yt_num"] = len(yt)
    for i in range(state["sub_yt_num"]):
        GetYoutube.get_yt_image(yt[i], sec_pos=0, imw_path=_join(_dirname('__file__'), f'static/image{i}.jpg'))
        state["game_screen"][f"html{i}"]["image_source"] = f'static/image{i}.jpg'
        state["game_screen"][f"html{i}"]["inside"] = yt[i]["original_url"]
        state["game_screen"][f"html{i}"]["slider_number"]["max_value"] = yt[i]["duration"]
        state["game_screen"][f"html{i}"]["visibility"] = True
    state["game_screen"]["radio_button"]["visibility"] = True
    
# UPDATES

def _set_visibility(state, key, state_dict, sw, ):
    for k in state_dict.keys():
        state[key][k]["visibility"] = sw

def _update_yt_url(state):
    playlist = "https://www.youtube.com/playlist?list=PLxWXI3TDg12zJpAiXauddH_Mn8O9fUhWf"
    watch = "https://www.youtube.com/watch?v=My3gyDHoGAs"
    state["yt_url"]["text_input"]["place_holder"] = playlist if "playlist" in state["yt_url"]["check_box"]["state_element"] else watch

def _check_yt_url(state):
    if len(state["yt_url"]["text_input"]["place_holder"])==len(state["yt_url"]["text_input"]["state_element"]):
        state["game_screen"]["button"]["visibility"] = True
        state["yt_url"]["text"]["visibility"] = False
    else: 
        state["game_screen"]["button"]["visibility"] = False
        state["yt_url"]["text"]["visibility"] = True

def _disable_game_screen(state):
    for i in range(state["sub_yt_num"]):
        num = state["game_screen"][f"html{i}"]["slider_number"]["state_element"]
        bnum = state["game_screen"][f"html{i}"]["slider_number"]["buf_state_element"]
        if num!=bnum:
            state["game_screen"][f"html{i}"]["button_disabled"] = "no"
            state["game_screen"][f"html{i}"]["slider_number"]["buf_state_element"] = num
            state["game_screen"]["ch"] = i
        else:
            state["game_screen"][f"html{i}"]["slider_number"]["visibility"] = False

def _update_game_screen(state):
    ch = state["game_screen"]["ch"]
    state["game_screen"][f"html{ch}"]["button_disabled"] = "yes"
    state["game_screen"][f"html{ch}"]["slider_number"]["visibility"] = False
    sec = int(state["game_screen"][f"html{ch}"]["slider_number"]["state_element"])
    yt = state["main_yt"]
    GetYoutube.get_yt_image(yt[ch], sec_pos=sec, imw_path=_join(_dirname('__file__'), f'static/image{ch}_{sec}.jpg'))
    _remove(_join(_dirname('__file__'), state["game_screen"][f"html{ch}"]["image_source"]))
    state["game_screen"][f"html{ch}"]["image_source"] = f'static/image{ch}_{sec}.jpg'
    state["game_screen"][f"html{ch}"]["inside"] = f'{yt[ch]["original_url"]}+&t={sec}s'
    for i in range(state["sub_yt_num"]): state["game_screen"][f"html{i}"]["slider_number"]["visibility"] = True

def __update_game_screen(state, crop=False):
    # 1rect+crop
    px = dict()
    for k in ["left", "top", "width", "height"]: px[k] = int(state["crop"][k]["state_element"])
    pt1 = (px["left"], px["top"])
    pt2 = (px["left"]+px["width"], px["top"]+px["height"])
    # gs
    for i in range(state["sub_yt_num"]):
        num = state["game_screen"][f"html{i}"]["slider_number"]["state_element"]
        bnum = state["game_screen"][f"html{i}"]["slider_number"]["buf_state_element"]
        state["game_screen"][f"html{i}"]["button_disabled"] = "yes"
        if num!=bnum:
            state["game_screen"][f"html{i}"]["slider_number"]["visibility"] = False
            state["game_screen"][f"html{i}"]["slider_number"]["buf_state_element"] = num
            sec = int(num)
            yt = state["main_yt"]
            GetYoutube.get_yt_image(yt[i], ydl_opts=state["ydl_opts"], sec_pos=sec, imw_path=_join(_dirname('__file__'), f'static/image{i}_{sec}.jpg'))
            if state["game_screen"][f"html{i}"]["image_source"]!=f'static/image{i}.jpg': _remove(_join(_dirname('__file__'), state["game_screen"][f"html{i}"]["image_source"]))
            state["game_screen"][f"html{i}"]["image_source"] = f'static/image{i}_{sec}.jpg'
            state["game_screen"][f"html{i}"]["inside"] = f'{yt[i]["original_url"]}+&t={sec}s'
        # 1rect
        if "1rect" in state["game_screen"][f"html{i}"]["image_source"]:
            if i==0: state["crop"]["crop_button"]["disabled"] = "yes"
            state["game_screen"][f"html{i}"]["slider_number"]["visibility"] = False
            _remove(_join(_dirname('__file__'), state["game_screen"][f"html{i}"]["image_source"]))
            GetYoutube.set_yt_image(
                rect={'check':{'pt1':pt1, 'pt2':pt2, 'color':(255, 0, 0), 'thickness':3}}, 
                imr_path=_join(_dirname('__file__'), f'static/image{i}_{int(num)}.jpg'),
                imw_path=_join(_dirname('__file__'), f'static/image{i}_{int(num)}_1rect.jpg')
            )
            state["game_screen"][f"html{i}"]["image_source"] = f'static/image{i}_{int(num)}_1rect.jpg'
            if i==3: state["crop"]["crop_button"]["disabled"] = "no"
        # crop
        if crop:
            if i==0:
                state["crop"]["crop_button"]["disabled"] = state["check"]["crop_button"]["disabled"] = "yes"
                state["game_screen"]["radio_button"]["state_element"] = None
                _set_visibility(state, "crop", state["crop"].to_dict(), False)
            GetYoutube.set_yt_image(
                rect={'check':{'pt1':pt1, 'pt2':pt2, 'color':(255, 0, 0), 'thickness':3}}, 
                imr_path=_join(_dirname('__file__'), f'static/image{i}_{int(num)}.jpg'),
                imw_path=_join(_dirname('__file__'), f'static/image{i}_{int(num)}_crop.jpg')
            )
            state["game_screen"][f"html{i}"]["image_source"] = f'static/image{i}_{int(num)}_crop.jpg'
            _remove(_join(_dirname('__file__'), state["game_screen"][f"html{i}"]["image_source"]))
    # all
    for i in range(state["sub_yt_num"]): state["game_screen"][f"html{i}"]["slider_number"]["visibility"] = True
    
def _update_cropper(state):
    num = dict()
    bnum = dict()
    for k in ["left", "top", "width", "height"]:
        num[k] = state["crop"][k]["state_element"]
        bnum[k] = state["crop"][k]["buf_state_element"]
        if num[k]!=bnum[k]:
            state["crop"]["check_button"]["disabled"] = "no"
            if k=="height": state["crop"]["width"]["buf_state_element"] = state["crop"]["width"]["state_element"] = int(num["height"]*16/9)
            if k=="width": state["crop"]["height"]["buf_state_element"] = state["crop"]["height"]["state_element"] = int(num["width"]*9/16)
            state["crop"][k]["buf_state_element"] = state["crop"][k]["state_element"]
            
def _rename_image(state):
    pass

# STATE INIT

initial_state = ss.init_state({
    "main_df": _get_main_df(),
    "main_yt": [], #_get_main_yt(),
    "main_yt_num": None,
    "sub_yt_num": 4,
    "yt_url": {
        "text_input": {
            "place_holder": "https://www.youtube.com/watch?v=My3gyDHoGAs",
            "state_element": [None],
            "visibility": True
        },
        "check_box": {
            "state_element": [None],
            "visibility": True
        },
        "text": {
            "visibility": False
        },
    },
    "game_screen": {
        "button": {
            "disabled": "no",
            "visibility": False
        },
        "ch": None,
        "html0": {
            "slider_number": {
                "max_value": 25252,
                "state_element": 0,
                "buf_state_element": 0,
                "visibility": True
            },
            "button_disabled": "yes",
            "image_source": None,
            "inside": "url",
            "visibility": False
        },
        "html1": {
            "slider_number": {
                "max_value": 25252,
                "state_element": 0,
                "buf_state_element": 0,
                "visibility": True
            },
            "button_disabled": "yes",
            "image_source": None,
            "inside": "url",
            "visibility": False
        },
        "html2": {
            "slider_number": {
                "max_value": 25252,
                "state_element": 0,
                "buf_state_element": 0,
                "visibility": True
            },
            "button_disabled": "yes",
            "image_source": None,
            "inside": "url",
            "visibility": False
        },
        "html3": {
            "slider_number": {
                "max_value": 25252,
                "state_element": 0,
                "buf_state_element": 0,
                "visibility": True
            },
            "button_disabled": "yes",
            "image_source": None,
            "inside": "url",
            "visibility": False,
        },
        "radio_button": {
            "state_element": None,
            "visibility": False
        }
    },
    "crop": {
        "left": {
            "state_element": 0,
            "buf_state_element": 0,
            "visibility": False
        },
        "top": {
            "state_element": 0,
            "buf_state_element": 0,
            "visibility": False
        },
        "width": {
            "state_element": 640,
            "buf_state_element": 640,
            "visibility": False
        },
        "height": {
            "state_element": 360,
            "buf_state_element": 360,
            "visibility": False
        },
        "check_button": {
            "disabled": "yes",
            "visibility": False
        },
        "crop_button": {
            "disabled": "yes",
            "visibility": False
        }
    }
})

#{'left':0,'width':1280,'top':0,'height':720}

def _dev_init_state(sw=True):
    # game_screen
    # for i in range(4): initial_state["game_screen"][f"html{i}"]["visibility"] = sw
    # initial_state["game_screen"]["radio_button"]["visibility"] = sw
    file_list = _glob(_join(_dirname('__file__'),'static/image*.jpg'))
    for file in file_list: _remove(file)
    # crop
    # _set_visibility(initial_state, "crop", initial_state["crop"].to_dict(), True)
    
def _start():
    # 任意のブラウザで開いてもpythonの実行を止めない https://qiita.com/benisho_ga/items/4844920a002f9d07c9c1
    browser = webbrowser.get('"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" %s &')
    browser.open("http://localhost:20000")

_dev_init_state()
#_start()