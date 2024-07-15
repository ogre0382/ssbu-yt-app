import itertools
import os
import sys
from datetime import timedelta, timezone
JST = timezone(timedelta(hours=+9), 'JST')
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.cloud import bigquery
from os.path import join, dirname
from time import sleep

# BigQueryのデータベース操作を行うクラス
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
    
    # BigQueryのデータセットを作成する
    def create_my_dataset(self):
        if self.dataset_name not in [obj.dataset_id for obj in self.client.list_datasets()]:
            dataset = bigquery.Dataset(self.dataset_ref)
            dataset.location = "US"
            self.client.create_dataset(dataset)

    # BigQueryのテーブルを作成する
    def create_my_table(self, table_name=None, table_item=None):
        if table_name!=None: table_ref = f'{self.dataset_ref}.{table_name}'
        if table_item!=None: self.client.query(f"CREATE TABLE IF NOT EXISTS `{table_ref}` ({', '.join(table_item)});")

    # BigQueryのテーブルにデータを挿入する
    def insert_my_data(self, table_name=None, insert_item=[], insert_data=[], main_data_index=-1):
        if table_name!=None: table_ref = f'{self.dataset_ref}.{table_name}'
        if len(insert_item)>0 and len(insert_data)>0: # 重複データが無いか確認
            select_df = self.client.query(f"SELECT {', '.join(insert_item)} FROM `{table_ref}`;").to_dataframe()
            select_val_tolist = select_df.values.tolist()
            select_val_list = list(itertools.chain.from_iterable(select_val_tolist))
            insert_values = []
            for d in insert_data:
                if (None in d) or (-1 in d):
                    print(f"欠損しているデータがあります: {d}")
                elif d[main_data_index] in select_val_list:
                    print(f"'{d[main_data_index]}'は既にデータベースに登録されています")
                else: # 既にデータベースに登録されているデータではない場合はデータ登録用のリストに格納
                    insert_values.append(str(d))
            print(f"INSERT INTO `{table_ref}` ({', '.join(insert_item)}) VALUES {', '.join(insert_values)};")
            self.client.query(f"INSERT INTO `{table_ref}` ({', '.join(insert_item)}) VALUES {', '.join(insert_values)};")
        else:
            print("登録するデータが無いか、データ型が指定されていません")

    # BigQueryのテーブルからデータを取得する
    def select_my_data(self, table_name=None, select_item=None, where_req=None):
        if table_name!=None: table_ref = f'{self.dataset_ref}.{table_name}'
        query = f"SELECT {', '.join(select_item)} FROM `{table_ref}`;"
        if where_req!=None: query=query[:-1]+f" WHERE {' AND '.join(where_req)};"
        return self.client.query(query).to_dataframe()
    
    # BigQueryのテーブルからデータを削除する
    def delete_my_data(self, table_name=None, where_req=None):
        if table_name!=None: table_ref = f'{self.dataset_ref}.{table_name}'
        if where_req!=None:
            print(f"DELETE FROM `{table_ref}` WHERE {' AND '.join(where_req)};")
            self.client.query(f"DELETE FROM `{table_ref}` WHERE {' AND '.join(where_req)};")
    
    # BigQueryのテーブルのデータを更新する
    def update_my_data(self, table_name=None, set_values=None, where_req=None):
        if table_name!=None: table_ref = f'{self.dataset_ref}.{table_name}'
        if set_values!=None and where_req!=None:
            print(f"UPDATE `{table_ref}` SET {', '.join(set_values)} WHERE {' AND '.join(where_req)};")
            self.client.query(f"UPDATE `{table_ref}` SET {', '.join(set_values)} WHERE {' AND '.join(where_req)};")

