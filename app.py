# app.py
from flask import Flask, request, send_file
import cv2
import numpy as np
import uuid
import tempfile
import os

app = Flask(__name__)

# Load face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def draw_on_face(frame):
    """
    Detect faces and draw a simple rectangle + text on each face
    Treats the face as one object
    """
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    # For each face found
    for (x, y, w, h) in faces:
        # Draw rectangle around face
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
        
        # Add text label
        cv2.putText(frame, 'FACE', (x, y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        # Optional: Draw a circle on the face
        center = (x + w // 2, y + h // 2)
        cv2.circle(frame, center, w // 3, (255, 0, 0), 2)
    
    return frame

@app.route('/process', methods=['POST'])
def process_video():
    """Process video - detect face and draw on it"""
    
    # Get video file
    video_file = request.files['video']
    
    # Save input video temporarily
    input_path = os.path.join(tempfile.gettempdir(), f"input_{uuid.uuid4().hex}.mp4")
    output_path = os.path.join(tempfile.gettempdir(), f"output_{uuid.uuid4().hex}.mp4")
    
    video_file.save(input_path)
    
    # Open video
    cap = cv2.VideoCapture(input_path)
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Setup output video
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
    
    # Process each frame
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Draw on face
        processed_frame = draw_on_face(frame)
        
        # Write frame
        out.write(processed_frame)
    
    # Clean up
    cap.release()
    out.release()
    os.remove(input_path)
    
    # Return processed video
    return send_file(
        output_path,
        mimetype='video/mp4',
        as_attachment=True,
        download_name='processed_video.mp4'
    )

@app.route('/', methods=['GET'])
def home():
    return "Video Face Detection Service. Send POST request to /process with video file."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
