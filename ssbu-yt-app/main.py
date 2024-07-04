import gc
import re
import writer as wf
import threading
import time
from dataclasses import astuple
from glob import glob as _glob
from os.path import dirname as _dirname
from os.path import join as _join
from os import remove as _remove
from pprint import pprint as _pprint
from sys import path
path.append(_join(_dirname('__file__'), '..'))
from threading import Thread
from tqdm import tqdm
from module.esports_analysis import EsportsAnalysis,Parameter #NewThread, get_charalists, get_templater, get_category, ssbu_each_analysis
from module.bq_db import SmashDatabase
from module.yt_obj import GetYoutube


# EVENT HANDLERS

## Input YouTube URL
def yt_url(state):
    _update_yt_url(state)
    _check_yt_url(state)

## Check game screens
def start_game_screen(state):
    _remove_img_file()
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
    state["game_screen"]["visibility"] = False
    state["option"]["html0_visibility"] = False
    _remove_img_file()
    if state["option"]["radio_button"]["state_element"]=="yes":
        state["option"]["html1_visibility"] = False
        state["option"]["inputs_visibility"] = True
        if state["inputs"]["crop"]==None: state["inputs"]["crop"]="None"
        _update_option(state)
    else:
        state["option"]["html1_visibility"] = True
        state["option"]["inputs_visibility"] = False

## 対戦している2キャラとその勝敗結果を取得し、それらに応じて対戦開始画面に飛べるURLをbigqueryに保存する
def collect(state):
    if state["collect"]["start_button"]["disabled"]=="no":
        state["collect"]["start_button"]["disabled"] = "yes"
        state["collect"]["stop_button"]["disabled"] = "no"
        state["collect"]["html_visibility"] = False
        state["option"]["visibility"] = False
        state["collect"]["repeater"] = dict()
        state["collect"]["repeater_visibility"] = True
        _remove_img_file()
        # _generate_message(state, state["collect"].to_dict()["repeater"])
        _generate_message(state)
        print(state["collect"]["repeater"])
        _generate_insert_data(state)
    if state["collect"]["stop_button"]["disabled"]=="no":
        state["collect"]["start_button"]["disabled"] = "no"
        state["collect"]["stop_button"]["disabled"] = "yes"
        state["collect"]["html_visibility"] = True
        
#### Event context https://www.streamsync.cloud/repeater.html
def view_results(state, payload, context):
    id = context["item"]['id']
    state["collect"]["repeater"][f"message{id}"]["visibility"] = True if "view" in payload else False

# LOAD / GENERATE DATA

def _get_main_df():
    return SmashDatabase().select_fighter_data()

def _get_select(state=None, main_df=None):
    select_df = main_df.sort_values('fighter_id')
    if state==None: lang_suf = ''
    else: lang_suf = '' if state["option"]["radio_button3"]["state_element"]=='jp' else '_en'
    select_df = select_df[f'fighter_name{lang_suf}']
    select_dict = select_df.to_dict()
    return {v: v for v in select_dict.values()}

def _get_main_yt(url):
    return GetYoutube(url).infos
    
def _get_game_screen(state):
    yt_infos = state["inputs"]["yt_infos"] = _get_main_yt(state["yt_url"]["text_input"]["state_element"])
    print(yt_infos)
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
    state["inputs"]["crop"] = {'crop0': {'pt1': pt1, 'pt2': pt2}}
    cv2dict = {'crop0':{'pt1':pt1, 'pt2':pt2, 'color':(255, 0, 0), 'thickness':3}}
    suffix = f'{px["left"]}_{px["top"]}_{px["width"]}_{px["height"]}'
    return cv2dict, suffix

def _get_3rect_pt():
    cv2dict = dict()
    w,h = 1920,1080
    cv2dict['name1P']  = {'pt1':(int(w*0.10), int(h*0.02)), 'pt2':(int(w*0.43), int(h*0.15)), 'color':(255, 0, 0), 'thickness':3}
    cv2dict['name2P']  = {'pt1':(int(w*0.60), int(h*0.02)), 'pt2':(int(w*0.93), int(h*0.15)), 'color':(255, 0, 0), 'thickness':3}
    cv2dict['GameSet'] = {'pt1':(int(w*0.21), int(h*0.16)), 'pt2':(int(w*0.79), int(h*0.64)), 'color':(255, 0, 0), 'thickness':3}
    suffix = "3rect"
    return cv2dict, suffix

