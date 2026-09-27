import os
import sys
import time
import threading
import datetime
import smtplib
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from collections import deque
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.responses import StreamingResponse, Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ultralytics import YOLO

# Windows beep sound ke liye (agar Windows nahi hai toh try-except handle kar lega)
try:
    import winsound
except ImportError:
    winsound = None

from lms_integration import send_challan_to_lms, send_to_lms, send_warning_to_lms

import database
from database import (
    init_db,
    get_students,
    get_student,
    add_student,
    update_student,
    get_warnings,
    get_chalans,
    get_notifications,
    mark_notification_read,
    get_unread_count,
    update_warning_delivery,
    update_chalan_delivery,
)
from notifications import send_warning, issue_chalan, mark_chalan_paid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------- Tunable settings (Optimized for Mobile Streams & Detection) ----------------
SMOKING_CONF = 0.30
ID_CARD_CONF = 0.35
PERSON_CONF = 0.45
SMOKING_IMGSZ = 640
ID_CARD_IMGSZ = 640
PERSON_IMGSZ = 224

# Smoking object filters
SMOKING_MIN_AREA = 15
SMOKING_MAX_AREA = 12000
SMOKING_MIN_ASPECT = 0.15
SMOKING_MAX_ASPECT = 4.0
SMOKING_MAX_CONF = 0.98

# ID card filters
ID_MIN_WIDTH = 40
ID_MIN_HEIGHT = 25
ID_MIN_ASPECT = 0.5
ID_MAX_ASPECT = 2.0

# State smoothing
CONFIRM_FRAMES = 2
CLEAR_FRAMES = 6
ALERT_COOLDOWN_SEC = 15
FRAME_SKIP = 1  # No frame skipping for real-time smoothness with mobile streams
CAMERA_SOURCES = [
    "http://192.168.0.100:8080/video",  # Update with your mobile IP Webcam URL
    0                                  # Fallback or second camera
]
JPEG_QUALITY = 75
ID_CARD_NEAR_PERSON = True  # require ID card to be on a detected person

# Where alert screenshots are stored
ALERTS_DIR = Path(BASE_DIR) / "alert_images"
ALERTS_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Cognitive Vision AI - Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Models ----------------
def load_model(path):
    try:
        model = YOLO(path)
        print(f"[models] loaded {os.path.basename(path)} | classes: {model.names}")
        return model
    except Exception as e:
        print(f"[models] FAILED to load {path}: {e}")
        return None

smoking_model = load_model(os.path.join(BASE_DIR, "smoking.pt"))
id_model = load_model(os.path.join(BASE_DIR, "id_card.pt"))
person_model = load_model(os.path.join(BASE_DIR, "yolov8n.pt"))

ID_CARD_CLASS = "id-card"
SMOKING_CLASSES = {"cigarette", "vape", "smoking"}

alerts = deque(maxlen=300)
history_alerts = deque(maxlen=500)
alerts_lock = threading.Lock()


# ---------------- Pydantic request models ----------------
class StudentCreate(BaseModel):
    name: str
    roll_no: str
    department: str = ""
    email: str = ""


class StudentUpdate(BaseModel):
    name: str | None = None
    roll_no: str | None = None
    department: str | None = None
    email: str | None = None


class WarningRequest(BaseModel):
    student_id: int
    alert_id: str = ""
    camera: str = "classroom"
    reason: str = "Smoking detected on campus"
    send_email: bool = False
    send_portal: bool = True


class ProcessAlertRequest(BaseModel):
    alert_id: str
    student_id: int
    reason: str
    send_email: bool = False
    send_portal: bool = True


class ChalanRequest(BaseModel):
    student_id: int
    alert_id: str = ""
    camera: str = "classroom"
    reason: str = "Repeated smoking violation"
    amount: int = 5000
    send_email: bool = False
    send_portal: bool = True


class ChalanStatusUpdate(BaseModel):
    status: str


