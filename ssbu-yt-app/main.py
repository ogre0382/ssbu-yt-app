import gc
import re
import writer as wf
import time
from dataclasses import astuple
from glob import glob as _glob
from os.path import dirname as _dirname
from os.path import join as _join
from os import remove as _remove
from sys import path
path.append(_join(_dirname('__file__'), '..'))
from threading import Thread
from tqdm import tqdm
from module.esports_analysis import EsportsAnalysis,Parameter
from module.bq_db import SmashDatabase
from module.yt_obj import GetYoutube


# EVENT HANDLERS

## Input YouTube URL：YouTube URLを更新し、検証する
def yt_url(state):
    _update_yt_url(state)
    _check_yt_url(state)

## Check game screens：ゲーム画面を確認する
def start_game_screen(state):
    _remove_img_file()
    state["yt_url"]["visibility"] = False
    state["game_screen"]["visibility"] = True
    state["game_screen"]["message"]["visibility"] = True
    _get_game_screen(state)
    state["game_screen"]["message"]["visibility"] = False
    state["game_screen"]["radio_button"]["visibility"] = True

## Check game screens：ゲーム画面を変更する
def change_game_screen(state, payload):
    if type(payload)==float:
        state["game_screen"]["radio_button"]["visibility"] = False
        _update_game_screen_secnum(state)
    else: 
        for i in range(state["sub_yt_num"]): state["game_screen"][f"html{i}"]["slider_number"]["visibility"] = False
        _update_game_screen(state)
        state["game_screen"]["radio_button"]["visibility"] = True

## Check game screens：ゲーム画面をクロップするかどうかを選択する
def start_stop_crop_3rect(state):
    for i in range(state["sub_yt_num"]): state["game_screen"][f"html{i}"]["slider_number"]["visibility"] = False
    state["game_screen"]["radio_button"]["visibility"] = False
    if state["game_screen"]["radio_button"]["state_element"]=="no":
        state["crop"]["visibility"] = True
    else:
        _update_proc_game_screen(state, rect=True, var_rect=False)
        state["option"]["visibility"] = True

## Crop game screens：ゲーム画面をクロップする範囲を確認する
def check_crop(state, payload):
    if type(payload)==float:
        _update_cropper(state)
        state["crop"]["check_button"]["disabled"] = "no"
        state["crop"]["crop_button"]["disabled"] = "yes"
    else:
        _update_proc_game_screen(state, rect=True)
        state["crop"]["check_button"]["disabled"] = "yes"
        state["crop"]["crop_button"]["disabled"] = "no"

## Crop game screens：ゲーム画面をクロップする
def execute_crop(state):
    if state["game_screen"]["radio_button"]["state_element"]=="no":
        state["crop"]["visibility"] = False
        for i in range(state["sub_yt_num"]): state["game_screen"][f"html{i}"]["slider_number"]["visibility"] = True    
        state["crop"]["crop_button"]["disabled"] = "yes"
        _update_proc_game_screen(state, crop=True)
        state["game_screen"]["radio_button"]["state_element"] = None
        state["game_screen"]["radio_button"]["visibility"] = True

## Do you collect data from the following YouTube?：オプションを入力する
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

## Analyze and Collect：対戦している2キャラとその勝敗結果を取得し、対戦開始画面に飛べるURLをbigqueryに保存する
def collect(state):
    if state["collect"]["start_button"]["disabled"]=="no":
        state["collect"]["start_button"]["disabled"] = "yes"
        state["collect"]["stop_button"]["disabled"] = "no"
        state["collect"]["html_visibility"] = False
        state["option"]["visibility"] = False
        state["collect"]["repeater"] = dict()
        state["collect"]["repeater_visibility"] = True
        _remove_img_file()
        _generate_message(state)
        _generate_insert_data(state)
    if state["collect"]["stop_button"]["disabled"]=="no":
        state["collect"]["start_button"]["disabled"] = "no"
        state["collect"]["stop_button"]["disabled"] = "yes"
        state["collect"]["html_visibility"] = True
        