def _generate_message(state, collect_repeater=dict()):
    for i in range(state["main_yt_num"]):
        collect_repeater.update({
            f"message{i}": {
                'id': i,
                "text": "Not started",
                "visibility": False,
                "repeater": _generate_view_results(state)
            }
        })
    state["collect"]["repeater"] = collect_repeater

def _generate_view_results(state, message_repeater=dict(), index=0, res_num=0):
    message_repeater.update({
        f"images{res_num}": {
            "start_html": {
                "image_source": f"static/image{res_num}_0.jpg",
                "inside_url": None,
                "inside_vs": None
            },
            "end_html": {
                "image_source": f"static/image{res_num}_1.jpg",
                "inside_url": None,
                "inside_res": None
            }
        }
    })
    if res_num>0: state["collect"]["repeater"][f"message{index}"]["repeater"] = message_repeater
    return message_repeater

# 【Python】threadingによるマルチスレッド処理の基本 | 入れ子のロック取得 RLock 
# https://tech.nkhn37.net/python-threading-multithread/#_RLock
lock = threading.RLock()
def _generate_insert_data(state):
    inputs = state["inputs"]
    category = {'VIP':['VIP'], 'smashmate':['めいと', 'メイト','レート', 'レーティング']}
    dsize = [(1024,576), (448*2,252*2), (448,252), (1280,720)]
    img = {
        "g_start": {
            "img": None,
            "temp_img": None,
            "temp_match_val": -1,
            "dsize": dsize[0],
            "crop": {"crop1": {'pt1': [0,0], 'pt2': [dsize[0][0],int(dsize[0][1]*0.2)]}}
        },
        "g_fighter": {
            "img_1p": None,
            "img_2p": None,
            "dsize": dsize[1],
            "crop_1p": {"crop1": {'pt1': [int(dsize[1][0]*0.10),int(dsize[1][1]*0.02)], 'pt2': [int(dsize[1][0]*0.43),int(dsize[1][1]*0.13)]}},
            "crop_2p": {"crop1": {'pt1':[int(dsize[1][0]*0.60),int(dsize[1][1]*0.02)], 'pt2':[int(dsize[1][0]*0.93),int(dsize[1][1]*0.13)]}}
        },
        "g_finish": {
            "img": None,
            "temp_img": "gameset.png",
            "temp_match_val": 0.474,
            "dsize": dsize[2],
            "crop": {"crop1": {'pt1':[int(dsize[2][0]*0.21),int(dsize[2][1]*0.16)], 'pt2':[int(dsize[2][0]*0.79),int(dsize[2][1]*0.64)]}}
        },
        "g_result": {
            "img_1p": None,
            "img_2p": None,
            "img_rs": None,
            "dsize": dsize[3],
            "crop_1p": {"crop1": {'pt1':[int(dsize[3][0]*0.266),int(dsize[3][1]*0.847)], 'pt2':[int(dsize[3][0]*0.343),int(dsize[3][1]*0.927)]}},
            "crop_2p": {"crop1": {'pt1':[int(dsize[3][0]*0.651),int(dsize[3][1]*0.847)], 'pt2':[int(dsize[3][0]*0.728),int(dsize[3][1]*0.927)]}},
            "crop_rs": {"crop1": {'pt1':[int(dsize[3][0]*0.000),int(dsize[3][1]*0.600)], 'pt2':[int(dsize[3][0]*0.500),int(dsize[3][1]*1.000)]}}
        },
        "imw_path": _dirname('__file__')
    }
    #  動画毎に並行(並列)処理
    fighter_df = inputs["fighter_df"]
    inputs_dict = inputs.to_dict()
    inputs_dict["fighter_df"] = fighter_df
    
    # ini_dur_dict = {
    #     # "EJdt-sWDhMU": [2333, 15800], 9
    #     "3h94qbZLS7E": [12504, 12620], 39 OK
    #     # "3h94qbZLS7E": [12654, 12716], 39 
    #     # "AEsMop2CT6U": [560, 5090], 23
    #     # "GPvZuZCVMmc": [1847, 2530], 34 OK
    #     "d7Kq6YuNiwY": [2146, 2349], 20
    #     "F1pFuBy0WEI": [11112, 11263], 33 OK 
    #     "3F0t_gQ0TqA": [14138, 14233], 51 OK
    #     # "87jIYtfEIPQ": [5928, 6222], 21
    #       "UFmLvDP-ICw": [0,0] 38 OK
    # }
    
    # ini_dur_dict = {
    #     "HCqSYGQRRXo": [4719, 4800],
    #     "FyQtFT2X1Jg": [13707, 14051]
    # }
    
    tasks = []
    for i in range(state["main_yt_num"]):
        # for k in ini_dur_dict.keys():
        #     if k in state["inputs"]["yt_infos"][i]['original_url']:
        #         initial = ini_dur_dict[k][0]-30
        #         duration = ini_dur_dict[k][1]+5
        # task = Thread(target=_generate_analysis_data, args=(state, inputs_dict, i, initial, duration))
        # task = Thread(target=_generate_analysis_data, args=(state, inputs_dict, i), kwargs=dict(initial=1))
        # task = Thread(target=_generate_analysis_data, args=(state, inputs_dict, i), kwargs=dict(initial=100))
        task = Thread(target=_generate_analysis_data, args=(state, inputs_dict, i,))
        # task = Thread(target=_generate_analysis_data, args=(state, i, EsportsAnalysis(i, param, initial-30, duration),))
        # task = Thread(target=_generate_yt_image, args=(state, i, EsportsAnalysis(i, param, 1),))
        # task = Thread(target=_generate_analysis_data, args=(state, i, EsportsAnalysis(i, param, 1),))
        # task = Thread(target=_generate_analysis_data, args=(state, i, EsportsAnalysis(i, param),))
        task.start()
        tasks.append(task)
    for t in tasks:
        t.join()
    state["collect"]["stop_button"]["disabled"] = "yes"
    state["collect"]["html_visibility"] = True

