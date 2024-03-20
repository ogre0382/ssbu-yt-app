import pandas as pd
import streamsync as ss
import re
import sys
from glob import glob as _glob
from os.path import join as _join
from os.path import dirname as _dirname
from os import remove as _remove
sys.path.append(_join(_dirname('__file__'), '..'))
from module.bq_db import SmashDatabase
from module.yt_obj import GetYoutube

class Test:
    def __init__(self, name):
        self.name = name

# EVENT HANDLERS

def yt_url(state):
    _update_yt_url(state)
    _check_yt_url(state)

def game_screen(state, payload):
    _set_visibility(state, "yt_url", state["yt_url"].to_dict(), False)
    if len(state["main_yt"])==0:
        _get_game_screen(state)
    else:
        if type(payload)==float: _disable_game_screen(state)
        else: _update_game_screen(state)
        
def crop(state, payload):
    if state["game_screen"]["radio_button"]["state_element"]=="no":
        _set_visibility(state, "crop", state["crop"].to_dict(), True)
    _update_cropper(state)
    
# LOAD / GENERATE DATA

def _get_main_df():
    return SmashDatabase('ssbu_dataset').select_chara_data()

def _get_main_yt(url="https://www.youtube.com/watch?v=hFDOOCutwmk", ydl_opts={'verbose':True, 'format':'best'}):
    return GetYoutube(url, ydl_opts=ydl_opts).infos
    
def _get_game_screen(state):
    state["game_screen"]["button"]["disabled"]="yes"
    if state["yt_url"]["radio_button"]["state_element"]!=None: 
        state["ydl_ops"]['cookiesfrombrowser'] = (state["yt_url"]["radio_button"]["state_element"],)
    yt = state["main_yt"] = _get_main_yt(state["yt_url"]["text_input"]["state_element"], ydl_opts=state["ydl_ops"])
    if len(yt)>state["sub_yt_num"]: state["main_yt_num"] = len(yt)
    else: state["sub_yt_num"] = state["main_yt_num"] = len(yt)
    for i in range(state["sub_yt_num"]):
        GetYoutube.get_yt_image(yt[i], ydl_opts=state["ydl_ops"], sec_pos=0, imw_path=_join(_dirname('__file__'), f'static/image{i}.jpg'))
        state["game_screen"][f"html{i}"]["image_source"] = f'static/image{i}.jpg'
        state["game_screen"][f"html{i}"]["inside"] = yt[i]["original_url"]
        state["game_screen"][f"html{i}"]["slider_number"]["max_value"] = yt[i]["duration"]
        state["game_screen"][f"html{i}"]["visibility"] = True
    state["game_screen"]["radio_button"]["visibility"] = True
    
# UPDATES

def _set_visibility(state, key, state_dict, sw):
    for k in state_dict.keys():
        state[key][k]["visibility"] = sw

def _update_yt_url(state):
    playlist = "https://www.youtube.com/playlist?list=PLxWXI3TDg12zJpAiXauddH_Mn8O9fUhWf"
    watch = "https://www.youtube.com/watch?v=My3gyDHoGAs"
    state["yt_url"]["text_input"]["place_holder"] = playlist if "playlist" in state["yt_url"]["check_box"]["state_element"] else watch
    state["yt_url"]["radio_button"]["visibility"] = True if "members-only" in state["yt_url"]["check_box"]["state_element"] else False

def _check_yt_url(state):
    if len(state["yt_url"]["text_input"]["place_holder"])==len(state["yt_url"]["text_input"]["state_element"]):
        state["game_screen"]["button"]["visibility"] = True
        state["yt_url"]["text"]["visibility"] = False
    else: 
        state["game_screen"]["button"]["visibility"] = False
        state["yt_url"]["text"]["visibility"] = True

def _disable_game_screen(state):
    screen = state["game_screen"]
    for i in range(state["sub_yt_num"]):
        if screen[f"html{i}"]["slider_number"]["state_element"]!=screen[f"html{i}"]["slider_number"]["buf_state_element"]:
            state["game_screen"][f"html{i}"]["button_disabled"] = "no"
        else:
            state["game_screen"][f"html{i}"]["button_disabled"] = "yes"
            state["game_screen"][f"html{i}"]["slider_number"]["visibility"] = False

def _update_game_screen(state):
    screen = state["game_screen"]
    for i in range(state["sub_yt_num"]):
        state["game_screen"][f"html{i}"]["button_disabled"] = "yes"
        if screen[f"html{i}"]["slider_number"]["state_element"]!=screen[f"html{i}"]["slider_number"]["buf_state_element"]:
            state["game_screen"][f"html{i}"]["slider_number"]["visibility"] = False
            state["game_screen"][f"html{i}"]["slider_number"]["buf_state_element"] = screen[f"html{i}"]["slider_number"]["state_element"]
            sec = int(screen[f"html{i}"]["slider_number"]["state_element"])
            index = i
            break
    yt = state["main_yt"]
    GetYoutube.get_yt_image(yt[index], ydl_opts=state["ydl_opts"], sec_pos=sec, imw_path=_join(_dirname('__file__'), f'static/image{index}_{sec}.jpg'))
    if state["game_screen"][f"html{index}"]["image_source"]!=f'static/image{index}.jpg': _remove(_join(_dirname('__file__'), state["game_screen"][f"html{index}"]["image_source"]))
    state["game_screen"][f"html{index}"]["image_source"] = f'static/image{index}_{sec}.jpg'
    state["game_screen"][f"html{index}"]["inside"] = f'{yt[index]["original_url"]}+&t={sec}s'
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

# STATE INIT

initial_state = ss.init_state({
    "main_df": _get_main_df(),
    "main_yt": [], #_get_main_yt(),
    "main_yt_num": None,
    "sub_yt_num": 4,
    "ydl_opts": {
        'verbose':True,
        'format':'best'
    },
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
        "radio_button": {
            "state_element":None,
            "visibility": False
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
        "html0": {
            "slider_number": {
                "max_value": 25252,
                "state_element": 0,
                "buf_state_element": 0,
                "visibility": True
            },
            "button_disabled": "yes",
            "image_source": "static/image0.jpg",
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
            "image_source": "static/image1.jpg",
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
            "image_source": "static/image2.jpg",
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
            "image_source": "static/image3.jpg",
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
    for i in range(4): initial_state["game_screen"][f"html{i}"]["visibility"] = sw
    initial_state["game_screen"]["radio_button"]["visibility"] = sw
    file_list = _glob(_join(_dirname('__file__'),'static/image*_*.jpg'))
    for file in file_list: _remove(file)
    # crop
    # _set_visibility(initial_state, "crop", initial_state["crop"].to_dict(), True)

_dev_init_state()