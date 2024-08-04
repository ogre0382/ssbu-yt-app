import cv2
from datetime import timedelta, timezone
JST = timezone(timedelta(hours=+9), 'JST')
import numpy as np
import yt_dlp
from dataclasses import dataclass, asdict

# https://github.com/ibaiGorordo/cap_from_youtube/blob/main/cap_from_youtube/cap_from_youtube.py

# YouTubeのストリーム情報を格納するためのデータクラス
@dataclass
class YoutubeStream:
    url: str = None
    resolution: str = None
    fps: str = None

    def __init__(self, format):
        self.url = format['url']
        self.resolution = format['format_note']
        self.fps = format['fps']

# YouTubeの情報を格納するためのデータクラス
@dataclass
class YoutubeInformation:
    title: str = None
    duration: int = -1
    channel: str = None
    release_timestamp: int = -1
    original_url: str = None
    fps: int = -1
    cap: cv2.VideoCapture = None

    def __init__(self, info):
        self.title = info['title']
        self.duration = info['duration']
        self.channel = info['channel']
        self.release_timestamp = info['timestamp'] if info['release_timestamp']==None else info['release_timestamp']
        self.original_url = info['original_url']
        self.fps = info['fps']
        self.cap = info['cap']

# YouTubeから情報を取得して画像処理するためのクラス
class GetYoutube:
    def __init__(self, input_url, resolution='best', ydl_opts={'verbose':True}, ):
        self.input_url = input_url
        self.resolution = resolution
        self.ydl_opts = ydl_opts
        self.info = None
        self.streams = None
        self.resolutions = None
        self.infos = []
        self.get_yt_infos()

    def __del__(self):
        for k in list(self.__dict__.keys()):
            if k!='infos': del self.__dict__[k]
    
    # YouTubeの情報を取得する
    def get_yt_infos(self):
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            infos = ydl.extract_info(self.input_url, download=False)
        if 'entries' in infos.keys(): infos = infos['entries']
        else: infos = [infos]
        for self.info in infos:
            self.get_yt_streams()
            self.get_yt_caps()
            self.infos.append(asdict(YoutubeInformation(self.info)))
        self.__del__()

    # YouTubeのストリーム情報を取得する
    def get_yt_streams(self):
        streams = [YoutubeStream(format)
                for format in self.info['formats'][::-1]
                if format['vcodec'] != 'none' and 'format_note' in format]
        _, unique_indices = np.unique(np.array([stream.resolution
                                                for stream in streams]), return_index=True)
        streams = [streams[index] for index in np.sort(unique_indices)]
        resolutions = np.array([stream.resolution for stream in streams])
        self.streams = streams[::-1]
        self.resolutions = resolutions[::-1]
    
    # YouTubeのストリームURLを取得する
    def get_yt_caps(self):
        if self.resolution == 'best':
            for j in range(len(self.streams)-1,-1,-1):
                if "p" in self.streams[j].resolution:
                    self.info['cap'] = self.streams[j].url
                    self.info['fps'] = self.streams[j].fps
                    break
        elif self.resolution not in self.resolutions:
            raise ValueError(f'Resolution {self.resolution} not available')
        else:
            res_index = np.where(self.resolutions == self.resolution)[0][0]
            self.info['cap'] = self.streams[res_index].url
            self.info['fps'] = self.streams[res_index].fps

    # YouTubeの画像を取得する：スタティックメソッド https://qiita.com/cardene/items/14d300c1b46371e74a38
    @staticmethod
    def get_yt_image(info, sec_pos=0, dsize=(1920,1080), gray=False, imw_path="imw_path", ydl_opts={'verbose':True}):
        cap = cv2.VideoCapture(info["cap"])
        cap.set(cv2.CAP_PROP_POS_FRAMES, info["fps"]*sec_pos)
        ret, img = cap.read()
        loop_cnt = 0
        while not ret:
            loop_cnt+=1
            print(f'Fail to do "cap.read()" with {info["original_url"]} ({loop_cnt} loop)')
            info = GetYoutube(info["original_url"], ydl_opts=ydl_opts).infos[0]
            cap = cv2.VideoCapture(info["cap"])
            cap.set(cv2.CAP_PROP_POS_FRAMES, info["fps"]*sec_pos)
            ret, img = cap.read()
        img = cv2.resize(img, dsize=dsize)
        if gray: img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if ('.jpg' in imw_path) or ('.png' in imw_path): cv2.imwrite(imw_path, img)
        return img
    
    # YouTubeの画像を処理する
    @staticmethod
    def set_yt_image(cv2dict=None, img=None, rect=False, crop=False, pre_dsize=None, post_dsize=None, gray=False, imr_path="imr_path", imw_path="imw_path"):
        if (img is None) and (('.jpg' in imr_path) or ('.png' in imr_path)): img = cv2.imread(imr_path, 0) if gray else cv2.imread(imr_path)
        if rect:
            for key in cv2dict.keys():
                img = cv2.rectangle(img, pt1=cv2dict[key]['pt1'], pt2=cv2dict[key]['pt2'], color=cv2dict[key]['color'], thickness=cv2dict[key]['thickness'])
        if crop:
            for i in range(len(cv2dict.keys())):
                img = img[cv2dict[f'crop{i}']['pt1'][1]:cv2dict[f'crop{i}']['pt2'][1], cv2dict[f'crop{i}']['pt1'][0]:cv2dict[f'crop{i}']['pt2'][0]]
                if i==0 and pre_dsize!=None: img = cv2.resize(img, dsize=pre_dsize)
        if post_dsize!=None: img = cv2.resize(img, dsize=post_dsize)
        if gray: img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if ('.jpg' in imw_path) or ('.png' in imw_path): cv2.imwrite(imw_path, img)
        return img

if __name__ == '__main__':
    url = 'https://www.youtube.com/playlist?list=PLxWXI3TDg12zJpAiXauddH_Mn8O9fUhWf'
    # 'cookiesfrombrowser': ('chrome',) -> メンバーシップ限定アーカイブ動画用オプション
    ydl_opts={'verbose':True, 'format':'best', 'cookiesfrombrowser': ('chrome',)}
    yt_infos = GetYoutube(url, ydl_opts=ydl_opts).infos
    print(yt_infos)