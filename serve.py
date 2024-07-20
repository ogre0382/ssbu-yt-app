import multiprocessing as mp
import uvicorn
import writer.serve
from fastapi import FastAPI, Response

# Multiple apps at once https://dev.writer.com/framework/custom-server#multiple-apps-at-once
def asgi_app(is_yt_app=True, mode="run"):
    app_name = "ssbu-yt-app" if is_yt_app else "ssbu-db-app"
    port = 382 if is_yt_app else 1017
    
    root_asgi_app = FastAPI(lifespan=writer.serve.lifespan)
    sub_asgi_app = writer.serve.get_asgi_app(app_name, mode)

    root_asgi_app.mount("/", sub_asgi_app)

    @root_asgi_app.get("/")
    async def init():
        return Response("""
        <h1>Welcome to the App Hub</h1>
        """)
        
    print(f"http://127.0.0.1:{port}/")
    
    uvicorn.run(root_asgi_app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        ws_max_size=writer.serve.MAX_WEBSOCKET_MESSAGE_SIZE)

# PyInstaller+multiprocessingをWindows上で動かす時のメモ https://qiita.com/npkk/items/cc4c46181c06ff41bdf3
if __name__ == '__main__':
    mp.freeze_support()
    asgi_app()
    # asgi_app(is_yt_app=False, mode="edit")