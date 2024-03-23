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
    if type(payload)==float:
        _secnum_game_screen(state)
    else: 
        _set_visibility(state, "game_screen", state["game_screen"].to_dict(), False, "slider_number", ['button','ch','radio_button'])
        _update_game_screen(state)

def start_stop_crop_3rect(state):
    _set_visibility(state, "game_screen", state["game_screen"].to_dict(), False, "slider_number", ['button','ch','radio_button'])
    if state["game_screen"]["radio_button"]["state_element"]=="no":
        _set_visibility(state, "crop", state["crop"].to_dict(), True)
        for i in range(state["sub_yt_num"]):
            sec = int(state["game_screen"][f"html{i}"]["slider_number"]["state_element"])
            state["game_screen"][f"html{i}"]["image_source"] = f'static/image{i}_{sec}.jpg'
    else:
        state["game_screen"]["radio_button"]["visibility"]=False
        _update_3rect_game_screen(state)
        state["collect"]["radio_button"]["visibility"] = True
    
def check_crop(state, payload):
    if type(payload)==float: _update_cropper(state)
    else: _update_1rect_game_screen(state)
    
def execute_crop(state):
    if state["game_screen"]["radio_button"]["state_element"]=="no":
        _set_visibility(state, "crop", state["crop"].to_dict(), False)
        _set_visibility(state, "game_screen", state["game_screen"].to_dict(), True, "slider_number", ['button','ch','radio_button'])
        state["crop"]["crop_button"]["disabled"] = "yes"
        _update_crop_game_screen(state)
        state["game_screen"]["radio_button"]["state_element"] = None
        
def collect(state):
    if state["collect"]["radio_button"]["state_element"]=="no":
        _init_state(state)
    else:
        pass
    
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
        GetYoutube.get_yt_image(yt[i], sec_pos=0, imw_path=_join(_dirname('__file__'), f'static/image{i}_0.jpg'))
        state["game_screen"][f"html{i}"]["image_source"] = f'static/image{i}_0.jpg'
        state["game_screen"][f"html{i}"]["inside"] = f'{yt[i]["original_url"]}&t={0}s'
        state["game_screen"][f"html{i}"]["slider_number"]["max_value"] = yt[i]["duration"]
        state["game_screen"][f"html{i}"]["visibility"] = True
    state["game_screen"]["radio_button"]["visibility"] = True
    
def _get_crop_pt(state):
    px = dict()
    for k in ["left", "top", "width", "height"]: px[k] = int(state["crop"][k]["state_element"])
    pt1 = (px["left"], px["top"])
    pt2 = (px["left"]+px["width"], px["top"]+px["height"])
    suffix = f'{px["left"]}_{px["top"]}_{px["width"]}_{px["height"]}'
    return pt1, pt2, suffix
    
# UPDATES

def _set_visibility(state, key, state_dict, sw, key2=None, ekeys=[]):
    for k in state_dict.keys():
        if k not in ekeys:
            if key2==None: state[key][k]["visibility"] = sw
            else: state[key][k][key2]["visibility"] = sw

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

def _secnum_game_screen(state):
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
    _remove(_join(_dirname('__file__'), state["game_screen"][f"html{ch}"]["image_source"]))
    state["game_screen"][f"html{ch}"]["button_disabled"] = "yes"
    sec = int(state["game_screen"][f"html{ch}"]["slider_number"]["state_element"])
    yt = state["main_yt"]
    GetYoutube.get_yt_image(yt[ch], sec_pos=sec, imw_path=_join(_dirname('__file__'), f'static/image{ch}_{sec}.jpg'))
    if "crop" in state["game_screen"][f"html{ch}"]["image_source"]:
        _remove(_join(_dirname('__file__'), f'{state["game_screen"][f"html{ch}"]["image_source"][:-9]}.jpg'))
        pt1, pt2, _ = _get_crop_pt(state)
        num = state["game_screen"][f"html{ch}"]["slider_number"]["state_element"]
        GetYoutube.set_yt_image(
            {'check':{'pt1':pt1, 'pt2':pt2, 'color':(255, 0, 0), 'thickness':3}}, 
            crop=True,
            imr_path=_join(_dirname('__file__'), f'static/image{ch}_{int(num)}.jpg'),
            imw_path=_join(_dirname('__file__'), f'static/image{ch}_{int(num)}_crop.jpg')
        )
        state["game_screen"][f"html{ch}"]["image_source"] = f'static/image{ch}_{sec}_crop.jpg'
    else:
        state["game_screen"][f"html{ch}"]["image_source"] = f'static/image{ch}_{sec}.jpg'
    state["game_screen"][f"html{ch}"]["inside"] = f'{yt[ch]["original_url"]}&t={sec}s'
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

def _update_1rect_game_screen(state):
    pt1, pt2, suffix = _get_crop_pt(state)
    state["crop"]["crop_button"]["disabled"] = "yes"
    for i in range(state["sub_yt_num"]):
        num = state["game_screen"][f"html{i}"]["slider_number"]["state_element"]
        GetYoutube.set_yt_image(
            {'check':{'pt1':pt1, 'pt2':pt2, 'color':(255, 0, 0), 'thickness':3}}, 
            rect=True,
            imr_path=_join(_dirname('__file__'), f'static/image{i}_{int(num)}.jpg'),
            imw_path=_join(_dirname('__file__'), f'static/image{i}_{int(num)}_{suffix}.jpg')
        )
        if state["game_screen"][f"html{i}"]["image_source"]!=f'static/image{i}_{int(num)}.jpg': _remove(_join(_dirname('__file__'), state["game_screen"][f"html{i}"]["image_source"]))
        state["game_screen"][f"html{i}"]["image_source"] = f'static/image{i}_{int(num)}_{suffix}.jpg'
    state["crop"]["check_button"]["disabled"] = "yes"
    state["crop"]["crop_button"]["disabled"] = "no"