# def _generate_analysis_data(state, index, analysis:EsportsAnalysis):
def _generate_analysis_data(state, inputs, index, initial=0, duration=0):
    print(_dirname('__file__'))
    analysis = EsportsAnalysis(Parameter(inputs, index, initial, duration, imw_path=_dirname('__file__')), )
    bar = tqdm(total=analysis.param.duration, leave=False, disable=False, initial=analysis.param.initial)
    game_data_list = []
    analysis.set_game_data(inputs, index)
    yt_id = analysis.param.yt_info['original_url'].split('=')[1]
    for sec in range(analysis.param.initial, analysis.param.duration):
    # for sec in range(660, 905):
        if state["collect"]["stop_button"]["disabled"]=="yes":
            state["collect"]["repeater"][f"message{index}"]["text"] = f"!Stopped{text[7:]}"
            break
        # lock_state = False
        # if analysis.states['find_game_start']:
        #     lock_state = lock.acquire()
        #     print(f"lock_state = {lock_state}")
        analysis.execute_analysis(index, sec)
        # if lock_state: lock.release()
        bar_text = f"Started image processing | {yt_id} -> {analysis.state}"
        bar.set_description(bar_text)
        bar.update(1)
        text = f"%{bar_text}: {int((sec+1)/analysis.param.duration*100)}% ({sec+1}/{analysis.param.duration} sec)"
        state["collect"]["repeater"][f"message{index}"]["text"] = text
        if ((analysis.game_data.fighter_name_1p in analysis.param.target_1p_fighters and analysis.game_data.fighter_id_2p>0) or 
            (analysis.game_data.fighter_name_1p_en in analysis.param.target_1p_fighters and analysis.game_data.fighter_id_2p>0) or 
            (analysis.game_data.fighter_id_1p>0 and analysis.game_data.fighter_name_2p in analysis.param.target_1p_fighters) or
            (analysis.game_data.fighter_id_1p>0 and analysis.game_data.fighter_name_2p_en in analysis.param.target_1p_fighters)):
            inside_url = analysis.game_data.game_start_url
            inside_vs = f"{analysis.game_data.fighter_name_1p} vs {analysis.game_data.fighter_name_2p}"
            image_source = f"static/image{index}_{yt_id}_{sec}_{re.sub('[.&/ -]', '', inside_vs)}.jpg"
            if state["collect"]["repeater"][f"message{index}"]["repeater"][f"images{len(game_data_list)}"]["start_html"]["image_source"]==f"static/image{len(game_data_list)}_0.jpg":
                state["collect"]["repeater"][f"message{index}"]["repeater"][f"images{len(game_data_list)}"]["start_html"]["image_source"] = image_source
            if state["collect"]["repeater"][f"message{index}"]["repeater"][f"images{len(game_data_list)}"]["start_html"]["inside_url"]==None:
                state["collect"]["repeater"][f"message{index}"]["repeater"][f"images{len(game_data_list)}"]["start_html"]["inside_url"] = inside_url
            if state["collect"]["repeater"][f"message{index}"]["repeater"][f"images{len(game_data_list)}"]["start_html"]["inside_vs"]==None:
                print(f'state["collect"]["repeater"][f"message{index}"]["repeater"] = {state["collect"]["repeater"][f"message{index}"]["repeater"]}')
                state["collect"]["repeater"][f"message{index}"]["repeater"][f"images{len(game_data_list)}"]["start_html"]["inside_vs"] = inside_vs
            if analysis.game_data.target_player_is_win!=None:
                inside_url = analysis.game_data.game_finish_url
                inside_res = "WIN" if analysis.game_data.target_player_is_win else "LOSE"
                image_source = f"static/image{index}_{yt_id}_{analysis.sec_buf}_{inside_res}.jpg"
                state["collect"]["repeater"][f"message{index}"]["repeater"][f"images{len(game_data_list)}"]["end_html"]["image_source"] = image_source
                state["collect"]["repeater"][f"message{index}"]["repeater"][f"images{len(game_data_list)}"]["end_html"]["inside_url"] = inside_url
                state["collect"]["repeater"][f"message{index}"]["repeater"][f"images{len(game_data_list)}"]["end_html"]["inside_res"] = inside_res
                print(f'state["collect"]["repeater"][f"message{index}"]["repeater"]= {state["collect"]["repeater"][f"message{index}"]["repeater"]}')
                game_data_list.append(analysis.game_data)
                analysis.set_game_data(inputs, index)
                _generate_view_results(state, state["collect"].to_dict()["repeater"][f"message{index}"]["repeater"], index, len(game_data_list))
    
    time.sleep(0.1*(1+index))
    smash_db = SmashDatabase()
    data_id = len(smash_db.select_analysis_data()) + 1
    # print(f"game_data_list (before) = {game_data_list}")
    for i in range(len(game_data_list)): game_data_list[i].id = data_id+i
    # print(f"game_data_list (after) = {game_data_list}")
    # print([astuple(data) for data in game_data_list])
    # データクラスと辞書型の相互変換: asdict()とastuple()関数の使い方 https://ya6mablog.com/how-to-use-dataclass/#index_id8
    smash_db.insert_analysis_data([astuple(data) for data in game_data_list])
    if "Stopped" not in state["collect"]["repeater"][f"message{index}"]["text"]:
        state["collect"]["repeater"][f"message{index}"]["text"] = f"+Finished{text[7:]}"
        
    # 【Python】オブジェクトを削除してメモリを解放する https://yumarublog.com/python/del/
    del analysis
    gc.collect()
        