def seed_default_students():
    """Seed default students including Muhammad Yasir Soomro, Amal Fatima, and Sualeha Jameel."""
    try:
        existing_students = get_students()
        existing_emails = [s.get("email") for s in existing_students]
        
        if "yasirsoomro468@gmail.com" not in existing_emails:
            add_student("Muhammad Yasir Soomro", "SE-001", "Software Engineering", "yasirsoomro468@gmail.com")
        if "amalfatima12020@gmail.com" not in existing_emails:
            add_student("Amal Fatima", "SE-002", "Software Engineering", "amalfatima12020@gmail.com")
        if "sualehajameel72@gmail.com" not in existing_emails:
            add_student("Sualeha Jameel", "SE-003", "Software Engineering", "sualehajameel72@gmail.com")
    except Exception as e:
        print(f"[db] Error seeding default students: {e}")


def send_real_email(to_email: str, subject: str, body: str, image_path: Path | str = None):
    """Send a real email using SMTP with a properly structured image attachment."""
    sender_email = os.environ.get("SMTP_EMAIL", "yasirsoomro468@gmail.com")
    sender_password = os.environ.get("SMTP_PASSWORD", "szfttcfocgjiorzy")
    
    if sender_password == "your_app_password_here" and not os.environ.get("SMTP_PASSWORD"):
        print("[email] SMTP password not configured properly.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        if image_path:
            img_path_obj = Path(image_path)
            if img_path_obj.exists():
                with open(img_path_obj, 'rb') as f:
                    img_data = f.read()
                
                img = MIMEImage(img_data, name=img_path_obj.name)
                img.add_header('Content-Disposition', 'attachment', filename=img_path_obj.name)
                msg.attach(img)
                print(f"[email] Attached image successfully: {img_path_obj.name}")

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        print(f"[email] Successfully sent email to {to_email}")
        return True
    except Exception as e:
        print(f"[email] Failed to send email: {e}")
        return False


def get_alert_snapshot(alert_id: str):
    if not alert_id:
        return None
    with alerts_lock:
        for alert in alerts:
            if alert["id"] == alert_id:
                return alert.copy()
    return None


def get_alert_image_path(alert: dict | None):
    if not alert or not alert.get("image"):
        return None
    image_path = ALERTS_DIR / alert["image"]
    return image_path if image_path.is_file() else None


def resolve_action_evidence(alert_id: str):
    if not alert_id:
        return None, None, None

    alert = get_alert_snapshot(alert_id)
    if not alert:
        return None, None, "Selected alert is no longer available"

    image_path = get_alert_image_path(alert)
    if not image_path:
        return alert, None, "Selected alert image is unavailable"

    return alert, image_path, None


def save_alert_image(camera, violation_type, annotated):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = f"{camera}_{violation_type}_{timestamp}.jpg"
    filepath = ALERTS_DIR / filename
    try:
        cv2.imwrite(str(filepath), annotated)
        return filename
    except Exception as e:
        print(f"[alert] failed to save image: {e}")
        return None


def play_alert_beep():
    """Play a system beep sound when an alert triggers."""
    try:
        if winsound:
            # Frequency 2500Hz, Duration 500ms
            winsound.Beep(2500, 500)
    except Exception as e:
        print(f"[beep] Error playing sound: {e}")


def add_alert(camera, violation_type, confidence, annotated):
    image_name = save_alert_image(camera, violation_type, annotated)
    alert_id = f"{camera}-{violation_type}-{int(time.time() * 1000)}"
    
    # Trigger beep sound asynchronously
    threading.Thread(target=play_alert_beep, daemon=True).start()

    with alerts_lock:
        default_students = get_students()
        suggested_student = default_students[0] if default_students else {
            "id": 1,
            "name": "Muhammad Yasir Soomro",
            "roll_no": "SE-001",
            "department": "Software Engineering",
            "email": "yasirsoomro468@gmail.com"
        }

        alert_data = {
            "id": alert_id,
            "camera": camera,
            "type": violation_type,
            "confidence": round(float(confidence), 2),
            "timestamp_iso": datetime.datetime.now().isoformat(timespec="seconds"),
            "image": image_name,
            "suggested_student": suggested_student,
        }
        alerts.appendleft(alert_data)
    print(f"[alert] {camera}: {violation_type} (conf={confidence:.2f}) image={image_name}")

    return alert_id


class ViolationState:
    __slots__ = ("pos", "neg", "active", "last_alert_ts")

    def __init__(self):
        self.pos = 0
        self.neg = 0
        self.active = False
        self.last_alert_ts = 0.0

    def update(self, positive, camera, violation_type, confidence, annotated):
        if positive:
            self.pos += 1
            self.neg = 0
        else:
            self.neg += 1
            self.pos = 0

        if not self.active and self.pos >= CONFIRM_FRAMES:
            self.active = True
            now = time.time()
            if now - self.last_alert_ts >= ALERT_COOLDOWN_SEC:
                self.last_alert_ts = now
                add_alert(camera, violation_type, confidence, annotated)
        elif self.active and self.neg >= CLEAR_FRAMES:
            self.active = False


def draw_box(frame, x1, y1, x2, y2, label, color):
    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
    cv2.putText(frame, label, (int(x1), max(0, int(y1) - 8)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)


def detect_persons(frame):
    persons = []
    max_conf = 0.0
    if person_model is None:
        return persons, max_conf
    res = person_model(frame, conf=PERSON_CONF, imgsz=PERSON_IMGSZ, classes=[0], verbose=False)[0]
    for box in res.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        conf = float(box.conf[0])
        persons.append((x1, y1, x2, y2, conf))
        if conf > max_conf:
            max_conf = conf
    return persons, max_conf


def is_near_any_person(x1, y1, x2, y2, persons, frame_height):
    if not persons:
        return True

    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0

    for px1, py1, px2, py2, _ in persons:
        if cx < px1 or cx > px2 or cy < py1 or cy > py2:
            continue
        person_height = py2 - py1
        if person_height <= 0:
            continue
        if cy <= py1 + person_height * 0.55:
            return True
    return False


def detect_smoking(frame, persons):
    boxes = []
    max_conf = 0.0
    detected_class = "None"

    if smoking_model is None:
        return boxes, max_conf, detected_class

    res = smoking_model(frame, conf=SMOKING_CONF, imgsz=SMOKING_IMGSZ, verbose=False)[0]
    frame_height = frame.shape[0]

    for box in res.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        conf = float(box.conf[0])
        cls_name = smoking_model.names[int(box.cls[0])]

        if cls_name.lower() not in SMOKING_CLASSES:
            continue

        w, h = x2 - x1, y2 - y1
        area = w * h
        aspect = h / w if w > 0 else 0

        if area < SMOKING_MIN_AREA or area > SMOKING_MAX_AREA:
            continue

        if aspect < SMOKING_MIN_ASPECT or aspect > SMOKING_MAX_ASPECT:
            continue

        if y1 > frame_height * 0.60:
            continue

        if not is_near_any_person(x1, y1, x2, y2, persons, frame_height):
            continue

        boxes.append((x1, y1, x2, y2, conf, cls_name))
        if conf > max_conf:
            max_conf = conf
            detected_class = cls_name

    return boxes, max_conf, detected_class


def is_on_any_person(x1, y1, x2, y2, persons):
    if not persons:
        return False
    box_area = (x2 - x1) * (y2 - y1)
    if box_area <= 0:
        return False

    for px1, py1, px2, py2, _ in persons:
        ix1 = max(x1, px1)
        iy1 = max(y1, py1)
        ix2 = min(x2, px2)
        iy2 = min(y2, py2)
        if ix2 <= ix1 or iy2 <= iy1:
            continue
        overlap = (ix2 - ix1) * (iy2 - iy1)
        if overlap / box_area >= 0.5:
            return True
    return False


def detect_id_cards(frame, persons):
    found = False
    max_conf = 0.0
    boxes = []

    if id_model is None:
        return found, max_conf, boxes

    res = id_model(frame, conf=ID_CARD_CONF, imgsz=ID_CARD_IMGSZ, verbose=False)[0]
    for box in res.boxes:
        cls_id = int(box.cls[0])
        cls_name = id_model.names.get(cls_id, "").lower()

        if cls_name not in (ID_CARD_CLASS, "id_card", "idcard", "id"):
            continue

        conf = float(box.conf[0])
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        w, h = x2 - x1, y2 - y1

        if w < ID_MIN_WIDTH or h < ID_MIN_HEIGHT:
            continue

        aspect = h / w if w > 0 else 0
        if aspect < ID_MIN_ASPECT or aspect > ID_MAX_ASPECT:
            continue

        if ID_CARD_NEAR_PERSON and not is_on_any_person(x1, y1, x2, y2, persons):
            continue

        found = True
        if conf > max_conf:
            max_conf = conf
        boxes.append((x1, y1, x2, y2, conf))

    return found, max_conf, boxes


def detect_in_frame(frame):
    annotated = frame.copy()
    persons, max_person_conf = detect_persons(frame)
    person_visible = len(persons) > 0

    smoking_boxes, max_smoking_conf, smoking_class = detect_smoking(frame, persons)
    id_card_found, max_id_conf, id_boxes = detect_id_cards(frame, persons)

    for x1, y1, x2, y2, conf in persons:
        draw_box(annotated, x1, y1, x2, y2, f"Person {conf:.2f}", (255, 180, 0))

    for x1, y1, x2, y2, conf, cls_name in smoking_boxes:
        draw_box(annotated, x1, y1, x2, y2, f"{cls_name} {conf:.2f}", (0, 0, 255))

    for x1, y1, x2, y2, conf in id_boxes:
        draw_box(annotated, x1, y1, x2, y2, f"ID Card {conf:.2f}", (0, 200, 0))

    if person_visible and not id_card_found:
        cv2.rectangle(annotated, (15, 15), (470, 65), (0, 0, 255), -1)
        cv2.putText(annotated, "WARNING: ID CARD MISSING!", (25, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    evidence = {
        "smoking_boxes": smoking_boxes,
        "max_smoking_conf": max_smoking_conf,
        "smoking_class": smoking_class,
        "id_card_found": id_card_found,
        "max_id_conf": max_id_conf,
        "person_visible": person_visible,
        "max_person_conf": max_person_conf,
        "persons": persons,
    }
    return evidence, annotated


class CameraPipeline:
    def __init__(self, name, source):
        self.name = name
        self.source = source
        self.online = False
        self.smoking_state = ViolationState()
        self.id_state = ViolationState()
        self._lock = threading.Lock()
        self._latest_jpeg = None
        self._status = {
            "camera": name,
            "online": False,
            "smoking_detected": False,
            "id_card_missing": False,
            "person_visible": False,
            "id_card_visible": False,
            "confidence": 0.0,
            "detected_class": "None",
            "fps": 0.0,
            "latest_alert_id": "",
        }
        self._stop = threading.Event()
        threading.Thread(target=self._run, daemon=True, name=f"pipeline-{name}").start()

    def _offline_frame(self, w=640, h=480):
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        cv2.putText(frame, f"{self.name.upper()} CAMERA OFFLINE", (60, h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 100), 2)
        cv2.putText(frame, "Check camera connection", (60, h // 2 + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (80, 80, 80), 1)
        return frame

    def _run(self):
        frame_idx = 0
        fps_count = 0
        fps_timer = time.time()
        offline_placeholder = self._offline_frame()

        while not self._stop.is_set():
            frame = None
            
            # Robust Mobile / IP Webcam Snapshot Handler
            if isinstance(self.source, str) and self.source.startswith("http"):
                try:
                    snap_url = self.source.replace("/video", "/shot.jpg")
                    req = urllib.request.urlopen(snap_url, timeout=3)
                    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
                    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                except Exception:
                    try:
                        cap = cv2.VideoCapture(self.source)
                        if cap.isOpened():
                            ret, frame = cap.read()
                            cap.release()
                    except Exception:
                        pass
            else:
                cap = cv2.VideoCapture(self.source)
                if cap.isOpened():
                    ret, frame = cap.read()
                    cap.release()

            if frame is None:
                self.online = False
                with self._lock:
                    self._status["online"] = False
                    ok_enc, buffer = cv2.imencode('.jpg', offline_placeholder, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
                    if ok_enc:
                        self._latest_jpeg = buffer.tobytes()
                time.sleep(1.0)
                continue

            self.online = True
            with self._lock:
                self._status["online"] = True

            # Resize to 640x360 to guarantee fluid real-time inference without lag
            frame = cv2.resize(frame, (640, 360))

            frame_idx += 1
            if frame_idx % FRAME_SKIP == 0:
                try:
                    evidence, annotated = detect_in_frame(frame)
                except Exception as e:
                    annotated = frame
                    evidence = None

                if evidence is not None:
                    smoking_positive = len(evidence["smoking_boxes"]) > 0
                    id_missing_positive = evidence["person_visible"] and not evidence["id_card_found"]

                    self.smoking_state.update(smoking_positive, self.name, "smoking",
                                             evidence["max_smoking_conf"], annotated)
                    self.id_state.update(id_missing_positive, self.name, "id_card_missing",
                                         evidence["max_person_conf"], annotated)

                    fps_count += 1
                    now = time.time()
                    fps = fps_count / (now - fps_timer) if now - fps_timer > 0 else 0.0
                    if now - fps_timer >= 5.0:
                        fps_count = 0
                        fps_timer = now

                    new_status = {
                        "camera": self.name,
                        "online": True,
                        "smoking_detected": self.smoking_state.active,
                        "id_card_missing": self.id_state.active,
                        "person_visible": evidence["person_visible"],
                        "id_card_visible": evidence["id_card_found"],
                        "confidence": round(evidence["max_smoking_conf"], 2),
                        "detected_class": evidence["smoking_class"],
                        "fps": round(fps, 1),
                        "latest_alert_id": self._get_latest_alert_id(),
                    }
                    ok_enc, buffer = cv2.imencode(
                        '.jpg', annotated, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
                    if ok_enc:
                        with self._lock:
                            self._latest_jpeg = buffer.tobytes()
                            self._status = new_status
            
            time.sleep(0.03)

        self.online = False
        with self._lock:
            self._status["online"] = False

    def _get_latest_alert_id(self):
        with alerts_lock:
            for alert in alerts:
                if alert.get("camera") == self.name:
                    return alert.get("id", "")
        return ""

    def get_status(self):
        with self._lock:
            return dict(self._status)

    def get_latest_jpeg(self):
        with self._lock:
            return self._latest_jpeg

    def stop(self):
        self._stop.set()


pipelines = {}
def start_pipelines():
    if pipelines:
        return
    for cam_name, src in zip(["classroom", "cafeteria"], CAMERA_SOURCES):
        pipelines[cam_name] = CameraPipeline(cam_name, src)


@app.on_event("startup")
def _startup():
    init_db()
    seed_default_students()
    start_pipelines()


def get_pipeline(camera):
    pipe = pipelines.get(camera)
    if pipe is None:
        raise HTTPException(status_code=404, detail=f"Unknown camera '{camera}'.")
    return pipe


@app.get("/")
def home():
    return {
        "status": "Active",
        "message": "Cognitive Vision AI Backend is running successfully!",
        "cameras": {name: p.online for name, p in pipelines.items()},
    }


@app.get("/live_status")
def live_status(camera: str = "classroom"):
    return get_pipeline(camera).get_status()


@app.get("/cafeteria_status")
def cafeteria_status():
    return pipelines["cafeteria"].get_status()


@app.get("/alerts")
def get_alerts():
    with alerts_lock:
        return {"alerts": list(alerts), "count": len(alerts)}


@app.get("/history/alerts")
def get_history_alerts():
    with alerts_lock:
        return {"history": list(history_alerts), "count": len(history_alerts)}


@app.get("/alert_image/{image_name}")
def alert_image(image_name: str):
    filepath = ALERTS_DIR / image_name
    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(status_code=404, detail="Alert image not found")
    return FileResponse(filepath, media_type="image/jpeg")


@app.post("/admin/process_alert")
def process_alert(req: ProcessAlertRequest):
    target_alert = get_alert_snapshot(req.alert_id)
    if not target_alert:
        target_alert = {
            "id": req.alert_id or f"manual-{int(time.time())}",
            "camera": "classroom",
            "type": "smoking",
            "confidence": 0.95,
            "timestamp_iso": datetime.datetime.now().isoformat(timespec="seconds"),
            "image": "",
        }

    image_path = get_alert_image_path(target_alert)

    with alerts_lock:
        for alert in alerts:
            if alert["id"] == req.alert_id:
                alerts.remove(alert)
                break

    student_id = req.student_id or 1
    student = get_student(student_id=student_id)
    if not student:
        student = {
            "id": 1,
            "name": "Muhammad Yasir Soomro",
            "roll_no": "SE-001",
            "department": "Software Engineering",
            "email": "yasirsoomro468@gmail.com"
        }

    existing_warnings = get_warnings(student_id=student_id)
    warning_count = len(existing_warnings)

    result, error = send_warning(
        student_id,
        req.alert_id,
        target_alert.get("camera", "classroom"),
        req.reason,
        send_email=False,
        send_portal=req.send_portal
    )

    if error:
        print(f"[warning] Database warning entry notice: {error}")

    updated_warnings = get_warnings(student_id=student_id)
    total_warnings = len(updated_warnings)

    email_success = False
    student_email = student.get("email")
    student_name = student.get("name")
    student_roll = student.get("roll_no")
    student_dept = student.get("department", "Software Engineering")

    if req.send_email and student_email:
        subject = f"Official Campus Policy Violation Notice - Warning #{total_warnings}"
        body = (
            f"Dear {student_name},\n\n"
            f"This is an official disciplinary notification from the Cognitive Vision AI Campus Surveillance System regarding a policy violation recorded on campus.\n\n"
            f"--- VIOLATION DETAILS ---\n"
            f"Student Name: {student_name}\n"
            f"Roll Number: {student_roll}\n"
            f"Department: {student_dept}\n"
            f"Violation Type: Smoking detected on campus premises\n"
            f"Location / Camera: {target_alert.get('camera', 'Classroom').capitalize()}\n"
            f"Warning Level: Warning #{total_warnings} issued\n\n"
            f"Please take this as a formal notice to exercise caution and strictly follow university decorum moving forward.\n\n"
            f"Regards,\n"
            f"Campus Administration Office"
        )
        threading.Thread(
            target=send_real_email,
            args=(student_email, subject, body, image_path),
            daemon=True
        ).start()
        email_success = True

    if req.send_portal:
        send_to_lms(
            target_alert.get("camera", "classroom"),
            target_alert.get("type", "smoking"),
            target_alert.get("confidence", 0.0),
            datetime.datetime.now().isoformat(timespec="seconds"),
            image_path,
            student_roll_no=student_roll,
            send_email_notification=False,
        )

    history_record = {
        **target_alert,
        "student": student,
        "reason": req.reason,
        "warning_count_previous": warning_count,
        "warning_count_total": total_warnings,
        "email_sent": email_success,
    }

    with alerts_lock:
        history_alerts.appendleft(history_record)

    return {
        "success": True,
        "student_name": student_name,
        "previous_warnings_count": warning_count,
        "total_warnings_count": total_warnings,
        "email_sent": email_success,
        "message": f"Alert processed for {student_name}. Total warnings: {total_warnings}."
    }


@app.get("/snapshot")
def snapshot(camera: str = "classroom"):
    pipe = get_pipeline(camera)
    jpeg = pipe.get_latest_jpeg()
    if jpeg is None:
        raise HTTPException(status_code=503, detail=f"No frame available for camera '{camera}'.")
    return Response(content=jpeg, media_type="image/jpeg")


def mjpeg_generator(pipe):
    deadline = time.time() + 10
    while pipe.get_latest_jpeg() is None:
        if time.time() > deadline and not pipe.online:
            return
        time.sleep(0.1)

    while True:
        jpeg = pipe.get_latest_jpeg()
        if jpeg is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg + b'\r\n')
        elif not pipe.online:
            break
        time.sleep(0.066)


@app.get("/video_feed")
def video_feed(camera: str = "classroom"):
    pipe = get_pipeline(camera)
    return StreamingResponse(
        mjpeg_generator(pipe),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/cafeteria_feed")
def cafeteria_feed():
    return video_feed(camera="cafeteria")


@app.post("/detect/object")
async def detect_object(file: UploadFile = File(...)):
    if smoking_model is None and id_model is None:
        raise HTTPException(status_code=500, detail="Models not loaded properly")

    contents = await file.read()
    img = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image format")

    evidence, annotated = detect_in_frame(img)

    detections = [
        {"class": cls, "confidence": round(conf, 2), "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)]}
        for (x1, y1, x2, y2, conf, cls) in evidence["smoking_boxes"]
    ]
    if evidence["id_card_found"]:
        detections.append({"class": "ID_Card", "confidence": round(evidence["max_id_conf"], 2), "bbox": []})

    smoking_detected = len(evidence["smoking_boxes"]) > 0
    id_card_missing = evidence["person_visible"] and not evidence["id_card_found"]

    return {
        "success": True,
        "smoking_detected": smoking_detected,
        "id_card_missing": id_card_missing,
        "person_visible": evidence["person_visible"],
        "confidence": round(evidence["max_smoking_conf"], 2),
        "detected_class": evidence["smoking_class"],
        "total_detections": len(detections),
        "detections": detections,
    }


# ---------------- Admin / Student management ----------------
@app.get("/admin/students")
def admin_list_students():
    return {"students": get_students()}


@app.post("/admin/students")
def admin_create_student(student: StudentCreate):
    existing = get_student(roll_no=student.roll_no)
    if existing:
        raise HTTPException(status_code=400, detail="Student with this roll number already exists")
    sid = add_student(student.name, student.roll_no, student.department, student.email)
    return {"success": True, "student_id": sid}


@app.get("/admin/students/{student_id}")
def admin_get_student(student_id: int):
    student = get_student(student_id=student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"student": student}


@app.patch("/admin/students/{student_id}")
def admin_update_student(student_id: int, student: StudentUpdate):
    ok = update_student(
        student_id,
        name=student.name,
        roll_no=student.roll_no,
        department=student.department,
        email=student.email,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"success": True}


@app.post("/admin/send_warning")
def admin_send_warning(req: WarningRequest):
    if not req.send_email and not req.send_portal:
        raise HTTPException(status_code=422, detail="Select Email or Portal delivery")

    student = get_student(student_id=req.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    alert, image_path, evidence_error = resolve_action_evidence(req.alert_id)

    violation_type = alert.get("type", "smoking") if alert else "smoking"
    confidence = alert.get("confidence", 0.0) if alert else 0.0
    camera = alert.get("camera", req.camera) if alert else req.camera

    result, error = send_warning(
        req.student_id,
        req.alert_id,
        camera,
        req.reason,
        send_email=False,
        send_portal=req.send_portal,
    )
    if error:
        raise HTTPException(status_code=404, detail=error)

    warning_id = result.get("warning_id")

    def background_dispatch():
        email_sent = False
        portal_sent = False

        if req.send_email and student.get("email"):
            subject = "Official Campus Policy Violation Notice - Warning"
            body = (
                f"Dear {student.get('name')},\n\n"
                f"This is an official notification regarding a disciplinary violation recorded on campus.\n\n"
                f"--- VIOLATION DETAILS ---\n"
                f"Student Name: {student.get('name')}\n"
                f"Roll Number: {student.get('roll_no')}\n"
                f"Department: {student.get('department', 'Software Engineering')}\n"
                f"Camera / Location: {camera.capitalize()}\n"
                f"Reason / Remarks: {req.reason}\n\n"
                f"Please maintain campus decorum and follow university rules.\n\n"
                f"Regards,\n"
                f"Campus Administration Office"
            )
            email_sent = send_real_email(student.get("email"), subject, body, image_path)

        try:
            portal_result = send_warning_to_lms(
                camera,
                violation_type,
                confidence,
                datetime.datetime.now().isoformat(timespec="seconds"),
                image_path,
                student.get("roll_no"),
                req.reason,
            )
            if isinstance(portal_result, dict):
                portal_sent = portal_result.get("sent", True)
            else:
                portal_sent = True
        except Exception as e:
            print(f"[lms] Failed to send warning to lms: {e}")
            portal_sent = False

        if warning_id:
            update_warning_delivery(warning_id, email_sent, portal_sent)

    threading.Thread(target=background_dispatch, daemon=True).start()

    return {
        **result,
        "success": True,
        "email_sent": req.send_email,
        "portal_sent": req.send_portal,
        "evidence_attached": bool(image_path),
        "message": f"Warning dispatch initiated in background for {student.get('name')}."
    }


@app.post("/admin/issue_chalan")
def admin_issue_chalan(req: ChalanRequest):
    if not req.send_email and not req.send_portal:
        raise HTTPException(status_code=422, detail="Select Email or Portal delivery")

    student = get_student(student_id=req.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    alert, image_path, evidence_error = resolve_action_evidence(req.alert_id)

    camera = alert.get("camera", req.camera) if alert else req.camera
    result, error = issue_chalan(
        req.student_id,
        req.alert_id,
        camera,
        req.reason,
        amount=req.amount,
        send_email=False,
        send_portal=req.send_portal,
    )
    if error:
        raise HTTPException(status_code=404, detail=error)

    chalan_id = result.get("chalan_id")

    def background_chalan_dispatch():
        email_sent = False
        portal_sent = False

        if req.send_email and student.get("email"):
            subject = f"Official University Fine Challan Notice - Rs. {req.amount}"
            body = (
                f"Dear {student.get('name')},\n\n"
                f"An official financial penalty (Challan) has been issued against your account due to a campus policy violation.\n\n"
                f"--- UNIVERSITY CHALLAN STATEMENT ---\n"
                f"Student Name: {student.get('name')}\n"
                f"Roll Number: {student.get('roll_no')}\n"
                f"Department: {student.get('department', 'Software Engineering')}\n"
                f"Violation Reason: {req.reason}\n"
                f"Location / Camera: {camera.capitalize()}\n"
                f"Fine Amount: PKR {req.amount}\n"
                f"Status: Unpaid / Pending\n\n"
                f"Please clear this due amount at the university accounts office or via the student portal.\n\n"
                f"Regards,\n"
                f"Accounts & Disciplinary Department"
            )
            email_sent = send_real_email(student.get("email"), subject, body, image_path)

        try:
            portal_result = send_challan_to_lms(
                camera,
                req.reason,
                req.amount,
                datetime.datetime.now().isoformat(timespec="seconds"),
                image_path,
                student.get("roll_no"),
            )
            if isinstance(portal_result, dict):
                portal_sent = portal_result.get("sent", True)
            else:
                portal_sent = True
        except Exception as e:
            print(f"[lms] Failed to send challan to lms: {e}")
            portal_sent = False

        if chalan_id:
            update_chalan_delivery(chalan_id, email_sent, portal_sent)

    threading.Thread(target=background_chalan_dispatch, daemon=True).start()

    return {
        **result,
        "success": True,
        "email_sent": req.send_email,
        "portal_sent": req.send_portal,
        "evidence_attached": bool(image_path),
        "message": f"Challan dispatch initiated in background for {student.get('name')}."
    }


@app.get("/admin/warnings")
def admin_list_warnings(student_id: int | None = None):
    return {"warnings": get_warnings(student_id)}


@app.get("/admin/chalans")
def admin_list_chalans(student_id: int | None = None):
    return {"chalans": get_chalans(student_id)}


@app.patch("/admin/chalans/{chalan_id}/status")
def admin_update_chalan_status(chalan_id: int, update: ChalanStatusUpdate):
    ok = mark_chalan_paid(chalan_id) if update.status == "paid" else False
    if not ok:
        raise HTTPException(status_code=400, detail="Could not update chalan status")
    return {"success": True}


# ---------------- Student portal APIs ----------------
@app.get("/portal/notifications/{student_id}")
def portal_notifications(student_id: int):
    return {"notifications": get_notifications(student_id), "unread_count": get_unread_count(student_id)}


@app.post("/portal/notifications/{notification_id}/read")
def portal_mark_read(notification_id: int):
    ok = mark_notification_read(notification_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}


@app.get("/portal/student/{roll_no}")
def portal_student_by_roll(roll_no: str):
    student = get_student(roll_no=roll_no)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"student": student}


if __name__ == "__main__":
    import uvicorn
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000)
    finally:
        for p in pipelines.values():
            p.stop()