## Analyze and Collect：対戦している2キャラとその勝敗結果を表示
def view_results(state, payload, context):
    # Event context https://dev.writer.com/framework/event-handlers#context
    id = context["item"]['id']
    state["collect"]["repeater"][f"message{id}"]["visibility"] = True if "view" in payload else False


# LOAD / GENERATE DATA

## 全ファイター名のデータを取得する
def _get_main_df():
    return SmashDatabase().select_fighter_data()

## 全ファイター名のマルチセレクトボックスのデータを生成取得する
def _get_select(state=None, main_df=None):
    select_df = main_df.sort_values('fighter_id')
    if state==None: lang_suf = ''
    else: lang_suf = '' if state["option"]["radio_button3"]["state_element"]=='jp' else '_en'
    select_df = select_df[f'fighter_name{lang_suf}']
    select_dict = select_df.to_dict()
    return {v: v for v in select_dict.values()}

## YouTubeの情報を取得する
def _get_main_yt(url):
    return GetYoutube(url).infos

## ゲーム画面を取得する
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

## クロップする範囲を取得する
def _get_crop_pt(state):
    px = dict()
    for k in ["left", "top", "width", "height"]: px[k] = int(state["crop"][k]["state_element"])
    pt1 = [px["left"], px["top"]]
    pt2 = [px["left"]+px["width"], px["top"]+px["height"]]
    state["inputs"]["crop"] = {'crop0': {'pt1': pt1, 'pt2': pt2}}
    cv2dict = {'crop0':{'pt1':pt1, 'pt2':pt2, 'color':(255, 0, 0), 'thickness':3}}
    suffix = f'{px["left"]}_{px["top"]}_{px["width"]}_{px["height"]}'
    return cv2dict, suffix

## 3つの矩形を表示する範囲を取得する
def _get_3rect_pt():
    cv2dict = dict()
    w,h = 1920,1080
    cv2dict['name1P']  = {'pt1':(int(w*0.10), int(h*0.02)), 'pt2':(int(w*0.43), int(h*0.15)), 'color':(255, 0, 0), 'thickness':3}
    cv2dict['name2P']  = {'pt1':(int(w*0.60), int(h*0.02)), 'pt2':(int(w*0.93), int(h*0.15)), 'color':(255, 0, 0), 'thickness':3}
    cv2dict['GameSet'] = {'pt1':(int(w*0.21), int(h*0.16)), 'pt2':(int(w*0.79), int(h*0.64)), 'color':(255, 0, 0), 'thickness':3}
    suffix = "3rect"
    return cv2dict, suffix

## 処理メッセージを生成する
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

## 処理結果のビューを生成する
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

## 動画毎に並行(並列)処理してBigqueryへ挿入するデータを生成する準備
def _generate_insert_data(state):
    inputs = state["inputs"]
    fighter_df = inputs["fighter_df"]
    inputs_dict = inputs.to_dict()
    inputs_dict["fighter_df"] = fighter_df
    tasks = []
    for i in range(state["main_yt_num"]):
        task = Thread(target=_generate_analysis_data, args=(state, inputs_dict, i,))
        task.start()
        tasks.append(task)
    for t in tasks:
        t.join()
    state["collect"]["stop_button"]["disabled"] = "yes"
    state["collect"]["html_visibility"] = True

