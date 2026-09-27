# CampusGuard AI — Smart Campus Surveillance

AI-powered campus monitoring system that detects smoking and ID card violations from live CCTV cameras, sends real-time alerts to the admin portal / mobile app, and allows admins to issue warnings or fines (chalans) to students.

## Features

- **Live Smoking Detection** — YOLOv8 model detects cigarette / vape near a person's face/mouth region.
- **ID Card Detection** — Checks whether a visible person is wearing an ID card.
- **Dual Camera Support** — Classroom + Cafeteria streams.
- **Real-time Alerts** — Alert screenshots saved automatically.
- **Admin Web Portal** — Modern dark UI to view cameras, alerts, students, warnings and chalans.
- **Admin Actions** — Send warnings via Email / Portal / Both; issue Rs. 5000 chalans with 7-day deadline.
- **Mobile App** — Flutter app for live cameras, detection alerts, and student notifications.

## Project Structure

```
COGNITIVE VISION AI/
├── Backend/                # FastAPI server (main entry point)
│   ├── main.py             # Detection pipelines + REST API
│   ├── database.py         # SQLite students / warnings / chalans / notifications
│   ├── notifications.py    # Email + portal notification service
│   ├── id_card.pt          # YOLOv8 ID card model
│   ├── smoking.pt          # YOLOv8 smoking model
│   └── yolov8n.pt          # YOLOv8 person detector
├── Frontend/               # Web admin portal (HTML/CSS/JS)
│   ├── index.html
│   ├── styles.css
│   └── admin.js
├── mobile-app/             # Flutter admin / student app
│   └── campus_guard_ai/
├── AI Engine/              # Older agents (deprecated; active logic is in Backend/main.py)
└── smoking-datasets/       # Training data
```

## Quick Start

### 1. Backend

```bash
cd "COGNITIVE VISION AI"
venv\Scripts\python.exe -m pip install -r "AI Engine\requirements.txt"
venv\Scripts\python.exe Backend\main.py
```

Backend runs at `http://127.0.0.1:8000`.

### 2. Web Admin Portal

Open `Frontend/index.html` in a browser, or serve it with any static server:

```bash
cd Frontend
python -m http.server 3000
```

Then visit `http://localhost:3000`.

### 3. Mobile App

```bash
cd "mobile-app\campus_guard_ai"
flutter pub get
flutter run -d chrome      # or your connected Android/iOS device
```

> For Android emulator use `http://10.0.2.2:8000`. For a real device use your PC's LAN IP and update `ApiService.baseUrl`.

## Email Setup (Required for email warnings/chalans)

Edit `Backend/notifications.py` or set environment variables:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
FROM_EMAIL=your-email@gmail.com
UNIVERSITY_NAME=Air Uni
```

For Gmail you must generate an **App Password** (not your regular password).

## Important Notes on Accuracy

- The current `id_card.pt` model contains a `smoking` class because it was trained on mixed data. The backend now filters out non-ID classes, but for true high accuracy the model should be retrained using **only** `id-card` images.
- The `smoking-datasets/id_card/` folder is empty. Populate it with proper labels before retraining.
- The backend applies strong post-processing filters (size, aspect ratio, upper-body position, person-zone checks) to reduce false positives.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health + camera status |
| `/video_feed?camera=classroom` | GET | MJPEG live stream |
| `/live_status?camera=classroom` | GET | Current detection status |
| `/alerts` | GET | Recent alerts with screenshot names |
| `/alert_image/{name}` | GET | Alert screenshot image |
| `/detect/object` | POST | Run detection on uploaded image |
| `/admin/students` | GET/POST | List / add students |
| `/admin/send_warning` | POST | Send warning (email/portal/both) |
| `/admin/issue_chalan` | POST | Issue fine / chalan |
| `/admin/warnings` | GET | List warnings |
| `/admin/chalans` | GET | List chalans |
| `/portal/notifications/{student_id}` | GET | Student notifications |

## Authors

CampusGuard AI — University Project
