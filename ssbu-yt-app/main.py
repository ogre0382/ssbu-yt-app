import pandas as pd
import streamsync as ss
import os
import re
import sys
sys.path.append(os.path.join(os.path.dirname('__file__'), '..'))
from module.bq_db import SmashDatabase
from module.yt_obj import GetYoutube, get_yt_image

class Test:
    def __init__(self, name):
        self.name = name

# EVENT HANDLERS

def yt_url(state):
    _update_yt_url(state)
    _check_yt_url(state)

def update_game_screen(state):
    state["game_screen"]["repeater"]["visibility"] = True
    ydl_opts = {'verbose':True, 'format':'best'}
    if state["yt_url"]["radio_button"]["state_element"]!=None: 
        ydl_opts['cookiesfrombrowser'] = (state["yt_url"]["radio_button"]["state_element"],)
    yt = state["main_yt"] = _get_main_yt(state["yt_url"]["text_input"]["state_element"], ydl_opts=ydl_opts) if len(state["main_yt"])==0 else state["main_yt"]
    # for i in range(4):
    #     state["game_screen"]["repeater"]["object"][f'image{i}']["source"] = get_yt_image(yt, ydl_opts, sindex=i, frame_pos=yt[i].fps*10)
    #     state["game_screen"]["repeater"]["object"][f'image{i}']["caption"] = f'{yt.infos[i].original_url}+&t=10s'
    # print(state["game_screen"]["repeater"]["object"])
    
# LOAD / GENERATE DATA

def _get_main_df():
    return SmashDatabase('ssbu_dataset').select_chara_data()

def _get_main_yt(url="https://www.youtube.com/watch?v=My3gyDHoGAs", ydl_opts={'verbose':True, 'format':'best'}):
    return GetYoutube(url, ydl_opts=ydl_opts).infos
    #return Test('ogre')
    
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

# STATE INIT

initial_state = ss.init_state({
    #"test": _get_test(),
    "main_df": _get_main_df(),
    "main_yt": _get_main_yt(),
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
            "visibility": False
        }
    },
    "game_screen": {
        "repeater": {
            "object": {
                "image0": {
                    "source": None,
                    "caption": None
                },
                "image1": {
                    "source": None,
                    "caption": None
                },
                "image2": {
                    "source": None,
                    "caption": None
                },
                "image3": {
                    "source": None,
                    "caption": None
                }
            },
            "visibility": True, #False,
        }        
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