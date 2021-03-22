import json
import asyncio
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Header
from fastapi import Request, Response
from fastapi import WebSocket
from fastapi.templating import Jinja2Templates
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK


# https://stribny.name/blog/2020/07/real-time-data-streaming-using-fastapi-and-websockets/
# https://stribny.name/blog/fastapi-video/

app = FastAPI()
templates = Jinja2Templates(directory="templates")
CHUNK_SIZE = 1024*1024
video_path = Path("video.mp4")

with open('measurements.json', 'r') as file:
    measurements = iter(json.loads(file.read()))


@app.get("/chart")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/video")
async def read_root(request: Request):
    return templates.TemplateResponse("video.html", context={"request": request})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await asyncio.sleep(0.1)
            payload = next(measurements)
            await websocket.send_json(payload)
    except ConnectionClosedOK:
        pass


@app.get("/video/src")
async def video_endpoint(range: str = Header(None)):
    start, end = range.replace("bytes=", "").split("-")
    start = int(start)
    end = int(end) if end else start + CHUNK_SIZE
    with open(video_path, "rb") as video:
        video.seek(start)
        data = video.read(end - start)
        filesize = str(video_path.stat().st_size)
        headers = {
            'Content-Range': f'bytes {str(start)}-{str(end)}/{filesize}',
            'Accept-Ranges': 'bytes'
        }
        return Response(data, status_code=206, headers=headers, media_type="video/mp4")


if __name__ == '__main__':
    uvicorn.run(app=app, host='127.0.0.1', port=8000)
