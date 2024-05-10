import itertools
import time
import os
import numpy as np
import pandas as pd
import string
import sys
# import warnings
# warnings.simplefilter('ignore', FutureWarning)
from datetime import datetime, timedelta, timezone
JST = timezone(timedelta(hours=+9), 'JST')
from dotenv import load_dotenv
from functools import wraps
from google.oauth2 import service_account
from google.cloud import bigquery
from os.path import join, dirname

def stop_watch(func):
    @wraps(func)
    def wrapper(*args, **kargs) :
        start = time.perf_counter()
        result = func(*args,**kargs)
        elapsed_time =  time.perf_counter() - start
        print(f"{func.__name__}は{elapsed_time}秒かかりました")
        return result
    return wrapper

class BigqueryDatabase:
    def __init__(self, dataset_name):
        self.client = self.get_my_client()
        self.dataset_name = dataset_name
        self.dataset_ref = f'{self.client.project}.{dataset_name}'

    # PythonからGCPへ接続するときの認証設定 https://qiita.com/R_plapla/items/a228c76cdf39456fd262
    # python-dotenvを使って環境変数を設定する https://qiita.com/harukikaneko/items/b004048f8d1eca44cba9
    def get_my_client(self):
        if sys.platform in ('win32', 'cygwin'): load_dotenv(join(dirname(__file__), '.env'))
        account = {
            "type": "service_account",
            "project_id": os.environ.get("GCP_PROJECT_ID"),
            "private_key_id": os.environ.get("GCS_PRIVATE_KEY_ID"),
            "private_key": os.environ.get("GCS_PRIVATE_KEY"),
            "client_email": os.environ.get("GCS_CLIENT_MAIL"),
            "client_id": os.environ.get("GCS_CLIENT_ID"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.environ.get("GCS_CLIENT_X509_CERT_URL")
        }
        credentials = service_account.Credentials.from_service_account_info(account)
        return bigquery.Client(credentials=credentials)
    
    def create_my_dataset(self):
        if self.dataset_name not in [obj.dataset_id for obj in self.client.list_datasets()]:
            dataset = bigquery.Dataset(self.dataset_ref)
            dataset.location = "US"
            self.client.create_dataset(dataset)

    def create_my_table(self, table_name=None, table_item=None):
        if table_name!=None: table_ref = f'{self.dataset_ref}.{table_name}'
        if table_item!=None: self.client.query(f"CREATE TABLE IF NOT EXISTS `{table_ref}` ({', '.join(table_item)});")

    def insert_my_data(self, table_name=None, insert_item=[], insert_data=[], main_data_index=-1):
        if table_name!=None: table_ref = f'{self.dataset_ref}.{table_name}'
        if len(insert_item)>0 and len(insert_data)>0:
        # 重複データが無いか確認
            select_df = self.client.query(f"SELECT {', '.join(insert_item)} FROM `{table_ref}`;").to_dataframe()
            select_val_tolist = select_df.values.tolist()
            select_val_list = list(itertools.chain.from_iterable(select_val_tolist))
            insert_values = []
            for d in insert_data:
                if d[main_data_index] in select_val_list:
                    print(f"'{d[main_data_index]}'は既にデータベースに登録されています")
                else:        
                    # 無ければデータ登録用のリストに格納
                    insert_values.append(str(d))
            print(f"INSERT INTO `{table_ref}` ({', '.join(insert_item)}) VALUES {', '.join(insert_values)};")
            self.client.query(f"INSERT INTO `{table_ref}` ({', '.join(insert_item)}) VALUES {', '.join(insert_values)};")
        else:
            print("登録するデータが無いか、データ型が指定されていません")

    def select_my_data(self, table_name=None, select_item=None, where_req=None):
        if table_name!=None: table_ref = f'{self.dataset_ref}.{table_name}'
        query = f"SELECT {', '.join(select_item)} FROM `{table_ref}`;"
        if where_req!=None: query=query[:-1]+f" WHERE {' AND '.join(where_req)};"
        #print(query)
        return self.client.query(query).to_dataframe()
         
    def delete_my_data(self, table_name=None, where_req=None):
        if table_name!=None: table_ref = f'{self.dataset_ref}.{table_name}'
        if where_req!=None:
            #print(f"DELETE FROM `{table_ref}` WHERE {' AND '.join(where_req)};")
            self.client.query(f"DELETE FROM `{table_ref}` WHERE {' AND '.join(where_req)};")
    
    def update_my_data(self, table_name=None, set_values=None, where_req=None):
        if table_name!=None: table_ref = f'{self.dataset_ref}.{table_name}'
        if set_values!=None and where_req!=None:
            #print(f"UPDATE `{table_ref}` SET {', '.join(set_values)} WHERE {' AND '.join(where_req)};")
            self.client.query(f"UPDATE `{table_ref}` SET {', '.join(set_values)} WHERE {' AND '.join(where_req)};")

# 【Python】クラスの継承・オーバーライドをしっかりと理解する https://note.com/keyma4note/n/ne62443307140
class SmashDatabase(BigqueryDatabase):
    def __init__(self, dataset_name):
        super().__init__(dataset_name)
        self.fighter_item_type = ('id INT64', 'recog_name STRING', 'first_color BOOL', 'fighter_id INT64', 'fighter_name STRING',)
        self.fighter_item = tuple([item.split()[0] for item in self.fighter_item_type])
        self.fighter_insert_data = [
            (1,	    'ALEX',         False,  79, 'STEVE'),
            (2,	    'BANJO',        True,   75, 'BANJO & KAZOOIE'),
            (3,	    'BAYONET',      True,   64, 'BAYONETTA'),
            (4, 	'BLACKPIT',     True,   33, 'BLACK PIT'),
            (5,	    'BRAWLER',      True,   84,	'Mii BRAWLER'),
            (6,	    'BYLETH',       True,   77,	'BYLETH'),
            (7,	    'CAPTAIN',      True,   12,	'CAPTAIN FALCON'),
            (8,	    'CHROM',        True,   29,	'CHROM'),
            (9,     'CLOUD',        True,   62,	'CLOUD'),
            (10,    'DAISY',        True,   15,	'DAISY'),
            (11,	'DARKSAM',      True,   5,  'DARK SAMUS'),
            (12,	'DEDEDE',       True,   42,	'DEDEDE'),
            (13,	'DIDDYK',       True,   39,	'DIDDY KONG'),
            (14,	'DONKEYK',      True,   2,	'DONKEY KONG'),
            (15,	'DrMA',         True,   20, 'Dr. MARIO'),
            (16,	'DUCKHUNT',     True,   59,	'DUCK HUNT'),
            (17,	'ENDERMAN',     False,  79,	'STEVE'),
            (18,	'FOX',          True,   8,	'FOX'),
            (19,	'GANONDORF',    True,   26, 'GANONDORF'),
            (20,	'GAOGAEN',      True,   71,	'GAOGAEN'),
            (21,	'GEKKOUGA',     True,   53,	'GEKKOUGA'),
            (22,	'GUNNER',       True,   86,	'Mii GUNNER'),
            (23,	'HERO',         True,   74,	'HERO'),
            (24,	'HIKARI',       True,   81,	'HOMURA / HIKARI'),
            (25,	'HOMU',         True,   81,	'HOMURA / HIKARI'),
            (26,	'ICECLIMBER',   True,   17,	'ICE CLIMBER'),
            (27,	'IGGY',         False,  58,	'KOOPA Jr.'),
            (28,	'IKE',          True,   37,	'IKE'),
            (29,	'INKLING',      True,   65,	'INKLING'),
            (30,	'JOKER',        True,   73,	'JOKER'),
            (31,	'KAMUI',        True,   63,	'KAMUI'),
            (32,	'KAZUYA',       True,   82,	'KAZUYA'),
            (33,	'KEN',          True,   61,	'KEN'),
            (34,	'KINGK',        True,   69,	'KING K. ROOL'),
            (35,	'KIRBY',        True,   7,	'KIRBY'),
            (36,	'KOOPAJr',      True,   58,	'KOOPA Jr.'),
            (37,	'LARRY',        False,  58,	'KOOPA Jr.'),
            (38,	'LEMMY',        False,  58,	'KOOPA Jr.'),
            (39,	'LITTLEMAC',    True,   52, 'LITTLE MAC'),
            (40,	'LUCAS',        True,   40,	'LUCAS'),
            (41,	'LUCA',         True,   44,	'LUCARIO'),
            (42,	'LUCINA',       True,   24,	'LUCINA'),
            (43,	'LUDWIG',       False,  58,	'KOOPA Jr.'),
            (44,	'LUIGI',        True,   10,	'LUIGI'),
            (45,	'MARTH',        True,   23,	'MARTH'),
            (46,	'META',         True,   31,	'META KNIGHT'),
            (47,	'MEWTWO',       True,   27,	'MEWTWO'),
            (48,	'MINMIN',       True,   78,	'MINMIN'),
            (49,	'MORTON',       False,  58,	'KOOPA Jr.'),
            (50,	'MrGAME',       True,   30,	'Mr. GAME & WATCH'),
            (51,	'MURABITO',     True,   48,	'MURABITO'),
            (52,	'NESS',         True,   11,	'NESS'),
            (53,	'PACKUN',       True,   72,	'PACKUN FLOWER'),
            (54,	'PACMAN',       True,   55,	'PAC-MAN'),
            (55,	'PALUTENA',     True,   54,	'PALUTENA'),
            (56,	'PEACH',        True,   14,	'PEACH'),
            (57,	'PICHU',        True,   21,	'PICHU'),
            (58,	'PIKACHU',      True,   9,	'PIKACHU'),
            (59,	'PIKMIN',       True,   43,	'PIKMIN & OLIMAR'),
            (60,	'POKEMON',      True,   38,	'POKEMON TRAINER'),
            (61,	'PURIN',        True,   13,	'PURIN'),
            (62,	'REFLET',       True,   56,	'REFLET'),
            (63,	'RICHT',        True,   68,	'RICHTER'),
            (64,	'RIDLEY',       True,   66,	'RIDLEY'),
            (65,	'ROBOT',        True,   45,	'ROBOT'),
            (66,	'ROCKMAN',      True,   49,	'ROCKMAN'),
            (67,	'ROSE',         True,   51,	'ROSETTA & CHIKO'),
            (68,	'ROY',          True,   28,	'ROY'),
            (69,	'RYU',          True,   60,	'RYU'),
            (70,	'SEPHIROTH',    True,   80,	'SEPHIROTH'),
            (71,	'SHEIK',        True,   18,	'SHEIK'),
            (72,	'SHIZUE',       True,   70,	'SHIZUE'),
            (73,	'SHULK',        True,   57,	'SHULK'),
            (74,	'SIMON',        True,   67,	'SIMON'),
            (75,	'SNAKE',        True,   36,	'SNAKE'),
            (76,	'SONIC',        True,   41,	'SONIC'),
            (77,	'SORA',         True,   83,	'SORA'),
            (78,	'STEVE',        True,   79,	'STEVE'),
            (79,	'SWORDFIGHTER', True,   85,	'Mii SWORD FIGHTER'),
            (80,	'TERRY',        True,   76,	'TERRY'),
            (81,	'TOONLI',       True,   46,	'TOON LINK'),
            (82,	'WARI',         True,   35,	'WARIO'),
            (83,	'WENDY',        False,  58,	'KOOPA Jr.'),
            (84,	'WiiFit',       True,   50,	'Wii Fit TRAINER'),
            (85,	'WOLF',         True,   47,	'WOLF'),
            (86,	'YOSHI',        True,   6,	'YOSHI'),
            (87,	'YOUNGLI',      True,   25,	'YOUNG LINK'),
            (88,	'ZELDA',        True,   19,	'ZELDA'),
            (89,	'ZEROSUIT',     True,   34,	'ZERO SUIT SAMUS'),
            (90,	'ZOMBIE',       False,  79,	'STEVE'),
            (91,	'FALCO',        True,   22,	'FALCO'),
            (92,	'KOOPA',        True,   16,	'KOOPA'),
            (93,	'LINK',         True,   3,	'LINK'),
            (94,	'MARIO',        True,   1,	'MARIO'),
            (95,	'PIT',          True,   32,	'PIT'),
            (96,	'SAMUS',        True,   4,	'SAMUS')
        ]
        self.analysis_item_type = (
            'id INT64', 'fighter_id_1p INT64', 'fighter_name_1p STRING', 'fighter_id_2p INT64', 'fighter_name_2p STRING', 
            'target_player_name STRING', 'target_player_is_1p BOOL', 'target_player_is_win BOOL', 
            'game_start_datetime DATETIME', 'game_start_url STRING','game_end_datetime DATETIME', 'game_end_url STRING', 
            'title STRING', 'category STRING',
        )
        self.analysis_item = tuple([item.split()[0] for item in self.analysis_item_type])
        self.drop_analysis_item = self.analysis_item[0:10]+self.analysis_item[12:]
    
    def create_fighter_table_data(self):
        super().create_my_table('fighter_table', self.fighter_item_type)
        super().insert_my_data('fighter_table', self.fighter_item, self.fighter_insert_data)
        
    def create_analysis_table(self):
        super().create_my_table('analysis_table', self.analysis_item_type)
    
    def insert_analysis_data(self, insert_data):
        super().insert_my_data('analysis_table', self.analysis_item_type, insert_data, 9)
    
    def select_fighter_data(self):
        df = super().select_my_data('fighter_table', ('*',))
        return df.sort_values('id')
    
    def select_analysis_data(self):
        df = super().select_my_data('analysis_table', ('*',))
        df = df.sort_values('game_start_datetime')
        # pandas 2.2.0の「Downcasting object dtype arrays ～」というFutureWarningに対応した https://qiita.com/yuji38kwmt/items/ba07a25924cfda363e42
        df = df.astype({"game_start_datetime":"str"})
        df = df.astype({"target_player_is_win":"str"})
        df = df[list(self.drop_analysis_item)]
        # [Python] pandas 条件抽出した行の特定の列に、一括で値を設定する https://note.com/kohaku935/n/n5836a09b96a6
        df.loc[df["target_player_is_win"]=="True", "target_player_is_win"] = "Win"
        df.loc[df["target_player_is_win"]=="False", "target_player_is_win"] = "Lose"
        return df
    
def main2():
    ssbu_db = SmashDatabase('ssbu_dataset')
    ssbu_db.create_my_dataset()
    ssbu_db.create_fighter_table_data()
    ssbu_db.create_analysis_table()
    df = ssbu_db.select_analysis_data()
    print(df)
    print(df['title'].value_counts())
    
# def ssbu_bq():
#     fighterlist = [fighterdata[4] for fighterdata in insert_data]
#     aulist=[]
#     for fighter in fighterlist:
#         for au in string.ascii_uppercase:
#             if au in fighter: aulist.append(au)
#     print(sorted(set(aulist)))

#     #select_item = ('fighter_id','fighter_name',)
#     select_item = ('*')
#     where_req = ('first_color = True','fighter_id < 72',)
#     df = ssbu_db.select_my_data('fighter_table', select_item, where_req)
#     df_sort = df.sort_values('fighter_id')
#     print(df_sort)
#     #print(df_sort['fighter_name'].to_list())
#     for recog_name in df_sort['recog_name'].to_list():
#         print(recog_name[-4:None])
#         print(recog_name[-5:-1])

#     df = ssbu_db.select_my_data('analysis_table', '*')
#     df_sort = df.sort_values('id')
#     print(df_sort)
#     print(df_sort['game_start_url'].to_list())

#     df = ssbu_db.select_my_data('analysis_table', ('*',), ('fighter_id_1p != 63','fighter_id_1p != 77',))
#     df_sort = df.sort_values('fighter_id_1p')
#     print(set(df_sort['fighter_name_1p'].to_list()))
#     df = ssbu_db.select_my_data('analysis_table', ('*',), ('fighter_id_2p != 63','fighter_id_2p != 77',))
#     df_sort = df.sort_values('fighter_id_2p')
#     print(set(df_sort['fighter_name_2p'].to_list()))
    
#     # df = ssbu_db.select_my_data('analysis_table', ('MAX(id)',))
#     # print(df.iloc[0,0])

#@stop_watch
def ssbu_bq_sel():
    ssbu_db = BigqueryDatabase('ssbu_dataset')
    
    #print(ssbu_db.select_my_data('analysis_table', ('MAX(id)',)).iloc[0,0])
    #print(len(ssbu_db.select_my_data('analysis_table', ('*',))))
    
    df = ssbu_db.select_my_data('analysis_table', ('*',))
    fighter_list = list(set(df['fighter_name_1p'].to_list()+df['fighter_name_2p'].to_list()))
    print(sorted(fighter_list),len(fighter_list))
    
    url_list = df['game_start_url'].to_list()
    org_url_list = list(set([url[:43] for url in url_list]))
    org_url_list.remove('https://www.youtube.com/watch?v=P7Olxt1_tG0')
    org_url_list.remove('https://www.youtube.com/watch?v=dqs-pK0JhuI')
    org_url_list.insert(0, 'https://www.youtube.com/watch?v=P7Olxt1_tG0')
    org_url_list.insert(0, 'https://www.youtube.com/watch?v=dqs-pK0JhuI')
    fighter_2p_list = df['fighter_name_2p'].to_list()
    rm_fighter_list = []
    for org_url in org_url_list:
        fighter_each_url = []
        for url, fighter_2p in zip(url_list, fighter_2p_list):
            if org_url in url: fighter_each_url.append(fighter_2p)
        if ('P7Olxt1_tG0' or 'dqs-pK0JhuI') in org_url: 
            rm_fighter_list += list(set(fighter_each_url)) 
        else: 
            #fighter_set = set([fighter for fighter in fighter_each_url if fighter not in rm_fighter_list])
            fighter_set = set(fighter_each_url)
            print(org_url, ":", len(fighter_set), ":", fighter_set)
    
def ssbu_bq_del():
    ssbu_db = BigqueryDatabase('ssbu_dataset')
    #ssbu_db.delete_my_data('fighter_table', ('id > -1',))
    #ssbu_db.delete_my_data('analysis_table', ('title = "2200を目指すスマメイト2095～"',))
    ssbu_db.delete_my_data('analysis_table', ('id > -1',))
    
def ssbu_bq_upd():
    ssbu_db = BigqueryDatabase('ssbu_dataset')
    ssbu_db.update_my_data('analysis_table', ("target_player_is_win_lose_draw = 'win'",) ,('fighter_id_1p = 46',))

if __name__ == '__main__':
    #BigqueryDatabase("ssbu_dataset")
    #ssbu_bq()
    #ssbu_bq_sel()
    #ssbu_bq_del()
    #ssbu_bq_upd()
    # main2()
    inputs = {"fighter_df": SmashDatabase('ssbu_dataset').select_fighter_data()}
    df_sorted = inputs["fighter_df"].sort_values(by='id')
    print(df_sorted)