def _update_crop_game_screen(state):
    pt1, pt2, _= _get_crop_pt(state)
    state["crop"]["crop_button"]["disabled"] = "yes"
    for i in range(state["sub_yt_num"]):
        num = state["game_screen"][f"html{i}"]["slider_number"]["state_element"]
        GetYoutube.set_yt_image(
            {'check':{'pt1':pt1, 'pt2':pt2, 'color':(255, 0, 0), 'thickness':3}}, 
            crop=True,
            imr_path=_join(_dirname('__file__'), f'static/image{i}_{int(num)}.jpg'),
            imw_path=_join(_dirname('__file__'), f'static/image{i}_{int(num)}_crop.jpg')
        )
        if state["game_screen"][f"html{i}"]["image_source"]!=f'static/image{i}_{int(num)}.jpg': _remove(_join(_dirname('__file__'), state["game_screen"][f"html{i}"]["image_source"]))
        state["game_screen"][f"html{i}"]["image_source"] = f'static/image{i}_{int(num)}_crop.jpg'

def _update_1rect_game_screen(state):
    pt1, pt2, suffix = _get_crop_pt(state)
    state["crop"]["crop_button"]["disabled"] = "yes"
    for i in range(state["sub_yt_num"]):
        num = state["game_screen"][f"html{i}"]["slider_number"]["state_element"]
        GetYoutube.set_yt_image(
            {'check':{'pt1':pt1, 'pt2':pt2, 'color':(255, 0, 0), 'thickness':3}}, 
            rect=True,
            imr_path=_join(_dirname('__file__'), f'static/image{i}_{int(num)}.jpg'),
            imw_path=_join(_dirname('__file__'), f'static/image{i}_{int(num)}_{suffix}.jpg')
        )
        if state["game_screen"][f"html{i}"]["image_source"]!=f'static/image{i}_{int(num)}.jpg': _remove(_join(_dirname('__file__'), state["game_screen"][f"html{i}"]["image_source"]))
        state["game_screen"][f"html{i}"]["image_source"] = f'static/image{i}_{int(num)}_{suffix}.jpg'
    state["crop"]["check_button"]["disabled"] = "yes"
    state["crop"]["crop_button"]["disabled"] = "no"
            
def _update_3rect_game_screen(state):
    cv2dict = dict()
    w,h = 1920,1080
    cv2dict['name1P']  = {'pt1':(int(w*0.10), int(h*0.02)), 'pt2':(int(w*0.43), int(h*0.13)), 'color':(255, 0, 0), 'thickness':3}
    cv2dict['name2P']  = {'pt1':(int(w*0.60), int(h*0.02)), 'pt2':(int(w*0.93), int(h*0.13)), 'color':(255, 0, 0), 'thickness':3}
    cv2dict['GameSet'] = {'pt1':(int(w*0.21), int(h*0.16)), 'pt2':(int(w*0.79), int(h*0.64)), 'color':(255, 0, 0), 'thickness':3}
    for i in range(state["sub_yt_num"]):
        num = state["game_screen"][f"html{i}"]["slider_number"]["state_element"]
        GetYoutube.set_yt_image(
            cv2dict, 
            rect=True,
            imr_path=_join(_dirname('__file__'), state["game_screen"][f"html{i}"]["image_source"]),
            imw_path=_join(_dirname('__file__'), state["game_screen"][f"html{i}"]["image_source"][:-4]+'_3rect.jpg')
        )
        state["game_screen"][f"html{i}"]["image_source"] = state["game_screen"][f"html{i}"]["image_source"][:-4]+'_3rect.jpg'

def _init_state(state):
    # game_screen
    # for i in range(4): initial_state["game_screen"][f"html{i}"]["visibility"] = sw
    # initial_state["game_screen"]["radio_button"]["visibility"] = sw
    file_list = _glob(_join(_dirname('__file__'),'static/image*.jpg'))
    for file in file_list: _remove(file)
    state["collection"]["radio_button"]["state_element"] = None
    state["collect"]["radio_button"]["visibility"] = False
    _set_visibility(state, "game_screen", state["game_screen"].to_dict(), True, "slider_number", ['button','ch','radio_button'])
    _set_visibility(state, "game_screen", state["game_screen"].to_dict(), False, ekeys=['button','ch','radio_button'])
    _set_visibility(state, "yt_url", state["yt_url"].to_dict(), True)
    state["game_screen"]["button"]["disabled"] = "no"
    state["game_screen"]["button"]["visibility"] = False
    state["game_screen"]["radio_button"]["state_element"] = None
    state["yt_url"]["text_input"]["state_element"] = [None]
    # state["yt_url"]["check_box"]["state_element"] = [None]
    # crop
    # _set_visibility(initial_state, "crop", initial_state["crop"].to_dict(), True)

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
            "state_element": 1920,
            "buf_state_element": 1920,
            "visibility": False
        },
        "height": {
            "state_element": 1080,
            "buf_state_element": 1080,
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
    },
    "collect": {
        "radio_button": {
            "state_element": None,
            "visibility": False
        }
    }
})

#{'left':0,'width':1280,'top':0,'height':720}
    
def _start():
    # �C�ӂ̃u���E�U�ŊJ���Ă�python�̎��s���~�߂Ȃ� https://qiita.com/benisho_ga/items/4844920a002f9d07c9c1
    browser = webbrowser.get('"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" %s &')
    browser.open("http://localhost:20000")

_init_state()
#_start()

