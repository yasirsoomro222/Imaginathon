# AI-Driven Campus Surveillance & Automated LMS Disciplinary System

An advanced campus AI system integrating YOLOv8 real-time behavior detection with an LMS web portal and a Flutter mobile application. It logs policy infractions with snapshot proof, triggers instant admin alerts, automates student email warnings, and provides an appeal challenge portal alongside a mobile companion app for monitoring.

---

## 🚀 Project Overview

This repository houses a comprehensive, multi-module solution designed to automate campus discipline, attendance, and safety enforcement. By combining computer vision, a robust web-based Learning Management System (LMS), and a mobile interface, the platform minimizes manual supervision overhead and establishes a streamlined automated feedback loop between security cameras and disciplinary records.

---

## 📁 Repository Structure

```text
AI-Hackathon/
├── COGNITIVE VISION AI/        # Computer Vision module (YOLOv8, inference scripts, model weights)
│   ├── models/                # Trained YOLOv8 detection weights (e.g., smoking.pt)
│   ├── inference.py           # Main real-time video processing script
│   └── requirements.txt       # Python dependencies
│
├── LMS/                       # Web portal and backend management system
│   ├── backend/               # Server-side APIs, database connection, alert routes
│   ├── frontend/              # Admin dashboard & student portal UI
│   └── package.json           # Node.js dependencies
│
├── mobile-app/                # Flutter mobile companion application (Campus Guard AI)
│   └── campus_guard_ai/       # Cross-platform mobile source code for real-time alerts & warnings
│
├── .gitignore                 # Excludes sensitive files, virtual environments, and weights
└── README.md                  # Project documentation

```

---

## 🛠️ Modules Breakdown

### 1. Cognitive Vision AI

* **Technology Stack**: Python, YOLOv8, OpenCV, PyTorch.
* **Functionality**: Performs real-time video inference and anomaly detection (such as unauthorized activities or policy violations). Automatically captures snapshot proof upon infraction detection and pushes alerts upstream to the backend database.

### 2. LMS (Learning Management System & Backend)

* **Technology Stack**: Python/Node.js backend, HTML/CSS/Bootstrap frontend templates, Relational Database.
* **Functionality**:
* **Admin Dashboard**: Centralized view for managing student registries, tracking automated attendance logs, and reviewing policy infractions.
* **Automated Warning & Challan System**: Dispatches system-generated warnings and penalty notices directly to student records.
* **Student Portal**: Allows students to view attendance reports, academic details, and file appeals against automated disciplinary logs.



### 3. Campus Guard AI (Mobile App)

* **Technology Stack**: Flutter & Dart.
* **Functionality**: Provides a mobile interface for stakeholders to view live status updates, receive real-time push alerts regarding campus security infractions, and review warnings on the go.

---

## ⚙️ Setup & Installation Instructions

### Prerequisites

* Python 3.10+
* Node.js & npm (for web management modules)
* Flutter SDK (for mobile application development)
* Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/YasirSoomro123/AI-Hackathon.git
cd AI-Hackathon

```

### Step 2: Set Up Cognitive Vision AI

1. Navigate to the vision directory:
```bash
cd "COGNITIVE VISION AI"

```

2. Install dependencies:
```bash
pip install -r requirements.txt

```

3. Place your trained model weights (e.g., `smoking.pt`) inside the `models/` directory.
4. Run inference:
```bash
python inference.py

```


### Step 3: Set Up LMS Backend & Web Portal

1. Navigate to the LMS folder:
```bash
cd ../LMS

```


2. Configure your environment variables using `.env.example` as a template.
3. Install backend dependencies and initialize the database/server.

### Step 4: Run the Mobile Application

1. Navigate to the mobile app directory:
```bash
cd ../mobile-app/campus_guard_ai

```

2. Get packages:
```bash
flutter pub get

```

3. Run the application on an emulator or physical device:
```bash
flutter run

```

---

## 🔐 Security & Configuration

* Sensitive configuration parameters, environment tokens (`.env`), cached compilation files (`__pycache__`, `node_modules`), and heavy model weight binaries (`.pt`, `*.weights`) are untracked via `.gitignore` to maintain repository security and efficiency.
