import subprocess

# Getting started https://www.streamsync.cloud/getting-started.html
#cmd = "streamsync edit ssbu-db-app --port 10000"
cmd = "streamsync edit ssbu-yt-app --port 20000"
#cmd = "streamsync edit test --port 30000"

# 【Python入門】subprocessを使ってコマンドを実行しよう！ https://www.sejuku.net/blog/51090
subprocess.call(cmd.split())