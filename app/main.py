import os
import uuid
import subprocess
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from app.processor import process_video

app = FastAPI()

TEMP_DIR = "/tmp"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.get("/")
def root():
    return {"status": "running"}

@app.post("/process-video")
async def process_video_endpoint(file: UploadFile = File(...)):
    input_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_input.mp4")
    output_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_output.mp4")

    with open(input_path, "wb") as f:
        f.write(await file.read())

    silent_video = process_video(input_path, output_path)

    final_output = output_path

    cmd = [
        "ffmpeg",
        "-y",
        "-i", silent_video,
        "-i", input_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        final_output
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return FileResponse(final_output, media_type="video/mp4", filename="output.mp4")