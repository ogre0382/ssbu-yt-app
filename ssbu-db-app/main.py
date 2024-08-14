import pandas as pd
import writer as wf
import os
import plotly.express as px
import re
import sys
sys.path.append(os.path.join(os.path.dirname('__file__'), '..'))
from module.bq_db import SmashDatabase
from time import sleep


# EVENT HANDLERS

# フィルタリング処理
def update(state):
    # Language：日本語 or 英語 を選択
    if state["input"]["lang"]["element"]!=" " and state["input"]["player"]["element"]==" ":
        state["df"] = _get_df()
        state["suf"] = "" if state["input"]["lang"]["element"]=="jp" else "_en"
        state["html"]["inside"] = _get_table(state["df"], state["suf"])
        _get_options(state, "player", 'target_player_name')
        _get_chart(state)
    
    # Player：プレイヤー名 を選択
    if state["input"]["player"]["element"]!=" " and state["input"]["fighter"]["element"]==" ":
        state["input"]["player"]["buf_element"] = state["input"]["player"]["element"]
        state["df"] = state["df"].query(f'target_player_name == "{state["input"]["player"]["element"]}"')
        state["html"]["inside"] = _get_table(state["df"], state["suf"])
        _get_merge_options(state, "fighter")
        _get_chart(state)
    
    # Fighter：プレイヤーの ファイター名 を選択
    if state["input"]["fighter"]["element"]!=" " and state["input"]["vs_fighter"]["element"]==" ":
        state["input"]["fighter"]["buf_element"] = state["input"]["fighter"]["element"]
        state["df"] = state["df"].query(f'fighter_name_1p{state["suf"]} == "{state["input"]["fighter"]["element"]}" or fighter_name_2p{state["suf"]} == "{state["input"]["fighter"]["element"]}"')
        state["html"]["inside"] = _get_table(state["df"], state["suf"])
        _get_merge_options(state, "vs_fighter", False)
        _get_chart(state)
    
    # vs Fighter：対戦相手の ファイター名 を選択
    if state["input"]["vs_fighter"]["element"]!=" " and state["input"]["category"]["element"]==" ":
        state["input"]["vs_fighter"]["buf_element"] = state["input"]["vs_fighter"]["element"]
        cond = "and" if state["input"]["fighter"]["element"]==state["input"]["vs_fighter"]["element"] else "or"
        state["df"] = state["df"].query(f'fighter_name_1p{state["suf"]} == "{state["input"]["vs_fighter"]["element"]}" {cond} fighter_name_2p{state["suf"]} == "{state["input"]["vs_fighter"]["element"]}"')
        state["html"]["inside"] = _get_table(state["df"], state["suf"])
        _get_options(state, "category", 'category')
        _get_chart(state)
    
    # Category：カテゴリー を選択
    if state["input"]["category"]["element"]!=" " and state["input"]["date"]["element"]==" ":
        state["input"]["category"]["buf_element"] = state["input"]["category"]["element"]
        state["df"] = state["df"].query(f'category == "{state["input"]["category"]["element"]}"')
        state["html"]["inside"] = _get_table(state["df"], state["suf"])
        _get_options(state, "date", 'game_start_datetime')
        _get_chart(state)
    
    # Date：日付 を選択
    if state["input"]["date"]["element"]!=" " and state["input"]["win_lose"]["element"]==" ":
        state["input"]["date"]["buf_element"] = state["input"]["date"]["element"]
        # state["df"] = state["df"].query(f'game_start_datetime == "{state["input"]["date"]["element"]}"')
        df = state["df"]
        state["df"] = df[df['game_start_datetime'].str.contains(f'{state["input"]["date"]["element"]}')]
        state["html"]["inside"] = _get_table(state["df"], state["suf"])
        _get_options(state, "win_lose", 'target_player_is_win')
        _get_chart(state)
    
    # Win or Lose：勝敗 を選択
    if state["input"]["win_lose"]["element"]!=" " and state["input"]["datetime"]["element"]==" ":
        state["input"]["win_lose"]["buf_element"] = state["input"]["win_lose"]["element"]
        state["df"] = state["df"].query(f'target_player_is_win == "{state["input"]["win_lose"]["element"]}"')
        state["html"]["inside"] = _get_table(state["df"], state["suf"])
        _get_options(state, "datetime", 'game_start_datetime')
        _get_chart(state)
    
    # Datetime：日時 を選択
    if state["input"]["datetime"]["element"]!=" " and state["input"]["correct_mode"]["element"]=="off":
        state["df"] = state["df"].query(f'game_start_datetime == "{state["input"]["datetime"]["element"]}"')
        state["html"]["inside"] = _get_table(state["df"], state["suf"])
        # Correct Mode 用の選択肢を作成
        df = state["sub_df"].sort_values('fighter_id')[[f'fighter_name{state["suf"]}']]
        df = df[~df.duplicated(keep='first')]
        df2dict = df[f'fighter_name{state["suf"]}'].to_dict()
        state["input"]["vs_fighter"]["options"] = state["input"]["fighter"]["options"] = {v: v for v in df2dict.values()}
        state["input"]["category"]["options"] = {v: v for v in ["smashmate", "other", "VIP"]}
        state["input"]["win_lose"]["options"] = {v: v for v in ["Lose", "Win"]}
        _update_visibility(state, ["correct_mode"])
    
    # Correct Mode：修正モード オン
    if state["input"]["correct_mode"]["element"]=="on":
        state["input"]["correct_mode"]["visibility2"] = True
        if 'delete' in state["input"]["correct_mode"]["element2"]:
            state["input"]["correct_mode"]["disabled"] = "no"
            _update_visibility(state, ["correct_mode"])
        else:
            state["input"]["correct_mode"]["disabled"] = "yes"
            _update_visibility(state, ["lang", "player", "datetime"], others_off=False)
        for k in init_dict["input"].keys(): 
            if "buf_element" in init_dict["input"][k].keys():
                if state["input"][k]["element"]!=state["input"][k]["buf_element"]:
                    state["set_values_type"].append(k)
                    state["input"]["correct_mode"]["disabled"] = "no"

