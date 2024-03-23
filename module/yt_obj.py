import cv2
from datetime import datetime, timedelta, timezone
JST = timezone(timedelta(hours=+9), 'JST')
import numpy as np
import os
import yt_dlp
from dataclasses import dataclass, field, asdict
from PIL import Image


@dataclass
class YoutubeStream:
    url: str = None
    resolution: str = None
    fps: str = None

    def __init__(self, format):
        self.url = format['url']
        self.resolution = format['format_note']
        self.fps = format['fps']

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
        self.release_timestamp = info['release_timestamp']
        self.original_url = info['original_url']
        self.fps = info['fps']
        self.cap = info['cap']

class GetYoutube:
    def __init__(self, input_url, resolution='best', ydl_opts={'verbose':True, 'format':'best', 'cookiesfrombrowser': ('chrome',)}, ):
        self.input_url = input_url
        self.resolution = resolution
        self.ydl_opts = ydl_opts
        self.info = None
        self.streams = None
        self.resolutions = None
        self.infos = []
        self.get_yt_infos()
        #os.system('cls')

    def __del__(self):
        for k in list(self.__dict__.keys()):
            if k!='infos': del self.__dict__[k]
    
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
    
    def get_yt_caps(self):
        if self.resolution == 'best':
            for j in range(len(self.streams)-1,-1,-1):
                if "p" in self.streams[j].resolution:
                    # self.info['cap'] = cv2.VideoCapture(self.streams[j].url)
                    self.info['cap'] = self.streams[j].url
                    self.info['fps'] = self.streams[j].fps
                    break
        elif self.resolution not in self.resolutions:
            raise ValueError(f'Resolution {self.resolution} not available')
        else:
            res_index = np.where(self.resolutions == self.resolution)[0][0]
            # self.info['cap'] = cv2.VideoCapture(self.streams[res_index].url)
            self.info['cap'] = self.streams[res_index].url
            self.info['fps'] = self.streams[res_index].fps

    # スタティックメソッド https://qiita.com/cardene/items/14d300c1b46371e74a38
    @staticmethod
    def get_yt_image(info, sec_pos=0, dsize=(1920,1080), imw_path=None, ydl_opts={'verbose':True, 'format':'best', 'cookiesfrombrowser': ('chrome',)}, ):
        cap = cv2.VideoCapture(info["cap"])
        cap.set(cv2.CAP_PROP_POS_FRAMES, info["fps"]*sec_pos)
        ret, img = cap.read()
        if not ret:
            info = GetYoutube(info["original_url"], ydl_opts=ydl_opts).infos[0]
            cap = cv2.VideoCapture(info["cap"])
            cap.set(cv2.CAP_PROP_POS_FRAMES, info["fps"]*sec_pos)
            ret, img = cap.read()
        img = cv2.resize(img, dsize=dsize)
        if ('.jpg' in imw_path) or ('.png' in imw_path): cv2.imwrite(imw_path, img)
        return img
    
    @staticmethod
    def set_yt_image(cv2dict, rect=False, crop=False, dsize=(1920,1080), imr_path=None, imw_path=None):
        img = cv2.imread(imr_path)
        if rect:
            for key in cv2dict.keys():
                img = cv2.rectangle(img, pt1=cv2dict[key]['pt1'], pt2=cv2dict[key]['pt2'], color=cv2dict[key]['color'], thickness=cv2dict[key]['thickness'])
        if crop:
            for key in cv2dict.keys():
                img = img[cv2dict[key]['pt1'][1]:cv2dict[key]['pt2'][1], cv2dict[key]['pt1'][0]:cv2dict[key]['pt2'][0]]
                #img = img[crop['top']:crop['top']+crop['height'], crop['left']:crop['left']+crop['width']]
        img = cv2.resize(img, dsize=dsize)
        if ('.jpg' in imw_path) or ('.png' in imw_path): cv2.imwrite(imw_path, img)
        return img
        

