import pandas as pd
import streamsync as ss
import re
import sys
from os.path import join as _join
from os.path import dirname as _dirname
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

def game_screen(state):
    print(state["main_yt"])
    if len(state["main_yt"])==0: _get_game_screen(state)
    else: _update_game_screen(state)
    
# LOAD / GENERATE DATA

def _get_main_df():
    return SmashDatabase('ssbu_dataset').select_chara_data()

def _get_main_yt(url="https://www.youtube.com/watch?v=hFDOOCutwmk", ydl_opts={'verbose':True, 'format':'best'}):
    return GetYoutube(url, ydl_opts=ydl_opts).infos
    #return Test('ogre')
    
def _get_game_screen(state):
    state["yt_url"]["button"]["disabled"]="yes"
    if state["yt_url"]["radio_button"]["state_element"]!=None: 
        state["ydl_ops"]['cookiesfrombrowser'] = (state["yt_url"]["radio_button"]["state_element"],)
    yt = state["main_yt"] = _get_main_yt(state["yt_url"]["text_input"]["state_element"], ydl_opts=state["ydl_ops"])
    img_num = len(yt) if len(yt)<=4 else 4
    for i in range(img_num):
        GetYoutube.get_yt_image(yt[i], ydl_opts=state["ydl_ops"], sec_pos=0, imw_path=_join(_dirname('__file__'), f'static/image{i}.jpg'))
        state["game_screen"][f"html{i}"]["image_source"] = f'static/image{i}.jpg'
        state["game_screen"][f"html{i}"]["inside"] = yt[i]["original_url"]
        state["game_screen"][f"html{i}"]["slider_number"]["maximum_value"] = yt[i]["duration"]
        state["game_screen"][f"html{i}"]["visibility"] = True
    print(state["main_yt"])
    
# UPDATES

def _update_yt_url(state):
    print(state["yt_url"]["check_box"]["state_element"])
    playlist = "https://www.youtube.com/playlist?list=PLxWXI3TDg12zJpAiXauddH_Mn8O9fUhWf"
    watch = "https://www.youtube.com/watch?v=My3gyDHoGAs"
    state["yt_url"]["text_input"]["place_holder"] = playlist if "playlist" in state["yt_url"]["check_box"]["state_element"] else watch
    state["yt_url"]["radio_button"]["visibility"] = True if "members-only" in state["yt_url"]["check_box"]["state_element"] else False

def _check_yt_url(state):
    if len(state["yt_url"]["text_input"]["place_holder"])==len(state["yt_url"]["text_input"]["state_element"]):
        state["yt_url"]["button"]["visibility"] = True
        state["yt_url"]["text"]["visibility"] = False
    else: 
        state["yt_url"]["button"]["visibility"] = False
        state["yt_url"]["text"]["visibility"] = True
        
def _update_game_screen(state):
    state["game_screen"]["button"]["disabled"] = "yes"
    print(type(state["game_screen"]))
    #game_screen = state["game_screen"].to_dict()
    #print(game_screen)
    yt = state["main_yt"]
    screen = state["game_screen"]
    for i in range(len(yt)):
        if screen[f"html{i}"]["slider_number"]["state_element"]!=screen[f"html{i}"]["slider_number"]["buf_state_element"]:
            state["game_screen"][f"html{i}"]["slider_number"]["buf_state_element"] = screen[f"html{i}"]["slider_number"]["state_element"]
            sec = int(screen[f"html{i}"]["slider_number"]["state_element"])
            index = i
            break
    print(yt[index])
    print(state["ydl_opts"])
    print(sec)
    print(_join(_dirname('__file__'), f'static/image{index}.jpg'))
    GetYoutube.get_yt_image(yt[index], ydl_opts=state["ydl_opts"], sec_pos=sec, imw_path=_join(_dirname('__file__'), f'static/image{index}_{sec}.jpg'))
    state["game_screen"][f"html{index}"]["image_source"] = f'static/image{index}_{sec}.jpg'
    state["game_screen"][f"html{index}"]["inside"] = f'{yt[index]["original_url"]}+&t={sec}s'
    state["game_screen"]["button"]["disabled"] = "no"

# STATE INIT

initial_state = ss.init_state({
    "main_df": _get_main_df(),
    "main_yt": [], #_get_main_yt(),
    "ydl_opts": {
        'verbose':True,
        'format':'best'
    },
    "yt_url": {
        "text_input": {
            "place_holder": "https://www.youtube.com/watch?v=My3gyDHoGAs",
            "state_element": [None]
        },
        "check_box": {
            "state_element": [None]
        },
        "radio_button": {
            "state_element":None,
            "visibility": False
        },
        "text": {
            "visibility": False
        },
        "button": {
            "disabled": "no",
            "visibility": False
        }
    },
    "game_screen": {
        "html0": {
            "image_source": None,
            "slider_number": {
                "maximum_value": 25252,
                "state_element": 0,
                "buf_state_element": 0
            },
            "inside": "url",
            "visibility": True
        },
        "html1": {
            "slider_number": {
                "maximum_value": 25252,
                "state_element": 0,
                "buf_state_element": 0
            },
            "inside": "url",
            "visibility": True
        },
        "html2": {
            "slider_number": {
                "maximum_value": 25252,
                "state_element": 0,
                "buf_state_element": 0
            },
            "inside": "url",
            "visibility": True
        },
        "html3": {
            "slider_number": {
                "maximum_value": 25252,
                "state_element": 0,
                "buf_state_element": 0
            },
            "inside": "url",
            "visibility": True
        },
        "button": {
            "disabled": "no"
        }
        # "repeater": {
        #     "object": {
        #         "image0": {
        #             "source": "static/image0.jpg",
        #             "caption": None
        #         },
        #         "image1": {
        #             "source": "static/image1.jpg",
        #             "caption": None
        #         },
        #         "image2": {
        #             "source": "static/image2.jpg",
        #             "caption": None
        #         },
        #         "image3": {
        #             "source": "static/image3.jpg",
        #             "caption": None
        #         }
        #     },
        #     "visibility": True, #False,
        # }        
    },
    "articles": {
        "Banana": {
            "type": "fruit",
            "color": "yellow"
        },
        "Lettuce": {
            "type": "vegetable",
            "color": "green"
        },
        "Spinach": {
            "type": "vegetable",
            "color": "green"
        }
    },
})

print(initial_state["main_df"])
print(initial_state["main_yt"])