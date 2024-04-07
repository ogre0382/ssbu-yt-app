import pandas as pd
import streamsync as ss
import re
import webbrowser
from glob import glob as _glob
from os.path import dirname as _dirname
from os.path import join as _join
from os import remove as _remove
from os import rename as _rename
from sys import path
path.append(_join(_dirname('__file__'), '..'))
# from module.esports_analysis import get_charalists as _get_charalists
# from module.esports_analysis import get_templater as _get_templater
from module.esports_analysis import Parameter
from module.bq_db import SmashDatabase
from module.yt_obj import GetYoutube
from module.test_data import part_gs_test as _part_gs_test
from module.test_data import full_gs_test as _full_gs_test

# EVENT HANDLERS

## Input YouTube URL
def yt_url(state):
    _update_yt_url(state)
    _check_yt_url(state)

## Check game screens
def start_game_screen(state):
    state["yt_url"]["visibility"] = False
    state["game_screen"]["visibility"] = True
    state["game_screen"]["message"]["visibility"] = True
    _get_game_screen(state)
    state["game_screen"]["message"]["visibility"] = False
    state["game_screen"]["radio_button"]["visibility"] = True
    
def change_game_screen(state, payload):
    if type(payload)==float:
        state["game_screen"]["radio_button"]["visibility"] = False
        _update_game_screen_secnum(state)
    else: 
        for i in range(state["sub_yt_num"]): state["game_screen"][f"html{i}"]["slider_number"]["visibility"] = False
        _update_game_screen(state)
        state["game_screen"]["radio_button"]["visibility"] = True

## Crop game screens
def start_stop_crop_3rect(state):
    for i in range(state["sub_yt_num"]): state["game_screen"][f"html{i}"]["slider_number"]["visibility"] = False
    state["game_screen"]["radio_button"]["visibility"] = False
    if state["game_screen"]["radio_button"]["state_element"]=="no":
        state["crop"]["visibility"] = True
    else:
        _update_proc_game_screen(state, rect=True, var_rect=False)
        state["option"]["visibility"] = True
    
def check_crop(state, payload):
    if type(payload)==float:
        _update_cropper(state)
        state["crop"]["check_button"]["disabled"] = "no"
        state["crop"]["crop_button"]["disabled"] = "yes"
    else:
        _update_proc_game_screen(state, rect=True)
        state["crop"]["check_button"]["disabled"] = "yes"
        state["crop"]["crop_button"]["disabled"] = "no"
    
def execute_crop(state):
    if state["game_screen"]["radio_button"]["state_element"]=="no":
        state["crop"]["visibility"] = False
        for i in range(state["sub_yt_num"]): state["game_screen"][f"html{i}"]["slider_number"]["visibility"] = True    
        state["crop"]["crop_button"]["disabled"] = "yes"
        _update_proc_game_screen(state, crop=True)
        state["game_screen"]["radio_button"]["state_element"] = None
        state["game_screen"]["radio_button"]["visibility"] = True

## Do you collect data from the following YouTube?
def option(state):
    if state["option"]["radio_button"]["state_element"]=="yes":
        state["option"]["inputs_visibility"] = True
        state["game_screen"]["visibility"] = False
        if state["inputs"]["crop"]==None: state["inputs"]["crop"]="None"
    else:
        _init_state(state)
    _update_option(state)
    print(state["inputs"])

## 対戦している2キャラとその勝敗結果を取得し、それらに応じて対戦開始画面に飛べるURLをbigqueryに保存する
def collect(state):
    #charalists = _get_charalists(state["inputs"]["chara_df"])
    state["option"]["visibility"] = False
    state["collect"]["repeater"]["visibility"] = True
    _update_view_results(state)

#### Event context https://www.streamsync.cloud/repeater.html
def view_results(state, payload, context):
    id = context["item"]["id"]
    # print(context["item"])
    # print(state["proc"]["repeater"][f"message{id}"])
    state["collect"]["repeater"][f"message{id}"]["visibility"] = True if "view" in payload else False
    # print(state["proc"]["repeater"][f"message{id}"])

# LOAD / GENERATE DATA

def _get_main_df():
    return SmashDatabase('ssbu_dataset').select_chara_data()

def _get_select(main_df=_get_main_df()):
    select_df = main_df.sort_values('chara_id')
    select_df = select_df['chara_name']
    select_dict = select_df.to_dict()
    return {v: v for v in select_dict.values()}