def _generate_yt_image(state, index, analysis:EsportsAnalysis):
    bar = tqdm(total=analysis.yt_info['duration'], leave=False, disable=False, initial=analysis.initial)
    for sec in range(analysis.initial, analysis.yt_info['duration']):
        if state["collect"]["stop_button"]["disabled"]=="yes":
            state["collect"]["repeater"][f"message{index}"]["text"] = f"!Stopped"
            break
        analysis.test_get_yt_image(index, sec)
        bar.update(1)


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
    cv2dict, suffix = _get_crop_pt(state) if var_rect else _get_3rect_pt()
    if crop==True: suffix = "crop"
    ch_range = range(state["sub_yt_num"]) if ch==4 else range(ch,ch+1)
    for i in ch_range:
        sec = int(state["game_screen"][f"html{i}"]["slider_number"]["state_element"])
        imr_file = f'static/image{i}_{sec}.jpg' if var_rect else state["game_screen"][f"html{i}"]["image_source"]
        imw_file = f'static/image{i}_{sec}_{suffix}.jpg' if var_rect else f'{state["game_screen"][f"html{i}"]["image_source"][:-4]}_{suffix}.jpg'
        GetYoutube.set_yt_image(
            cv2dict, rect=rect, crop=crop, post_dsize=(1920,1080),
            imr_path=_join(_dirname('__file__'), imr_file),
            imw_path=_join(_dirname('__file__'), imw_file),
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
    ## Select a language of fighter names
    state["inputs"]["target_lang"] = state["option"]["radio_button3"]["state_element"]
    ## Select fighters player use
    state["option"]["multiselect"]["options"] = _get_select(state, state["inputs"]["fighter_df"])
    if None not in state["option"]["multiselect"]["state_element"]:
        state["inputs"]["target_1p_fighters"] = state["option"]["multiselect"]["state_element"]
    inputs = [input for input in state["inputs"].to_dict().values()]
    if '' in inputs or None in inputs:
        state["collect"]["visibility"] = False
    else:
        state["collect"]["visibility"] = True


# STATE INIT

rel = True
full_gs = True
jp = True

if not rel:
    if full_gs:
        target_1p_fighters = ['KAMUI'] if jp else ['CORRIN']
        playlist_id = "PLxWXI3TDg12zrFRN6cl_z5qCHF-VTbhdZ" if jp else "PLxWXI3TDg12wt42UpVkbz4WyJp17SNrDl"
        # yt_infos = _get_main_yt("https://www.youtube.com/playlist?list=PLxWXI3TDg12wDTFFBiYvWBdkjrn9OPsCY")
        yt_infos = _get_main_yt(f"https://www.youtube.com/playlist?list={playlist_id}")
        # yt_infos = _get_main_yt("https://www.youtube.com/watch?v=MlPDNrRCv5M") # 英語テスト
        if jp:
            yt_infos = [info for info in yt_infos for yt_id in [ # https://www.youtube.com/playlist?list=PLxWXI3TDg12zrFRN6cl_z5qCHF-VTbhdZ
            # "EJdt-sWDhMU",
            "3h94qbZLS7E",
            # "AEsMop2CT6U",
            "GPvZuZCVMmc",
            # "d7Kq6YuNiwY",
            "F1pFuBy0WEI",
            "3F0t_gQ0TqA",
            # "87jIYtfEIPQ"
        ] if yt_id in info['original_url']]
        crop = {'crop0': {'pt1': [0,0], 'pt2': [1920,1080]}}
        target_lang = 'jp' if jp else 'en'
    else:
        target_1p_fighters = ['KAMUI']
        # yt_infos = _get_main_yt("https://www.youtube.com/playlist?list=PLxWXI3TDg12ynGyOqMitigy6a8JgkyYwY")
        # yt_infos = _get_main_yt("https://www.youtube.com/watch?v=mIzS8ek44v8")
        crop = {'crop0': {'pt1': [0, 0], 'pt2': [1585, 891]}}
        target_lang = 'jp'
        # target_lang = 'en'

state_dict = {
    "main_yt_num": 10 if rel else len(yt_infos),
    "sub_yt_num": 4,
    "inputs": {
        "target_player_name": None if rel else 'auto',
        "target_category": None if rel else 'auto',
        "target_1p_fighters": None if rel else target_1p_fighters,
        "target_lang": None if rel else target_lang,
        "fighter_df": _get_main_df(),
        "yt_infos": None if rel else yt_infos,
        "crop": {'crop0': {'pt1': [0,0], 'pt2': [1920,1080]}} if rel else crop
    },
    "yt_url": {
        "text_input": {
            "place_holder": "https://www.youtube.com/watch?v=My3gyDHoGAs",
            "state_element": [None],
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
        "html0_visibility": True,
        "html1_visibility": False,
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
        "radio_button3": {
            "state_element": None
        },
        "multiselect": {
            "options": _get_select(state=None,main_df=_get_main_df()),
            "state_element": [None]
        },
        "visibility": False
    },
    "collect": {
        "start_button": {
            "disabled": "no",
        },
        "stop_button": {
            "disabled": "yes",
        },
        "html_visibility": False,
        "repeater": dict(),
        "repeater_visibility": False,
        "visibility": False if rel else True
    }
}

initial_state = wf.init_state(state_dict)

# _pprint(state_dict)
# print("-"*20)
print(state_dict)

def _remove_img_file():
    file_list = _glob(_join(_dirname('__file__'),'static/image*.jpg'))
    for file in file_list: _remove(file)
    
def _init_app(state=None):
    _remove_img_file()
    if state!=None:
        print(state_dict)
        # state["page"]["visibility"] = False
        # state.open_url("http://127.0.0.1:382/")
        # state.set_page("top")
        # state.user_state.state = {}
        # state.user_state.ingest(state_dict)
        # wf.init_state(state_dict)
    # initial_state.user_state.ingest(state_dict)
    
_init_app()