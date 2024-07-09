import subprocess

# Getting started https://www.writer.cloud/getting-started.html
# cmd = "writer edit ssbu-db-app --port 1993"
cmd = "writer edit ssbu-yt-app --port 382"
# cmd = "writer edit test --port 20000"

# 【Python入門】subprocessを使ってコマンドを実行しよう！ https://www.sejuku.net/blog/51090
subprocess.call(cmd.split())