def _get_main_yt(url):
    return GetYoutube(url).infos
    
def _get_game_screen(state):
    yt_infos = state["inputs"]["yt_infos"] = _get_main_yt(state["yt_url"]["text_input"]["state_element"])
    if len(yt_infos)<state["main_yt_num"]: state["main_yt_num"] = len(yt_infos)
    if len(yt_infos)<state["sub_yt_num"]: state["sub_yt_num"] = len(yt_infos)
    for i in range(state["sub_yt_num"]):
        GetYoutube.get_yt_image(yt_infos[i], sec_pos=0, imw_path=_join(_dirname('__file__'), f'static/image{i}_0.jpg'))
        state["game_screen"][f"html{i}"]["image_source"] = f'static/image{i}_0.jpg'
        state["game_screen"][f"html{i}"]["inside"] = f'{yt_infos[i]["original_url"]}&t={0}s'
        state["game_screen"][f"html{i}"]["slider_number"]["max_value"] = yt_infos[i]["duration"]
    for i in range(state["sub_yt_num"]): state["game_screen"][f"html{i}"]["visibility"] = True
    
def _get_crop_pt(state):
    px = dict()
    for k in ["left", "top", "width", "height"]: px[k] = int(state["crop"][k]["state_element"])
    pt1 = [px["left"], px["top"]]
    pt2 = [px["left"]+px["width"], px["top"]+px["height"]]
    state["inputs"]["crop"] = {'crop':{'pt1':pt1, 'pt2':pt2}}
    cv2dict = {'crop':{'pt1':pt1, 'pt2':pt2, 'color':(255, 0, 0), 'thickness':3}}
    suffix = f'{px["left"]}_{px["top"]}_{px["width"]}_{px["height"]}'
    return cv2dict, suffix

def _get_3rect_pt():
    cv2dict = dict()
    w,h = 1920,1080
    cv2dict['name1P']  = {'pt1':(int(w*0.10), int(h*0.02)), 'pt2':(int(w*0.43), int(h*0.13)), 'color':(255, 0, 0), 'thickness':3}
    cv2dict['name2P']  = {'pt1':(int(w*0.60), int(h*0.02)), 'pt2':(int(w*0.93), int(h*0.13)), 'color':(255, 0, 0), 'thickness':3}
    cv2dict['GameSet'] = {'pt1':(int(w*0.21), int(h*0.16)), 'pt2':(int(w*0.79), int(h*0.64)), 'color':(255, 0, 0), 'thickness':3}
    suffix = "3rect"
    return cv2dict, suffix
    
# UPDATES

def _update_yt_url(state):
    playlist = "https://www.youtube.com/playlist?list=PLxWXI3TDg12zJpAiXauddH_Mn8O9fUhWf"
    watch = "https://www.youtube.com/watch?v=My3gyDHoGAs"
    state["yt_url"]["text_input"]["place_holder"] = playlist if "playlist" in state["yt_url"]["check_box_state_element"] else watch

def _check_yt_url(state):
    if len(state["yt_url"]["text_input"]["place_holder"])==len(state["yt_url"]["text_input"]["state_element"]):
        state["yt_url"]["button_visibility"] = True
        state["yt_url"]["text_visibility"] = False
    else: 
        state["yt_url"]["button_visibility"] = False
        state["yt_url"]["text_visibility"] = True

def _update_game_screen_secnum(state):
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
    yt_infos = state["inputs"]["yt_infos"]
    GetYoutube.get_yt_image(yt_infos[ch], sec_pos=sec, imw_path=_join(_dirname('__file__'), f'static/image{ch}_{sec}.jpg'))
    if "crop" in state["game_screen"][f"html{ch}"]["image_source"]:
        _remove(_join(_dirname('__file__'), f'{state["game_screen"][f"html{ch}"]["image_source"][:-9]}.jpg'))
        _update_proc_game_screen(state, crop=True, ch=ch)
    else:
        state["game_screen"][f"html{ch}"]["image_source"] = f'static/image{ch}_{sec}.jpg'
    state["game_screen"][f"html{ch}"]["inside"] = f'{yt_infos[ch]["original_url"]}&t={sec}s'
    for i in range(state["sub_yt_num"]): state["game_screen"][f"html{i}"]["slider_number"]["visibility"] = True