"""
@dataclass
class YoutubeInfomation:
    title: str = None
    duration: int = None
    release_datetime: datetime = None
    original_url: str = None
    fps: int = 0
    cap: cv2.VideoCapture = None

    def __init__(self, info):
        self.title = info['title']
        self.duration = info['duration']
        self.release_datetime = datetime.fromtimestamp(info['release_timestamp'], JST).strftime('%Y-%m-%d %T')
        self.original_url = info['original_url']
        self.fps = info['fps']
        self.formats = info['formats'][::-1]
        self.cap = None

    def __del__(self):
        for k in list(self.__dict__.keys()):
            if k not in ('title', 'duration', 'release_datetime', 'original_url', 'fps'): del self.__dict__[k]

    @staticmethod
    def get_yt_infos(input_url, ydl_opts={}):
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            infos = ydl.extract_info(input_url, download=False)
            if 'entries' in infos.keys(): infos = infos['entries']
            else: infos = [infos]
            return [YoutubeInfomation(info) for info in infos]


@dataclass
class YoutubeStream:
    url: str = None
    resolution: str = None

    def __init__(self, format):
        self.url = format['url']
        self.resolution = format['format_note']

    @staticmethod
    def get_yt_streams(info):
        streams = [YoutubeStream(format)
                for format in info.formats
                if format['vcodec'] != 'none' and 'format_note' in format]
        info.__del__()
        _, unique_indices = np.unique(np.array([stream.resolution
                                                for stream in streams]), return_index=True)
        streams = [streams[index] for index in np.sort(unique_indices)]
        resolutions = np.array([stream.resolution for stream in streams])
        return streams[::-1], resolutions[::-1]


def get_yt_caps(input_url, resolution='best', ydl_opts={}):
    infos = YoutubeInfomation.get_yt_infos(input_url, ydl_opts=ydl_opts)
    for i,info in enumerate(infos):
        streams, resolutions = YoutubeStream.get_yt_streams(info)
        
        if resolution == 'best':
            for j in range(len(streams)-1,-1,-1):
                if "p" in streams[j].resolution:
                    info.cap = cv2.VideoCapture(streams[j].url)
                    break

        elif resolution not in resolutions:
            raise ValueError(f'Resolution {resolution} not available')
        
        else:
            res_index = np.where(resolutions == resolution)[0][0]
            info.cap = cv2.VideoCapture(streams[res_index].url)
        #print(info)
        infos[i] = info

    return infos
"""

#def get_yt_image(info, frame_pos, dsize=None, crop_dsize=None, crop=None, add_rect_dsize=None, add_rect=None, cv2pil=False, gray=False):
def get_yt_image(info, frame_pos, ydl_opts={}, dsize=None, crop=None, add_rect=None, cv2pil=False, gray=False):
    cap = info.cap
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
    ret, img = cap.read()
    if not ret:
        yt = GetYoutube(info.original_url, ydl_opts=ydl_opts)
        info = yt.infos[0]
        cap = info.cap
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
        ret, img = cap.read()
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    if dsize!=None: img = cv2.resize(img, dsize=dsize)
    if crop!=None:
        #if crop_dsize!=None: img = cv2.resize(img, dsize=crop_dsize)
        left, top, width, height = tuple(map(int, crop.values()))
        img = img[top:top + height, left:left + width]
        if dsize!=None: img = cv2.resize(img, dsize=dsize)
    if add_rect!=None:
        #if add_rect_dsize!=None: img = cv2.resize(img, dsize=add_rect_dsize)
        for key in add_rect.keys():
            img = cv2.rectangle(img, pt1=add_rect[key]['pt1'], pt2=add_rect[key]['pt2'], color=add_rect[key]['color'], thickness=add_rect[key]['thickness'])
    if gray: img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    if cv2pil: return info,Image.fromarray(img)
    else: return info,img

def get_total_sec(infos):
    total_sec=0
    for info in infos:
        total_sec+=info["duration"]
    return timedelta(seconds=total_sec)

if __name__ == '__main__':
    # url = 'https://www.youtube.com/playlist?list=PLxWXI3TDg12zAPnbxJkz99IB_npRLLB3_'
    url = 'https://www.youtube.com/playlist?list=PLxWXI3TDg12zJpAiXauddH_Mn8O9fUhWf'
    #url = 'https://www.youtube.com/watch?v=6aUsPo83Rsw'
    ydl_opts={'verbose':True, 'format':'best', 'cookiesfrombrowser': ('chrome',)}
    yt_infos = GetYoutube(url, ydl_opts=ydl_opts).infos
    # for info in yt.infos:
    #     for tgt in [19928.0]:
    #         for sec in range(int(tgt-1),int(tgt+1)):
    #             cv2.imshow('19928', get_yt_image(info.cap, sec*info.fps))
    #             cv2.waitKey()
    print(yt_infos)
    # for info in yt_infos:
    #     print(GetYoutube.get_yt_image(info))
        
    # print(get_total_sec(yt_infos))
    #print(type(get_yt_image(yt_infos[0], yt_infos[0]["fps"]*100, ydl_opts=ydl_opts)[1]))