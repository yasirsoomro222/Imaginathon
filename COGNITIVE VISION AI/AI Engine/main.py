import cv2
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from Agents.classroom_agent import ClassroomAgent
# Agar aapne cafeteria_agent.py bhi bana liya hai toh usay bhi import kar lein:
from Agents.cafeteria_agent import CafeteriaAgent

app = FastAPI(title="Cognitive Vision AI - Coordinator Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agents initialize karein
classroom_agent = ClassroomAgent()
cafeteria_agent = CafeteriaAgent()

classroom_status = {
    "smoking_detected": False,
    "id_card_detected": False,
    "missing_id_alert": False,
    "confidence": 0.0,
    "detected_class": "None"
}

cafeteria_status = {
    "cafeteria_smoking_detected": False,
    "confidence": 0.0,
    "detected_class": "None",
    "warning": "Normal"
}

@app.get("/live_status")
def get_live_status():
    return classroom_status

@app.get("/cafeteria_status")
def get_cafeteria_status():
    return cafeteria_status

# 1. Classroom Feed Generator
def generate_classroom_frames():
    global classroom_status
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success or frame is None:
            break

        annotated_frame, status = classroom_agent.process_frame(frame)
        classroom_status = status

        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        if not ret:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    cap.release()

# 2. Cafeteria Feed Generator
def generate_cafeteria_frames():
    global cafeteria_status
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success or frame is None:
            break

        annotated_frame, status = cafeteria_agent.process_frame(frame)
        cafeteria_status = status

        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        if not ret:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    cap.release()

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(generate_classroom_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/cafeteria_feed")
def cafeteria_feed():
    return StreamingResponse(generate_cafeteria_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    import sys
    print("=" * 70)
    print("DEPRECATED: AI Engine server has been merged into Backend/main.py")
    print("Run:  venv\\Scripts\\python.exe Backend\\main.py")
    print("=" * 70)
    sys.exit(0)