import cv2
import mediapipe as mp

mp_face = mp.solutions.face_detection

def process_video(input_path, output_path):
    cap = cv2.VideoCapture(input_path)

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    silent_path = output_path.replace(".mp4", "_silent.mp4")

    out = cv2.VideoWriter(
        silent_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height)
    )

    with mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.5) as detector:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = detector.process(rgb)

            if results.detections:
                for det in results.detections:
                    bbox = det.location_data.relative_bounding_box

                    x = int(bbox.xmin * width)
                    y = int(bbox.ymin * height)
                    w = int(bbox.width * width)
                    h = int(bbox.height * height)

                    # Draw bounding box
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)

                    # Draw center circle
                    cx, cy = x + w//2, y + h//2
                    cv2.circle(frame, (cx, cy), 20, (255, 0, 0), -1)

            out.write(frame)

    cap.release()
    out.release()

    return silent_path