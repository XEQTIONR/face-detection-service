import cv2
import ffmpeg
import numpy as np
import os
import tempfile
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse

app = FastAPI()

# Load the face detection model
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@app.post("/anonymize/")
async def anonymize_video(background_tasks: BackgroundTasks, video: UploadFile = File(...)):
    # 1. Save uploaded file to a temporary location
    input_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    input_temp.write(await video.read())
    input_path = input_temp.name
    input_temp.close()

    output_path = input_path.replace(".mp4", "_out.mp4")

    # 2. Open video to get metadata
    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0: fps = 24

    # 3. Setup FFmpeg process for writing (The "Magic" Fix)
    # This creates an H.264 MP4 that is web-compatible
    process = (
        ffmpeg
        .input('pipe:', format='rawvideo', pix_fmt='bgr24', s=f'{width}x{height}', r=fps)
        .output(output_path, pix_fmt='yuv420p', vcodec='libx264', preset='ultrafast')
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Face Detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 0), -1)

            # Push the processed frame into the FFmpeg pipe
            process.stdin.write(frame.tobytes())

    finally:
        cap.release()
        process.stdin.close()
        process.wait()

    # 4. Cleanup and Return
    background_tasks.add_task(remove_file, input_path)
    background_tasks.add_task(remove_file, output_path)

    return FileResponse(output_path, media_type="video/mp4", filename="redacted.mp4")

@app.get("/health")
def health():
    return {"status": "ok"}