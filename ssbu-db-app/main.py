import pandas as pd
import writer as wf
import os
import re
import sys
sys.path.append(os.path.join(os.path.dirname('__file__'), '..'))
from module.bq_db import SmashDatabase
from time import sleep

# EVENT HANDLERS

# 【配布用】Python スクリプトを実行ファイル化する PyInstaller を徹底解説！ https://www.cfxlog.com/python-pyinstaller/
def update(state):
    if state["input"]["lang"]["element"]!=" " and state["input"]["player"]["element"]==" ":
        state["df"] = _get_df()
        state["suf"] = "" if state["input"]["lang"]["element"]=="jp" else "_en"
        state["html"]["inside"] = _get_table(state["df"], state["suf"])
        _get_options(state, "player", 'target_player_name')
    
    if state["input"]["player"]["element"]!=" " and state["input"]["fighter"]["element"]==" ":
        state["input"]["player"]["buf_element"] = state["input"]["player"]["element"]
        state["df"] = state["df"].query(f'target_player_name == "{state["input"]["player"]["element"]}"')
        state["html"]["inside"] = _get_table(state["df"], state["suf"])
        _get_merge_options(state, "fighter")
    
    if state["input"]["fighter"]["element"]!=" " and state["input"]["vs_fighter"]["element"]==" ":
        state["input"]["fighter"]["buf_element"] = state["input"]["fighter"]["element"]
        state["df"] = state["df"].query(f'fighter_name_1p{state["suf"]} == "{state["input"]["fighter"]["element"]}" or fighter_name_2p{state["suf"]} == "{state["input"]["fighter"]["element"]}"')
        state["html"]["inside"] = _get_table(state["df"], state["suf"])
        _get_merge_options(state, "vs_fighter", False)
    
    if state["input"]["vs_fighter"]["element"]!=" " and state["input"]["category"]["element"]==" ":
        state["input"]["vs_fighter"]["buf_element"] = state["input"]["vs_fighter"]["element"]
        cond = "and" if state["input"]["fighter"]["element"]==state["input"]["vs_fighter"]["element"] else "or"
        state["df"] = state["df"].query(f'fighter_name_1p{state["suf"]} == "{state["input"]["vs_fighter"]["element"]}" {cond} fighter_name_2p{state["suf"]} == "{state["input"]["vs_fighter"]["element"]}"')
        state["html"]["inside"] = _get_table(state["df"], state["suf"])
        _get_options(state, "category", 'category')
    
    if state["input"]["category"]["element"]!=" " and state["input"]["win_lose"]["element"]==" ":
        state["input"]["category"]["buf_element"] = state["input"]["category"]["element"]
        state["df"] = state["df"].query(f'category == "{state["input"]["category"]["element"]}"')
        state["html"]["inside"] = _get_table(state["df"], state["suf"])
        _get_options(state, "win_lose", 'target_player_is_win')
    
    if state["input"]["win_lose"]["element"]!=" " and state["input"]["datetime"]["element"]==" ":
        state["input"]["win_lose"]["buf_element"] = state["input"]["win_lose"]["element"]
        state["df"] = state["df"].query(f'target_player_is_win == "{state["input"]["win_lose"]["element"]}"')
        state["html"]["inside"] = _get_table(state["df"], state["suf"])
        _get_options(state, "datetime", 'game_start_datetime')
    
    if state["input"]["datetime"]["element"]!=" " and state["input"]["correct_mode"]["element"]=="off":
        state["df"] = state["df"].query(f'game_start_datetime == "{state["input"]["datetime"]["element"]}"')
        state["html"]["inside"] = _get_table(state["df"], state["suf"])
        
        df = state["sub_df"].sort_values('fighter_id')[[f'fighter_name{state["suf"]}']]
        df = df[~df.duplicated(keep='first')]
        df2dict = df[f'fighter_name{state["suf"]}'].to_dict()
        state["input"]["vs_fighter"]["options"] = state["input"]["fighter"]["options"] = {v: v for v in df2dict.values()}
        state["input"]["category"]["options"] = {v: v for v in ["smashmate", "other", "VIP"]}
        state["input"]["win_lose"]["options"] = {v: v for v in ["Lose", "Win"]}
        _update_visibility(state, ["correct_mode"])
    
    if state["input"]["correct_mode"]["element"]=="on":
        state["input"]["correct_mode"]["visibility2"] = True
        if 'delete' in state["input"]["correct_mode"]["element2"]:
            state["input"]["correct_mode"]["disabled"] = "no"
            _update_visibility(state, ["correct_mode"])
        else:
            _update_visibility(state, ["lang", "player", "datetime"], others_off=False)
        for k in init_dict["input"].keys(): 
            if "buf_element" in init_dict["input"][k].keys():
                if state["input"][k]["element"]!=state["input"][k]["buf_element"]:
                    state["set_values_type"].append(k)
                    state["input"]["correct_mode"]["disabled"] = "no"
        print(f'state["input"]["correct_mode"]["element2"] = {state["input"]["correct_mode"]["element2"]}')
    