## 動画解析した結果からデータを生成する
def _generate_analysis_data(state, inputs, index, initial=0, duration=0):
    analysis = EsportsAnalysis(Parameter(inputs, index, initial, duration, imw_path=_dirname('__file__')), )
    bar = tqdm(total=analysis.param.duration, leave=False, disable=False, initial=analysis.param.initial)
    game_data_list = []
    analysis.set_game_data(inputs, index)
    yt_id = analysis.param.yt_info['original_url'].split('=')[1]
    for sec in range(analysis.param.initial, analysis.param.duration):
        if analysis.execute_analysis(index, sec)==1:
            state["collect"]["start_button"]["disabled"] = "no"
            state["collect"]["stop_button"]["disabled"] = "yes"
            state["collect"]["html_visibility"] = True
        if state["collect"]["stop_button"]["disabled"]=="yes":
            state["collect"]["repeater"][f"message{index}"]["text"] = f"!Stopped{text[7:]}"
            break
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
                state["collect"]["repeater"][f"message{index}"]["repeater"][f"images{len(game_data_list)}"]["start_html"]["inside_vs"] = inside_vs
            if analysis.game_data.target_player_is_win!=None:
                inside_url = analysis.game_data.game_finish_url
                inside_res = "WIN" if analysis.game_data.target_player_is_win else "LOSE"
                image_source = f"static/image{index}_{yt_id}_{analysis.sec_buf}_{inside_res}.jpg"
                state["collect"]["repeater"][f"message{index}"]["repeater"][f"images{len(game_data_list)}"]["end_html"]["image_source"] = image_source
                state["collect"]["repeater"][f"message{index}"]["repeater"][f"images{len(game_data_list)}"]["end_html"]["inside_url"] = inside_url
                state["collect"]["repeater"][f"message{index}"]["repeater"][f"images{len(game_data_list)}"]["end_html"]["inside_res"] = inside_res
                game_data_list.append(analysis.game_data)
                analysis.set_game_data(inputs, index)
                _generate_view_results(state, state["collect"].to_dict()["repeater"][f"message{index}"]["repeater"], index, len(game_data_list))
    
    time.sleep(0.1*(1+index))
    smash_db = SmashDatabase()
    data_id = len(smash_db.select_analysis_data()) + 1
    for i in range(len(game_data_list)): game_data_list[i].id = data_id+i
    # データクラスと辞書型の相互変換: asdict()とastuple()関数の使い方 https://ya6mablog.com/how-to-use-dataclass/#index_id8
    smash_db.insert_analysis_data([astuple(data) for data in game_data_list])
    if "Stopped" not in state["collect"]["repeater"][f"message{index}"]["text"]:
        state["collect"]["repeater"][f"message{index}"]["text"] = f"+Finished{text[7:]}"
        
    # 【Python】オブジェクトを削除してメモリを解放する https://yumarublog.com/python/del/
    del analysis
    gc.collect()


# UPDATES

## YouTube URLのタイプを更新する
def _update_yt_url(state):
    playlist = "https://www.youtube.com/playlist?list=PLxWXI3TDg12zJpAiXauddH_Mn8O9fUhWf"
    watch = "https://www.youtube.com/watch?v=My3gyDHoGAs"
    state["yt_url"]["text_input"]["place_holder"] = playlist if "playlist" in state["yt_url"]["check_box_state_element"] else watch

## 入力されたYouTube URLを検証する
def _check_yt_url(state):
    if len(state["yt_url"]["text_input"]["place_holder"])==len(state["yt_url"]["text_input"]["state_element"]):
        state["yt_url"]["button_visibility"] = True
        state["yt_url"]["text_visibility"] = False
    else: 
        state["yt_url"]["button_visibility"] = False
        state["yt_url"]["text_visibility"] = True

## ゲーム画面のスライダー番号を更新する
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

## ゲーム画面を更新する
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

## クロップする範囲座標を更新する
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

## ゲーム画面をクロップした結果か矩形を描画した結果の表示を更新する
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

## オプションを更新する
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

## 画像ファイルを削除する
def _remove_img_file():
    for file in _glob(_join(_dirname('__file__'),'static/image*.jpg')): _remove(file)


# STATE INIT

state_dict = {
    "main_yt_num": 10,
    "sub_yt_num": 4,
    "inputs": {
        "target_player_name": None,
        "target_category": None,
        "target_1p_fighters": None,
        "target_lang": None,
        "fighter_df": _get_main_df(),
        "yt_infos": None,
        "crop": {'crop0': {'pt1': [0,0], 'pt2': [1920,1080]}}
    },
    "yt_url": {
        "text_input": {
            "place_holder": "https://www.youtube.com/watch?v=My3gyDHoGAs",
            "state_element": [None],
        },
        "check_box_state_element": [None],
        "text_visibility": False,
        "button_visibility": False,
        "visibility": True
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
        "visibility": False
    }
}

initial_state = wf.init_state(state_dict)
    
_remove_img_file()