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
from module.esports_analysis import get_charalists as _get_charalists
from module.bq_db import SmashDatabase
from module.yt_obj import GetYoutube

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
        state["option"]["radio_button"]["visibility"] = True
    
def check_crop(state, payload):
    if type(payload)==float:
        _update_cropper(state)
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
        state["option"]["visibility"] = True
        state["game_screen"]["visibility"] = False
        if state["inputs"]["crop"]==None: state["inputs"]["crop"]="None"
    else:
        _init_state(state)
    _update_option(state)

## 対戦している2キャラとその勝敗結果を取得し、それらに応じて対戦開始画面に飛べるURLをbigqueryに保存する
def collect(state):
    #charalists = _get_charalists(state["inputs"]["chara_df"])
    pass

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
            state["crop"]["check_button"]["disabled"] = "no"
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
        state["start_button"]["visibility"] = False
        state["stop_button"]["visibility"] = False
    else:
        state["start_button"]["visibility"] = True
        state["stop_button"]["visibility"] = True

# STATE INIT

rel = True

if not rel:
    yti0 = {
        'title': '【スマブラSP】VIP→トレモ', 
        'duration': 5496, 'channel': 'Neo', 'release_timestamp': 1630295308, 'original_url': 'https://www.youtube.com/watch?v=9wFfGMbNuIg', 'fps': 60, 
        'cap': 'https://rr5---sn-oguelnsr.googlevideo.com/videoplayback?expire=1712083324&ei=HP0LZqWYBOzr2roP_Pe0sAY&ip=106.73.16.65&id=o-AB-392f_drUAAqdqYV3T_Gdz7w-9qnVKhD_9_GCRvTRv&itag=298&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=qd&mm=31%2C29&mn=sn-oguelnsr%2Csn-oguesn6r&ms=au%2Crdu&mv=m&mvi=5&pl=16&initcwndbps=846250&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=1898594811&dur=5496.233&lmt=1674517743193918&mt=1712061202&fvip=4&keepalive=yes&fexp=51141541&c=IOS&txp=7216224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRgIhAJsAKyuiOUpqyIG-LXVC6iMnjYIPdANrgUMUVj8VyQlaAiEA4-ctl788BHcEhCAWyahFC7MKcPULsKktS7Xf4wzryTw%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRgIhALW0VGBZv8qNO4zZHTS26wvEN4hXFuumh5UCVd3DTYlIAiEAzSLyJu_c65j75IPyL9MEM7ZxUZsWZyTBNV405rNHULM%3D'
    }
    yti1 = {
        'title': '【スマブラSP】VIP 連勝\u3000負けたら辞める', 
        'duration': 3665, 'channel': 'Neo', 'release_timestamp': 1630548488, 'original_url': 'https://www.youtube.com/watch?v=xU1BLJ9gZ7I', 'fps': 60, 
        'cap': 'https://rr3---sn-oguesndl.googlevideo.com/videoplayback?expire=1712083326&ei=Hv0LZrSmEeuF2roP8I2c2Ao&ip=106.73.16.65&id=o-AJU0BRpcOCkVFgBSu1gFF5JbIknCsC_KyhzWOhPlbKfl&itag=298&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=ic&mm=31%2C29&mn=sn-oguesndl%2Csn-oguelnz7&ms=au%2Crdu&mv=m&mvi=3&pl=16&initcwndbps=923750&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=1367839480&dur=3664.433&lmt=1671856597725800&mt=1712061202&fvip=4&keepalive=yes&fexp=51141541&c=IOS&txp=7216224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRQIhAKL0YeIGTCB41ruVBR_T63B5ES6sXJWMLec_qAhEUxv9AiAU9bsrta9OWYElUI4CfdIwwM4CnXdMoMCqsUtloxUEyQ%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRAIgJDHcI7EGbJSa1R1w8YLEwwaWBwztd9SWPaE1K3IK1M0CIB8a1sNhK3p_tfVbRHwehjuAPjhOXBD1ngPZZvT8HTIA'
    }
    yti2 = {
        'title': '【スマブラSP】すまめいと', 
        'duration': 5458, 'channel': 'Neo', 'release_timestamp': 1631176068, 'original_url': 'https://www.youtube.com/watch?v=cdTxb0a0jrA', 'fps': 60, 
        'cap': 'https://rr2---sn-ogul7n7z.googlevideo.com/videoplayback?expire=1712083328&ei=IP0LZouhE5yF0-kPjZWA4QE&ip=106.73.16.65&id=o-AEIdxzSYOmtrLkGdJq0H44dZFhH_ThcmwcFjrbMSffNa&itag=298&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=zE&mm=31%2C29&mn=sn-ogul7n7z%2Csn-oguelnsl&ms=au%2Crdu&mv=m&mvi=2&pl=16&initcwndbps=923750&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=1889958743&dur=5457.716&lmt=1631225593097688&mt=1712061202&fvip=1&keepalive=yes&fexp=51141541&c=IOS&txp=7216222&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRgIhAKD5IJBSHNH6k0niQ9JxQ-cS0y69hl_sIqXM78Z9ImS7AiEA9-M1Cbfxu-TDx7zFG5ZZmPpIJ7J7HwAr0wwAW-BCIeE%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRQIgdtaRAGaZK6j0HBpSUCYB0at4-op84s_x6qVgSlAosmECIQCmMRlY5eQa22S98BjePcya6yF32yRR2ZTkZO8yC00Jcg%3D%3D'
    }
    yti3 = {'title': '【スマブラSP】すまめいと→vip', 
            'duration': 6677, 'channel': 'Neo', 'release_timestamp': 1633075410, 'original_url': 'https://www.youtube.com/watch?v=RAtI3Hl4weU', 'fps': 60, 
            'cap': 'https://rr5---sn-oguelnzl.googlevideo.com/videoplayback?expire=1712083330&ei=Iv0LZtn-Hpu12roP7_ql6Aw&ip=106.73.16.65&id=o-AFF3hMzc2FafMHM3ZfMXyzJkNMvMYipOROWQ2jq9nabA&itag=298&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=RF&mm=31%2C26&mn=sn-oguelnzl%2Csn-npoe7nds&ms=au%2Conr&mv=m&mvi=5&pl=16&initcwndbps=846250&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=2279255606&dur=6677.232&lmt=1686068743330652&mt=1712061202&fvip=4&keepalive=yes&fexp=51141541&c=IOS&txp=7216224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRQIgNxAZCVpP6bb5HZtWpOBzWH64i2A1TYJr11p-5YS3XJACIQChP3r7WNB736PqtX7W5qvFWk4SM90OBszH0NsGFnT59A%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRgIhAKeJARs6jXIKC4rqhvY8tzp5ApCjUq6HSLUqeWTlk9WmAiEAlNsLxgYRoIZeVDgDr54S2P3rdPUtoG32hhnUEk01o44%3D'
    }
    yti4 = {'title': '【スマブラSP】カムイメイト', 
            'duration': 7955, 'channel': 'Neo', 'release_timestamp': 1654925784, 'original_url': 'https://www.youtube.com/watch?v=pRmmyRNcQk0', 'fps': 60, 
            'cap': 'https://rr4---sn-oguelnsy.googlevideo.com/videoplayback?expire=1712083332&ei=JP0LZom5GPjM2roPovyy0Ao&ip=106.73.16.65&id=o-AB4ohTaG48wEXwibot_hSOgy_WgMZE9USYb38lgjAK0T&itag=298&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=-e&mm=31%2C26&mn=sn-oguelnsy%2Csn-npoe7nl6&ms=au%2Conr&mv=m&mvi=4&pl=16&initcwndbps=923750&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=2485924475&dur=7955.150&lmt=1680509445822434&mt=1712061202&fvip=2&keepalive=yes&fexp=51141541&c=IOS&txp=7219224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRQIhAL2u4o1Jrw8LWKHK80anM6wvs6NqRjpQP7dNpkBjHHOvAiB93vWij6FqjG0jn9rPriGossY26ZI5pT8RxhK6_bSKzw%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRQIgMCCU2I-mEl-zDo98Y0wZvt9umxNzRd3as-r8Fh6V_zoCIQDSNbx7i3amzRcTPNHexJuG8lp-uacuhJIrxPgNmQpnNA%3D%3D'
    }

state_dict = {
    "sub_yt_num": 4,
    "inputs": {
        "target_player_name": None if rel else 'auto',
        "target_category": None if rel else 'auto',
        "target_1p_charas": None if rel else ['KAMUI'],
        "chara_df": _get_main_df(),
        "yt_infos": None if rel else [yti0, yti1, yti2, yti3, yti4],
        "crop": None if rel else {'crop': {'pt1': [0, 0], 'pt2': [1585, 891]}}
    },
    "yt_url": {
        "text_input": {
            "place_holder": "https://www.youtube.com/watch?v=My3gyDHoGAs",
            "state_element": None if rel else "https://www.youtube.com/playlist?list=PLxWXI3TDg12zJpAiXauddH_Mn8O9fUhWf",
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
            "visibility": False
        },
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
            }
        }
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