def _update_cropper(state):
    num = dict()
    bnum = dict()
    for k in ["left", "top", "width", "height"]:
        num[k] = state["crop"][k]["state_element"]
        bnum[k] = state["crop"][k]["buf_state_element"]
        if num[k]!=bnum[k]:
            if k=="height": state["crop"]["width"]["buf_state_element"] = state["crop"]["width"]["state_element"] = int(num["height"]*16/9)
            if k=="width": state["crop"]["height"]["buf_state_element"] = state["crop"]["height"]["state_element"] = int(num["width"]*9/16)
            state["crop"][k]["buf_state_element"] = state["crop"][k]["state_element"]
        
def _update_proc_game_screen(state, rect=False, crop=False, ch=4, var_rect=True):
    state["crop"]["crop_button"]["disabled"] = "yes"
    #check_gs_ans = state["game_screen"]["radio_button"]["state_element"]
    cv2dict, suffix = _get_crop_pt(state) if var_rect else _get_3rect_pt()
    if crop==True: suffix = "crop"
    ch_range = range(state["sub_yt_num"]) if ch==4 else range(ch,ch+1)
    for i in ch_range:
        sec = int(state["game_screen"][f"html{i}"]["slider_number"]["state_element"])
        imr_file = f'static/image{i}_{sec}.jpg' if var_rect else state["game_screen"][f"html{i}"]["image_source"]
        imw_file = f'static/image{i}_{sec}_{suffix}.jpg' if var_rect else f'{state["game_screen"][f"html{i}"]["image_source"][:-4]}_{suffix}.jpg'
        GetYoutube.set_yt_image(
            cv2dict, rect=rect, crop=crop,
            imr_path=_join(_dirname('__file__'), imr_file),
            imw_path=_join(_dirname('__file__'), imw_file)
        )
        if state["game_screen"][f"html{i}"]["image_source"]!=f'static/image{i}_{sec}.jpg' and ch==4:
            _remove(_join(_dirname('__file__'), state["game_screen"][f"html{i}"]["image_source"]))
        state["game_screen"][f"html{i}"]["image_source"] = imw_file
        
def _update_option(state):
    ## Input player name
    if "auto" in state["option"]["text_input"]["check_box_state_element"]:
        state["option"]["text_input"]["visibility"] = False
        state["inputs"]["target_player_name"] = "auto"
    else: 
        state["option"]["text_input"]["visibility"] = True
        state["inputs"]["target_player_name"] = state["option"]["text_input"]["state_element"]
    ## Select YouTube title category
    if "auto" in state["option"]["radio_button2"]["check_box_state_element"]:
        state["option"]["radio_button2"]["visibility"] = False
        state["inputs"]["target_category"] = "auto"
    else:
        state["option"]["radio_button2"]["visibility"] = True
        state["inputs"]["target_category"] = state["option"]["radio_button2"]["state_element"]
    ## Select fighters player use
    state["inputs"]["target_1p_charas"] = state["option"]["multiselect"]["state_element"]
    inputs = [input for input in state["inputs"].to_dict().values()]
    if '' in inputs or None in inputs:
        state["collect"]["visibility"] = False
    else:
        state["collect"]["visibility"] = True

## 対戦している2キャラとその勝敗結果を取得し、それらに応じて対戦開始画面に飛べるURLをbigqueryに保存する
def _update_view_results(state):
    inputs = state["inputs"]
    img_proc_temps = {
        "g_start": {
            "img_file": None,
            "dsize": (448,252)
        },
        "g_fighter": {
            "img_file": None,
            "dsize": (1024,576)
        },
        "g_finish": {
            "img_file": "gameset.png",
            "dsize": (448,252)
        },
        "g_result": {
            "img_file": None,
            "dsize": (1280,720)
        }
    }
    param = Parameter(inputs, img_proc_temps)
    for yt_info in inputs["yt_infos"]:
        param.get_yt_info(yt_info)
        print(param)
        print()


# STATE INIT

rel = False
full_gs = True

if not rel:
    if full_gs: target_1p_charas, yt_infos, crop= _full_gs_test()
    else: target_1p_charas, yt_infos, crop = _part_gs_test()

