import numpy as np
import subprocess
import cv2
import ffmpeg
import os
import tempfile
import logging
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse

# Setup logging so you can see errors in the DigitalOcean "Runtime Logs"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Get the absolute path to the XML file to avoid "File Not Found" errors
CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)
        logger.info(f"Cleaned up: {path}")

@app.post("/anonymize/")
async def anonymize_video(background_tasks: BackgroundTasks, video: UploadFile = File(...)):
    logger.info(f"Received file: {video.filename}")
    
    # 1. Save input
    try:
        while chunk := await video.read(1024 * 1024): # Read 1MB at a time
            input_temp.write(chunk)
    finally:
        input_path = input_temp.name
        input_temp.close()
    
    output_path = input_path.replace(".mp4", "_out.mp4")
    logger.info(f"Temporary input path: {input_path}")

    # 2. Open video and check if it actually opened
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        logger.error("Could not open input video with OpenCV")
        return {"error": "Invalid video format"}

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0: fps = 24.0
    
    logger.info(f"Video Meta: {width}x{height} at {fps} FPS")

    # 3. Setup FFmpeg Pipe
    try:
        process = (
            ffmpeg
            .input('pipe:', format='rawvideo', pix_fmt='bgr24', s=f'{width}x{height}', r=fps)
            .output(output_path, pix_fmt='yuv420p', vcodec='libx264', preset='ultrafast')
            .overwrite_output()
            .run_async(pipe_stdin=True, pipe_stderr=True) # Catch FFmpeg errors
        )
        logger.info("FFmpeg pipe initialized")
    except Exception as e:
        logger.error(f"FFmpeg startup failed: {e}")
        return {"error": "FFmpeg initialization failed"}

    # 4. Processing Loop
    try:
        logger.info("Gonna try")
        frame_count = 0
        while cap.isOpened():
            logger.info("in while")
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 0), -1)
                logger.info("rectange created")

            try:
                # 2. THE CRITICAL FIX: Force frame to match the pipe's expected size
                # If the frame is 1081x1920 but the pipe expects 1080x1920, it fails on frame 2.
                logger.info("Trying step 2")
                if frame.shape[1] != width or frame.shape[0] != height:
                    frame = cv2.resize(frame, (width, height))
            except Exception as e:
                logger.error(f"Step 2 Error during processing: {e}")

            try:
                # 3. Ensure the frame is in C-contiguous memory (required for pipes)
                logger.info("Trying step 3")
                frame_bytes = frame.tobytes()
            except Exception as e:
                logger.error(f"Step 3 Error during processing: {e}")

            try:
                logger.info("Trying step 4")
                process.stdin.write(frame_bytes)
            except BrokenPipeError:
                logger.error("FFmpeg pipe closed unexpectedly. Check FFmpeg stderr for details.")
                break
            logger.info("wrote bytes")
            frame_count += 1
            if frame_count % 30 == 0:
                logger.info(f"Processed {frame_count} frames...")

    except Exception as e:
        logger.error(f"Error during processing: {e}")
    finally:
        cap.release()
        if process.stdin:
            process.stdin.close()
        process.wait()
        logger.info("Processing complete")

    # 5. Verify Output exists
    if not os.path.exists(output_path) or os.path.getsize(output_path) < 100:
        logger.error("Output file is missing or empty")
        return {"error": "Processing failed to produce output"}

    background_tasks.add_task(remove_file, input_path)
    background_tasks.add_task(remove_file, output_path)

    return FileResponse(output_path, media_type="video/mp4", filename="redacted.mp4")

@app.get("/debug-ffmpeg")
def debug_ffmpeg():
    try:
        res = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        return {"status": "found", "version": res.stdout.split('\n')[0]}
    except FileNotFoundError:
        return {"status": "not found", "error": "FFmpeg binary is missing from the OS"}