# データ修正
def correct(state):
    game_start_url = state["df"].iat[0, 11]
    # 対象データを削除
    if 'delete' in state["input"]["correct_mode"]["element2"]:
        SmashDatabase().delete_analysis_data((f"game_start_url = '{game_start_url}'",))
    # 対象データを修正
    else:
        set_values = []
        for k in state["set_values_type"]:
            # 修正対象がプレイヤー名の場合
            if k=="player":
                element = state["input"]["player"]["element"]
                set_value = (f"target_player_name = '{element}'")
            # 修正対象がプレイヤーのファイター名の場合
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
            # 修正対象が対戦相手のファイター名の場合
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
            # 修正対象がカテゴリーの場合
            if k=="category":
                element = state["input"]["category"]["element"]
                set_value = (f"category = '{element}'")
            # 修正対象が勝敗の場合
            if k=="win_lose":
                element = "true" if state["input"]["win_lose"]["element"]=="Win" else "false"
                set_value = (f"target_player_is_win = {element}")
            # 修正対象追加
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

# データベースからデータを取得
def _get_df():
    return SmashDatabase().select_analysis_data(drop=True)

# テーブルを作成取得
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

# 日時用フォーマット関数
def _format_df(datetime_str):
    return datetime_str[:10]

# 選択肢を取得
def _get_options(state, input_type, df_item):
    df = state["df"][[df_item]].sort_values(df_item)
    if input_type=="date":
        # df = df.to_string(formatters={'game_start_datetime': _format_df})
        df_list = [st[:10] for st in df[df_item].to_list()]
        df = pd.DataFrame(df_list, columns=['game_start_datetime'])
    # df.drop_duplicates(df_item)
    df2dict = df[df_item].to_dict()
    state["input"][input_type]["options"] = {v: v for v in df2dict.values()}
    print(state["input"][input_type]["options"])
    _update_visibility(state, [input_type])

# データをマージして選択肢を取得
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
    
def _get_chart(state=None, is_wl=False):
    if state!=None:
        df = state["df"]
        suf = state["suf"]
    else:
        df = _get_df()
        suf = ""
    if is_wl:
        pass
    df_1p = df.query('target_player_is_1p == False')
    df_1p = df_1p[['fighter_id_1p', f'fighter_name_1p{suf}', 'target_player_is_win']]
    df_1p.columns = ['fighter_id', 'fighter_name', 'target_player_is_win']
    df_2p = df.query('target_player_is_1p == True')
    df_2p = df_2p[['fighter_id_2p', f'fighter_name_2p{suf}', 'target_player_is_win']]
    df_2p.columns = ['fighter_id', 'fighter_name', 'target_player_is_win']
    df = pd.concat([df_1p, df_2p], axis=0)
    df = df.sort_values('fighter_id')
    
    # 1. 各ファイターの試合数をカウント
    total_counts = df['fighter_name'].value_counts().reset_index()
    total_counts.columns = ['fighter_name', 'total_matches']

    # 2. 各ファイターの勝利数をカウント
    win_counts = df.query('target_player_is_win == "Win"')['fighter_name'].value_counts().reset_index()
    win_counts.columns = ['fighter_name', 'win_matches']

    # 3. 試合数と勝利数をマージ
    merged_counts = pd.merge(total_counts, win_counts, on='fighter_name', how='left')

    # 4. 勝率を計算
    merged_counts['win_rate'] = merged_counts['win_matches'] / merged_counts['total_matches']

    # NaNを0に置き換え（勝利数が0のファイターのため）
    merged_counts['win_rate'] = merged_counts['win_rate'].fillna(0)
    
    win_rate = merged_counts[['fighter_name','win_rate']].sort_values('fighter_name')
    fig = px.bar(win_rate, x='fighter_name', y='win_rate')
    
    if state!=None: state["chart"] = fig
    else: return fig

# UPDATES

# 入力欄の表示を更新
def _update_visibility(state, options_type_list=[], others_off=True):
    for k in init_dict["input"].keys(): 
        if others_off: state["input"][k]["visibility"] = True if k in options_type_list else False
        else: state["input"][k]["visibility"] = True if k not in options_type_list else False


# STATE INIT

init_dict = {
    "df": _get_df(),
    "sub_df": SmashDatabase().select_fighter_data(),
    "set_values_type": [],
    "chart": _get_chart(),
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
        "date": {
            "options": {"":""},
            "element": " ",
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