state_dict = {
    "main_yt_num": 10 if rel else len(yt_infos),
    "sub_yt_num": 4,
    "inputs": {
        "target_player_name": None if rel else 'auto',
        "target_category": None if rel else 'auto',
        "target_1p_charas": None if rel else target_1p_charas,
        "chara_df": _get_main_df(),
        "yt_infos": None if rel else yt_infos,
        "crop": None if rel else crop
    },
    "yt_url": {
        "text_input": {
            "place_holder": "https://www.youtube.com/watch?v=My3gyDHoGAs",
            "state_element": None,
        },
        "check_box_state_element": [None],
        "text_visibility": False,
        "button_visibility": False,
        "visibility": True if rel else False
    },
    "game_screen": {
        "message": {
            "text": "% Now Loading ...",
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
            "visibility": False
        },
        "radio_button": {
            "state_element": None,
            "visibility": False,
        },
        "visibility": False
    },
    "crop": {
        "left": {
            "state_element": 0,
            "buf_state_element": 0,
        },
        "top": {
            "state_element": 0,
            "buf_state_element": 0,
        },
        "width": {
            "state_element": 1920,
            "buf_state_element": 1920,
        },
        "height": {
            "state_element": 1080,
            "buf_state_element": 1080,
        },
        "check_button": {
            "disabled": "yes",
        },
        "crop_button": {
            "disabled": "yes",
        },
        "visibility": False
    },
    "option": {
        "radio_button": {
            "state_element": None,
        },
        "inputs_visibility": False,
        "text_input": {
            "state_element": None,
            "visibility": True,
            "check_box_state_element": [None]
        },
        "radio_button2": {
            "state_element": None,
            "visibility": True,
            "check_box_state_element": [None]
        },
        "multiselect": {
            "options": _get_select(),
            "state_element": None
        },
        "visibility": False
    },
    "collect": {
        "start_button": {
            "disabled": "no",
            "visibility": False if rel else True
        },
        "stop_button": {
            "disabled": "yes",
            "visibility": False if rel else True
        },
        "repeater": {
            "message0": {
                "id": 0,
                "text": "Not started",
                "visibility": False,
                "repeater": {
                    "images0": {
                        "start_html": {
                            "image_source": "static/image0_0.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image0_0.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    },
                    "images1": {
                        "start_html": {
                            "image_source": "static/image0_0_crop.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image0_0_crop.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    },
                    "images2": {
                        "start_html": {
                            "image_source": "static/image0_0_crop_3rect.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image0_0_crop_3rect.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    }
                }
            },
            "message1": {
                "id": 1,
                "text": "Not started",
                "visibility": False,
                "repeater": {
                    "images0": {
                        "start_html": {
                            "image_source": "static/image1_0.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image1_0.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    },
                    "images1": {
                        "start_html": {
                            "image_source": "static/image1_0_crop.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image1_0_crop.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    },
                    "images2": {
                        "start_html": {
                            "image_source": "static/image1_0_crop_3rect.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image1_0_crop_3rect.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    }
                }
            },
            "message2": {
                "id": 2,
                "text": "Not started",
                "visibility": False,
                "repeater": {
                    "images0": {
                        "start_html": {
                            "image_source": "static/image2_0.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image2_0.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    },
                    "images1": {
                        "start_html": {
                            "image_source": "static/image2_0_crop.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image2_0_crop.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    },
                    "images2": {
                        "start_html": {
                            "image_source": "static/image2_0_crop_3rect.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image2_0_crop_3rect.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    }
                }
            },
            "message3": {
                "id": 3,
                "text": "Not started",
                "visibility": False,
                "repeater": {
                    "images0": {
                        "start_html": {
                            "image_source": "static/image3_0.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image3_0.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    },
                    "images1": {
                        "start_html": {
                            "image_source": "static/image3_0_crop.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image3_0_crop.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    },
                    "images2": {
                        "start_html": {
                            "image_source": "static/image3_0_crop_3rect.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image3_0_crop_3rect.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    }
                }
            },
            "visibility": False
        },
        "visibility": False if rel else True
    }
}

initial_state = ss.init_state(state_dict)

def _start():
    # 任意のブラウザで開いてもpythonの実行を止めない https://qiita.com/benisho_ga/items/4844920a002f9d07c9c1
    browser = webbrowser.get('"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" %s &')
    browser.open("http://localhost:20000")

def _init_state(state=None):
    file_list = _glob(_join(_dirname('__file__'),'static/image*.jpg'))
    for file in file_list: _remove(file)
    if state!=None:
        print(state.user_state)
        #state.user_state = state_dict
        state.user_state.ingest(state_dict)
        print(state.user_state)
    
_init_state()
#_start()

print(initial_state["inputs"])

