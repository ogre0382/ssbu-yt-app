import subprocess

def gen_exe():
    NAME = 'ssbu-yt-app'
    name_opt = '--name'
    name_cmd = [f"{name_opt}={NAME}"]
    
    MODULENAME = ['cv2', 'easyocr', 'yt_dlp']
    mod_opt = '--hidden-import'
    mod_cmd = [f"{mod_opt}="+module for module in MODULENAME]
    
    PACKAGENAME = ['db_dtypes', 'google', 'shapely', 'writer']
    pac_opt = '--collect-all'
    pac_cmd = [f"{pac_opt}="+package for package in PACKAGENAME]
    
    cmd = ["pyinstaller", "--onefile"] + name_cmd + mod_cmd + pac_cmd +  ["serve.py"]
    print(cmd)
    subprocess.run(cmd)
    
if __name__ == '__main__':
    gen_exe()