def correct(state):
    game_start_url = state["df"].iat[0, 11]
    if 'delete' in state["input"]["correct_mode"]["element2"]:
        SmashDatabase().delete_analysis_data((f"game_start_url = '{game_start_url}'",))
    else:
        set_values = []
        for k in state["set_values_type"]:
            if k=="player":
                element = state["input"]["player"]["element"]
                set_value = (f"target_player_name = '{element}'")
            if k=="fighter":
                y = 5 if state["suf"]=="_en" else 6
                suf2 = "" if state["suf"]=="_en" else "_en"
                element = state["input"]["fighter"]["element"]
                element2 = state["sub_df"].query(f'fighter_name{state["suf"]} == "{element}"').iat[0, 4]
                element3 = state["sub_df"].query(f'fighter_name{state["suf"]} == "{element}"').iat[0, y]
                if state["input"]["fighter"]["buf_element"]==state["df"][[f'fighter_name_1p{state["suf"]}']].iat[0, 0]:
                    set_value = (f"fighter_name_1p{state['suf']} = '{element}'")    
                    set_value2 = (f"fighter_id_1p = {element2}")
                    set_value3 = (f"fighter_name_1p{suf2} = '{element3}'")
                else:
                    set_value = (f"fighter_name_2p{state['suf']} = '{element}'")
                    set_value2 = (f"fighter_id_2p = {element2}")
                    set_value3 = (f"fighter_name_2p{suf2} = '{element3}'")
            if k=="vs_fighter":
                y = 5 if state["suf"]=="_en" else 6
                suf2 = "" if state["suf"]=="_en" else "_en"
                element = state["input"]["vs_fighter"]["element"]
                element2 = state["sub_df"].query(f'fighter_name{state["suf"]} == "{element}"').iat[0, 4]
                element3 = state["sub_df"].query(f'fighter_name{state["suf"]} == "{element}"').iat[0, y]
                if state["input"]["vs_fighter"]["buf_element"]==state["df"][[f'fighter_name_1p{state["suf"]}']].iat[0, 0]:
                    set_value = (f"fighter_name_1p{state['suf']} = '{element}'")
                    set_value2 = (f"fighter_id_1p = {element2}")
                    set_value3 = (f"fighter_name_1p{suf2} = '{element3}'")
                else:
                    set_value = (f"fighter_name_2p{state['suf']} = '{element}'")
                    set_value2 = (f"fighter_id_2p = {element2}")
                    set_value3 = (f"fighter_name_2p{suf2} = '{element3}'")
            if k=="category":
                element = state["input"]["category"]["element"]
                set_value = (f"category = '{element}'")
            if k=="win_lose":
                element = True if state["input"]["category"]["element"]=="Win" else False
                set_value = (f"target_player_is_win = {element}")
            if set_value not in set_values:
                set_values.append(set_value)
                if k in ["fighter", "vs_fighter"]:
                    set_values.append(set_value2)
                    set_values.append(set_value3)
        SmashDatabase().update_analysis_data(set_values, (f"game_start_url = '{game_start_url}'",))
    _update_visibility(state)
    state["html"]["inside"] = " "
    state["html"]["msg_visibility"] = True
    sleep(5)
    state["html"]["inside"] = _get_table(_get_df().query(f'game_start_url == "{game_start_url}"'), state["suf"])
    state["html"]["msg_visibility"] = False


# LOAD DATA

def _get_df():
    return SmashDatabase().select_analysis_data(drop=True)

