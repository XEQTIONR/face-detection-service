import cv2
import tempfile
import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from starlette.background import BackgroundTasks

app = FastAPI(title="Face Redaction Microservice")

# Load OpenCV's pre-trained Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def remove_file(path: str):
    """Utility to clean up temporary files after the response is sent."""
    if os.path.exists(path):
        os.remove(path)

@app.post("/anonymize/")
async def anonymize_video(background_tasks: BackgroundTasks, video: UploadFile = File(...)):
    # 1. Create temporary files for input and output
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as input_temp:
        input_temp.write(await video.read())
        input_path = input_temp.name

    output_path = input_path.replace(".mp4", "_output.mp4")

    # 2. Open the video using OpenCV
    cap = cv2.VideoCapture(input_path)
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Set up the video writer (using mp4v codec)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # 3. Process the video frame-by-frame
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert frame to grayscale for the face detection algorithm
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Draw a black square over each detected face
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 0), -1) # -1 fills the rectangle

        # Write the processed frame to the output video
        out.write(frame)

    # 4. Clean up resources
    cap.release()
    out.release()

    # 5. Schedule cleanup of temporary files after the user downloads the result
    background_tasks.add_task(remove_file, input_path)
    background_tasks.add_task(remove_file, output_path)

    # 6. Return the processed video
    return FileResponse(
        path=output_path, 
        media_type="video/mp4", 
        filename=f"anonymized_{video.filename}"
    )

@app.get("/health")
def health_check():
    return {"status": "healthy"}