# BigQueryのデータベース(スマブラ)操作を行うクラス：【Python】クラスの継承・オーバーライドをしっかりと理解する https://note.com/keyma4note/n/ne62443307140
class SmashDatabase(BigqueryDatabase):
    def __init__(self):
        super().__init__('ssbu_dataset')
        self.fighter_item_type = ('id INT64', 'recog_name STRING', 'recog_name_en STRING', 'first_color BOOL', 'fighter_id INT64', 'fighter_name STRING', 'fighter_name_en STRING',)
        self.fighter_item = tuple([item.split()[0] for item in self.fighter_item_type])
        self.fighter_insert_data = [
            (1,	    'ALEX',             'ALEX',             False,  79, 'STEVE',                'STEVE'             ),
            (2,	    'BANJOKAZOOIE',     'BANJOKAZOOIE',     True,   75, 'BANJO & KAZOOIE',      'BANJO & KAZOOIE'   ),
            (3,	    'BAYONETTA',        'BAYONETTA',        True,   64, 'BAYONETTA',            'BAYONETTA'         ),
            (4, 	'BLACKPIT',         'DARKPIT',          True,   33, 'BLACK PIT',            'DARK PIT'          ),
            (5,	    'BYLETH',           'BYLETH',           True,   77,	'BYLETH',               'BYLETH'            ),
            (6,	    'CAPTAINFALCON',    'CAPTAINFALCON',    True,   12,	'CAPTAIN FALCON',       'CAPTAIN FALCON'    ),
            (7,	    'CHROM',            'CHROM',            True,   29,	'CHROM',                'CHROM'             ),
            (8,     'CLOUD',            'CLOUD',            True,   62,	'CLOUD',                'CLOUD'             ),
            (9,     'DAISY',            'DAISY',            True,   15,	'DAISY',                'DAISY'             ),
            (10,	'DARKSAMUS',        'DARKSAMUS',        True,   5,  'DARK SAMUS',           'DARK SAMUS'        ),
            (11,	'DEDEDE',           'KINGDEDEDE',       True,   42,	'DEDEDE',               'KING DEDEDE'       ),
            (12,	'DIDDYKONG',        'DIDDYKONG',        True,   39,	'DIDDY KONG',           'DIDDY KONG'        ),
            (13,	'DONKEYKONG',       'DONKEYKONG',       True,   2,	'DONKEY KONG',          'DONKEY KONG'       ),
            (14,	'DrMARIO',          'DrMARIO',          True,   20, 'Dr. MARIO',            'Dr. MARIO'         ),
            (15,	'DUCKHUNT',         'DUCKHUNT',         True,   59,	'DUCK HUNT',            'DUCK HUNT'         ),
            (16,	'ENDERMAN',         'ENDERMAN',         False,  79,	'STEVE',                'STEVE'             ),
            (17,	'FALCO',            'FALCO',            True,   22,	'FALCO',                'FALCO'             ),
            (18,	'FOX',              'FOX',              True,   8,	'FOX',                  'FOX'               ),
            (19,	'GANONDORF',        'GANONDORF',        True,   26, 'GANONDORF',            'GANONDORF'         ),
            (20,	'GAOGAEN',          'INCINEROAR',       True,   71,	'GAOGAEN',              'INCINEROAR'        ),
            (21,	'GEKKOUGA',         'GRENINJA',         True,   53,	'GEKKOUGA',             'GRENINJA'          ),
            (22,	'HERO',             'HERO',             True,   74,	'HERO',                 'HERO'              ),
            (23,	'HIKARIHOMURA',     'MYTHRAPYRA',       True,   81,	'HOMURA / HIKARI',      'PYRA / MYTHRA'     ),
            (24,	'HOMURAHIKARI',     'PYRAMYTHRA',       True,   81,	'HOMURA / HIKARI',      'PYRA / MYTHRA'     ),
            (25,	'ICECLIMBER',       'ICECLIMBER',       True,   17,	'ICE CLIMBER',          'ICE CLIMBER'       ),
            (26,	'IGGY',             'IGGY',             False,  58,	'KOOPA Jr.',            'BOWSER Jr.'        ),
            (27,	'IKE',              'IKE',              True,   37,	'IKE',                  'IKE'               ),
            (28,	'INKLING',          'INKLING',          True,   65,	'INKLING',              'INKLING'           ),
            (29,	'JOKER',            'JOKER',            True,   73,	'JOKER',                'JOKER'             ),
            (30,	'KAMUI',            'CORRIN',           True,   63,	'KAMUI',                'CORRIN'            ),
            (31,	'KAZUYA',           'KAZUYA',           True,   82,	'KAZUYA',               'KAZUYA'            ),
            (32,	'KEN',              'KEN',              True,   61,	'KEN',                  'KEN'               ),
            (33,	'KINGKROOL',        'KINGKROOL',        True,   69,	'KING K. ROOL',         'KING K. ROOL'      ),
            (34,	'KIRBY',            'KIRBY',            True,   7,	'KIRBY',                'KIRBY'             ),
            (35,	'KOOPA',            'BOWSER',           True,   16,	'KOOPA',                'BOWSER'            ),
            (36,	'KOOPAJr',          'BOWSERJr',         True,   58,	'KOOPA Jr.',            'BOWSER Jr.'        ),
            (37,	'LARRY',            'LARRY',            False,  58,	'KOOPA Jr.',            'BOWSER Jr.'        ),
            (38,	'LEMMY',            'LEMMY',            False,  58,	'KOOPA Jr.',            'BOWSER Jr.'        ),
            (39,	'LINK',             'LINK',             True,   3,	'LINK',                 'LINK'              ),
            (40,	'LITTLEMAC',        'LITTLEMAC',        True,   52, 'LITTLE MAC',           'LITTLE MAC'        ),
            (41,	'LUCAS',            'LUCAS',            True,   40,	'LUCAS',                'LUCAS'             ),
            (42,	'LUCARIO',          'LUCARIO',          True,   44,	'LUCARIO',              'LUCARIO'           ),
            (43,	'LUCINA',           'LUCINA',           True,   24,	'LUCINA',               'LUCINA'            ),
            (44,	'LUDWIG',           'LUDWIG',           False,  58,	'KOOPA Jr.',            'BOWSER Jr.'        ),
            (45,	'LUIGI',            'LUIGI',            True,   10,	'LUIGI',                'LUIGI'             ),
            (46,	'MARIO',            'MARIO',            True,   1,	'MARIO',                'MARIO'             ),
            (47,	'MARTH',            'MARTH',            True,   23,	'MARTH',                'MARTH'             ),
            (48,	'METAKNIGHT',       'METAKNIGHT',       True,   31,	'META KNIGHT',          'META KNIGHT'       ),
            (49,	'MEWTWO',           'MEWTWO',           True,   27,	'MEWTWO',               'MEWTWO'            ),
            (50,	'MiiBRAWLER',       'MiiBRAWLER',       True,   84,	'Mii BRAWLER',          'Mii BRAWLER'       ),
            (51,	'MiiGUNNER',        'MiiGUNNER',        True,   86,	'Mii GUNNER',           'Mii GUNNER'        ),
            (52,	'MiiSWORDFIGHTER',  'MiiSWORDFIGHTER',  True,   85,	'Mii SWORD FIGHTER',    'Mii SWORD FIGHTER' ),
            (53,	'MINMIN',           'MINMIN',           True,   78,	'MINMIN',               'MINMIN'            ),
            (54,	'MORTON',           'MORTON',           False,  58,	'KOOPA Jr.',            'KOOPA Jr.'         ),
            (55,	'MrGAMEWATCH',      'MRGAMEWATCH',      True,   30,	'Mr. GAME & WATCH',     'MR. GAME & WATCH'  ),
            (56,	'MURABITO',         'VILLAGER',         True,   48,	'MURABITO',             'VILLAGER'          ),
            (57,	'NESS',             'NESS',             True,   11,	'NESS',                 'NESS'              ),
            (58,	'PACKUNFLOWER',     'PIRANHAPLANT',     True,   72,	'PACKUN FLOWER',        'PIRANHA PLANT'     ),
            (59,	'PACMAN',           'PACMAN',           True,   55,	'PAC-MAN',              'PAC-MAN'           ),
            (60,	'PALUTENA',         'PALUTENA',         True,   54,	'PALUTENA',             'PALUTENA'          ),
            (61,	'PEACH',            'PEACH',            True,   14,	'PEACH',                'PEACH'             ),
            (62,	'PICHU',            'PICHU',            True,   21,	'PICHU',                'PICHU'             ),
            (63,	'PIKACHU',          'PIKACHU',          True,   9,	'PIKACHU',              'PIKACHU'           ),
            (64,	'PIKMINALPH',       'ALPH',             False,  43,	'PIKMIN & OLIMAR',      'OLIMAR'            ),
            (65,	'PIKMINOLIMAR',     'OLIMAR',           True,   43,	'PIKMIN & OLIMAR',      'OLIMAR'            ),
            (66,	'PIT',              'PIT',              True,   32,	'PIT',                  'PIT'               ),
            (67,	'POKEMONTRAINER',   'POKEMONTRAINER',   True,   38,	'POKEMON TRAINER',      'POKEMON TRAINER'   ),
            (68,	'PURIN',            'JIGGLYPUFF',       True,   13,	'PURIN',                'JIGGLYPUFF'        ),
            (69,	'REFLET',           'ROBIN',            True,   56,	'REFLET',               'ROBIN'             ),
            (70,	'RICHTER',          'RICHTER',          True,   68,	'RICHTER',              'RICHTER'           ),
            (71,	'RIDLEY',           'RIDLEY',           True,   66,	'RIDLEY',               'RIDLEY'            ),
            (72,	'ROBOT',            'ROB',              True,   45,	'ROBOT',                'R.O.B.'            ),
            (73,	'ROCKMAN',          'MEGAMAN',          True,   49,	'ROCKMAN',              'MEGA MAN'          ),
            (74,	'ROSETTACHIKO',     'ROSALINALUMA',     True,   51,	'ROSETTA & CHIKO',      'ROSALINA & LUMA'   ),
            (75,	'ROY',              'ROY',              True,   28,	'ROY',                  'ROY'               ),
            (76,	'RYU',              'RYU',              True,   60,	'RYU',                  'RYU'               ),
            (77,	'SAMUS',            'SAMUS',            True,   4,	'SAMUS',                'SAMUS'             ),
            (78,	'SEPHIROTH',        'SEPHIROTH',        True,   80,	'SEPHIROTH',            'SEPHIROTH'         ),
            (79,	'SHEIK',            'SHEIK',            True,   18,	'SHEIK',                'SHEIK'             ),
            (80,	'SHIZUE',           'ISABELLE',         True,   70,	'SHIZUE',               'ISABELLE'          ),
            (81,	'SHULK',            'SHULK',            True,   57,	'SHULK',                'SHULK'             ),
            (82,	'SIMON',            'SIMON',            True,   67,	'SIMON',                'SIMON'             ),
            (83,	'SNAKE',            'SNAKE',            True,   36,	'SNAKE',                'SNAKE'             ),
            (84,	'SONIC',            'SONIC',            True,   41,	'SONIC',                'SONIC'             ),
            (85,	'SORA',             'SORA',             True,   83,	'SORA',                 'SORA'              ),
            (86,	'STEVE',            'STEVE',            True,   79,	'STEVE',                'STEVE'             ),
            (87,	'TERRY',            'TERRY',            True,   76,	'TERRY',                'TERRY'             ),
            (88,	'TOONLINK',         'TOONLINK',         True,   46,	'TOON LINK',            'TOON LINK'         ),
            (89,	'WARIO',            'WARIO',            True,   35,	'WARIO',                'WARIO'             ),
            (90,	'WENDY',            'WENDY',            False,  58,	'KOOPA Jr.',            'KOOPA Jr.'         ),
            (91,	'WiiFitTRAINER',    'WiiFitTRAINER',    True,   50,	'Wii Fit TRAINER',      'Wii Fit TRAINER'   ),
            (92,	'WOLF',             'WOLF',             True,   47,	'WOLF',                 'WOLF'              ),
            (93,	'YOSHI',            'YOSHI',            True,   6,	'YOSHI',                'YOSHI'             ),
            (94,	'YOUNGLINK',        'YOUNGLINK',        True,   25,	'YOUNG LINK',           'YOUNG LINK'        ),
            (95,	'ZELDA',            'ZELDA',            True,   19,	'ZELDA',                'ZELDA'             ),
            (96,	'ZEROSUITSAMUS',    'ZEROSUITSAMUS',    True,   34,	'ZERO SUIT SAMUS',      'ZERO SUIT SAMUS'   ),
            (97,	'ZOMBIE',           'ZOMBIE',           False,  79,	'STEVE',                'STEVE'             )
        ]
        self.analysis_item_type = (
            'id INT64', 'fighter_id_1p INT64', 'fighter_name_1p STRING', 'fighter_name_1p_en STRING',
                        'fighter_id_2p INT64', 'fighter_name_2p STRING', 'fighter_name_2p_en STRING', 
            'target_player_name STRING', 'target_player_is_1p BOOL', 'target_player_is_win BOOL', 
            'game_start_datetime DATETIME', 'game_start_url STRING','game_end_datetime DATETIME', 'game_end_url STRING', 
            'title STRING', 'category STRING',
        )
        self.analysis_item = tuple([item.split()[0] for item in self.analysis_item_type])
        self.drop_analysis_item = self.analysis_item[0:12]+self.analysis_item[14:]
    
    # ファイター名のデータセットを作成する
    def create_fighter_table_data(self):
        super().create_my_table('fighter_table', self.fighter_item_type)
        super().insert_my_data('fighter_table', self.fighter_item, self.fighter_insert_data)
    
    # 分析結果のデータセットを作成する
    def create_analysis_table(self):
        super().create_my_table('analysis_table', self.analysis_item_type)
    
    # 分析結果のデータを挿入する
    def insert_analysis_data(self, insert_data):
        super().insert_my_data('analysis_table', self.analysis_item, insert_data, 11)
    
    # ファイター名のデータを取得する
    def select_fighter_data(self):
        df = super().select_my_data('fighter_table', ('*',))
        return df.sort_values('id')
    
    # 分析結果のデータを取得する
    def select_analysis_data(self, drop=False):
        df = super().select_my_data('analysis_table', ('*',))
        df = df.sort_values('game_start_datetime')
        # pandas 2.2.0の「Downcasting object dtype arrays ～」というFutureWarningに対応した https://qiita.com/yuji38kwmt/items/ba07a25924cfda363e42
        df = df.astype({"game_start_datetime":"str"})
        df = df.astype({"target_player_is_win":"str"})
        if drop: df = df[list(self.drop_analysis_item)]
        # [Python] pandas 条件抽出した行の特定の列に、一括で値を設定する https://note.com/kohaku935/n/n5836a09b96a6
        df.loc[df["target_player_is_win"]=="True", "target_player_is_win"] = "Win"
        df.loc[df["target_player_is_win"]=="False", "target_player_is_win"] = "Lose"
        return df
    
    def delete_analysis_data(self, where_req):
        super().delete_my_data('analysis_table', where_req)
    
    # 分析結果のデータを更新する
    def update_analysis_data(self, set_values, where_req):
        super().update_my_data('analysis_table', set_values, where_req)

def main_create(ssbu_db:SmashDatabase):
    ssbu_db.create_my_dataset()
    ssbu_db.create_fighter_table_data()
    ssbu_db.create_analysis_table()
    print(f"作成したデータベース: {ssbu_db.select_fighter_data()}")
    print(f"作成したデータベース: {ssbu_db.select_analysis_data()}")

def main_delete(ssbu_db:SmashDatabase, where_req):
    print(f"削除前のデータベース: {ssbu_db.select_analysis_data()}")
    ssbu_db.delete_analysis_data(where_req)
    sleep(5)
    print(f"削除後のデータベース: {ssbu_db.select_analysis_data()}")    

if __name__ == '__main__':
    ssbu_db = SmashDatabase()
    main_create(ssbu_db)
    main_delete(ssbu_db, (f"REGEXP_CONTAINS(target_player_name, r'向井田可夢')",))