def _get_table(df=_get_df(), suf=""):
    df = df[[
        'target_player_name', f'fighter_name_1p{suf}', f'fighter_name_2p{suf}',
        'category', 'target_player_is_win', 'game_start_datetime', 
        'game_start_url'
    ]]
    # pandas.DataFrame, Seriesの要素の値を置換するreplace https://note.nkmk.me/python-pandas-replace/#_6
    df = df.replace('https(.*)', r"<span class='link'><a href='https\1' target='_blank'> https\1 </a></span>", regex=True)
    # Pythonで表をHTMLに変換する https://blog.shikoan.com/python-table-html/#Style%E3%81%A7%E3%82%A4%E3%83%B3%E3%83%87%E3%83%83%E3%82%AF%E3%82%B9%E3%82%92%E9%9D%9E%E8%A1%A8%E7%A4%BA%E3%81%AB%E3%81%99%E3%82%8B
    table = df.style.hide().to_html()
    # マッチする部分を置換: sub(), subn() https://note.nkmk.me/python-re-match-search-findall-etc/#sub-subn
    table = re.sub('<table id(.*)>', r'<table id\1 border=1>', table)
    # 【CSS/html】table,th,tdの文字色を変える方法 https://csshtml.work/table-color/#spancolor
    return re.sub('</style>', '.link{color: blue;}</style>', table)

def _get_options(state, input_type, df_item):
    df = state["df"][[df_item]].sort_values(df_item)
    df = df[~df.duplicated(keep='first')]
    df2dict = df[df_item].to_dict()
    state["input"][input_type]["options"] = {v: v for v in df2dict.values()}
    _update_visibility(state, [input_type])

def _get_merge_options(state, input_type, fighter_query=True):
    df_1p = state["df"].query(f'target_player_is_1p == {fighter_query}')
    df_1p = df_1p[['fighter_id_1p', f'fighter_name_1p{state["suf"]}']]
    df_1p.columns = ['fighter_id', 'fighter_name']
    df_2p = state["df"].query(f'target_player_is_1p == {not fighter_query}')
    df_2p = df_2p[['fighter_id_2p', f'fighter_name_2p{state["suf"]}']]
    df_2p.columns = ['fighter_id', 'fighter_name']
    df = pd.concat([df_1p, df_2p], axis=0)
    df = df[['fighter_id', 'fighter_name']].sort_values('fighter_id')
    df = df[~df.duplicated(keep='first')]
    df2dict = df['fighter_name'].to_dict()
    state["input"][input_type]["options"] = {v: v for v in df2dict.values()}
    _update_visibility(state, [input_type])
    

# UPDATES

def _update_visibility(state, options_type_list=[], others_off=True):
    for k in init_dict["input"].keys(): 
        if others_off: state["input"][k]["visibility"] = True if k in options_type_list else False
        else: state["input"][k]["visibility"] = True if k not in options_type_list else False


# STATE INIT

init_dict = {
    "df": _get_df(),
    "sub_df": SmashDatabase().select_fighter_data(),
    "set_values_type": [],
    "input":{
        "lang": {
            "options": {"jp":"jp", "en":"en"},
            "element": " ",
            "visibility": True
        },
        "correct_mode": {
            "element": "off",
            "element2": [],
            "disabled": "yes",
            "visibility": False,
            "visibility2": False
        },
        "player": {
            "options": {"":""},
            "element": " ",
            "buf_element": " ",
            "visibility": False
        },
        "t_player": {
            "visibility": False
        },
        "fighter": {
            "options": {"":""},
            "element": " ",
            "buf_element": " ",
            "visibility": False
        },
        "vs_fighter": {
            "options": {"":""},
            "element": " ",
            "buf_element": " ",
            "visibility": False
        },
        "category": {
            "options": {"":""},
            "element": " ",
            "buf_element": " ",
            "visibility": False
        },
        "win_lose": {
            "options": {"":""},
            "element": " ",
            "buf_element": " ",
            "visibility": False
        },
        "datetime": {
            "options": {"":""},
            "element": " ",
            "visibility": False
        }   
    },
    "html": {
        "inside": _get_table(),
        "msg_visibility": False
    }
}

initial_state = wf.init_state(init_dict)
