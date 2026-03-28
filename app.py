from flask import Flask, request, send_file, jsonify
import cv2
import numpy as np
import uuid
import tempfile
import os
import sys
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load face detector with error handling
try:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        raise Exception("Failed to load cascade classifier")
    logging.info("Face detector loaded successfully")
except Exception as e:
    logging.error(f"Error loading face detector: {e}")
    face_cascade = None

def draw_on_face(frame):
    if face_cascade is None:
        return frame
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    for (x, y, w, h) in faces:
        # Draw rectangle around face
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
        cv2.putText(frame, 'FACE', (x, y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        # Draw circle on face
        center = (x + w // 2, y + h // 2)
        cv2.circle(frame, center, w // 3, (255, 0, 0), 2)
    
    return frame

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'face_detector_loaded': face_cascade is not None,
        'opencv_version': cv2.__version__
    }), 200

@app.route('/process', methods=['POST'])
def process_video():
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file'}), 400
        
        video_file = request.files['video']
        input_path = os.path.join(tempfile.gettempdir(), f"input_{uuid.uuid4().hex}.mp4")
        output_path = os.path.join(tempfile.gettempdir(), f"output_{uuid.uuid4().hex}.mp4")
        
        video_file.save(input_path)
        
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            return jsonify({'error': 'Could not open video file'}), 400
        
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            processed_frame = draw_on_face(frame)
            out.write(processed_frame)
            frame_count += 1
            
            if frame_count % 100 == 0:
                logging.info(f"Processed {frame_count} frames")
        
        cap.release()
        out.release()
        
        # Clean up input file
        try:
            os.remove(input_path)
        except:
            pass
        
        return send_file(
            output_path,
            mimetype='video/mp4',
            as_attachment=True,
            download_name='processed_video.mp4'
        )
    
    except Exception as e:
        logging.error(f"Error processing video: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'service': 'Face Detection Service',
        'endpoints': {
            '/health': 'GET - Health check',
            '/process': 'POST - Process video with face detection',
            '/': 'GET - This help message'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)