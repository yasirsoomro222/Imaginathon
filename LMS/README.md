# University LMS (Learning Management System)

An assumed/approximate university LMS built for a final-year project. The team does not have
access to the real university LMS, so this application models one end-to-end: enrollments,
attendance, assignments, results/GPA, fee challans, warnings and announcements — with
**Student** and **Admin** portals.

A companion project (the main FYP) will later connect to this LMS to push **warnings** and
**fee challans** to students. The `Warning` model already carries `source` (manual/system/api)
and `related_challan_id` fields, and every mutation goes through POST routes, so a REST API
can be layered on without reshaping the data model.

## Features

**Student portal**
- Dashboard: attendance %, semester GPA, unpaid/overdue challans, unread warnings
- Courses and per-course detail (teacher, credit hours, assessments, attendance)
- Attendance with 75% threshold colour coding (red < 75, amber 75–79, green ≥ 80)
- Assignments with file upload (pdf/doc/docx/zip/png/jpg/jpeg/txt, max 16 MB) and
  pending / submitted / graded / overdue states
- Results: per-assessment marks, finalized grades, GPA/CGPA on the HEC scale,
  in-progress courses show "In Progress" instead of 0.00
- Fee challans with status badges and a **printable 3-copy bank challan** (Bank/University/Student)
- Warnings with unread highlighting and deep links to the related challan
- Announcements (pinned first, expired hidden) and profile

**Admin panel**
- Dashboard statistics incl. low-attendance students and bulk warning shortcut
- Students: CRUD, activate/deactivate, password reset, per-student snapshot
- Courses: CRUD, enroll/unenroll students
- Attendance: bulk present/absent grid per course+date, per-course report
- Assignments: create, view submissions, grade with feedback, download files
- Results: assessments per course, bulk marks entry, **finalize course result** (locks GPA)
- Challans: single or bulk issue, mark paid with receipt number, cancel, print
- Warnings: single or multi-student issue, **bulk attendance warnings** for everyone below 75%
- Announcements: CRUD with pin and expiry

**Notifications** — in-app bell badge (unread warning count) plus email. Email sends via SMTP
when configured in `.env`; otherwise it prints `[SIMULATED EMAIL]` to the console so demos work
without credentials.

## Tech Stack

- Python 3.11 / Flask 3, Flask-SQLAlchemy, Flask-Login, Flask-WTF (CSRF), Flask-Mail
- SQLite (`instance/lms.db`)
- Bootstrap 5 + Bootstrap Icons **vendored locally** (`app/static/vendor/`) — no CDN needed,
  so the demo works without internet
- Werkzeug scrypt password hashing

## Setup

```bash
python -m venv venv
venv\Scripts\activate            # Windows
pip install -r requirements.txt

python seed.py --reset           # create demo database (idempotent; --reset wipes and reseeds)
python run.py                    # http://127.0.0.1:5000
```

## Demo Accounts

| Role | Email | Password |
|---|---|---|
| Admin | `admin@university.edu.pk` | `admin123` |
| Student (any) | `aisha.khan@university.edu.pk` … `hamza.ali@university.edu.pk` | `student123` |

Roll numbers are `FA23-BCS-001` … `FA23-BCS-005`. The seeder prints the full credential
table with scenario notes when it finishes.

## Seeded Demo Scenarios

| Roll No | Student | Scenario |
|---|---|---|
| FA23-BCS-001 | Aisha Khan | Top performer — CGPA 3.82 |
| FA23-BCS-002 | Bilal Ahmed | F grade — CGPA 1.93, low attendance, read warning |
| FA23-BCS-003 | Zainab Raza | 62.5% attendance in CS301 — red, debarment risk, critical warnings; 76% in MTH101 — amber; all four assignment states (pending, submitted, graded, overdue) |
| FA23-BCS-004 | Maryam Shah | Overdue challan + unread linked fee warning + due-soon/paid/cancelled challans |
| FA23-BCS-005 | Hamza Ali | Zero state — no records anywhere, no crash |

All seeded dates are generated relative to the run date, so overdue/due-soon/expired states
remain correct whenever the demo is reseeded.

## Email (optional)

Copy `.env.example` to `.env` and fill in SMTP settings (e.g. a Gmail app password):

```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=you@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=you@gmail.com
```

Without SMTP config, `send_email()` prints the message to the server console instead.

## Project Structure

```
run.py                  entry point
seed.py                 idempotent demo data (--reset)
config.py               app configuration
app/
├── __init__.py         app factory, filters, error handlers
├── models.py           13 models + grade/GPA/attendance logic
├── mail_utils.py       send_email() — SMTP or console simulation
├── auth.py             login/logout/change password
├── student.py          student blueprint
├── admin.py            admin blueprint
├── templates/          Jinja2 templates (auth/student/admin/email/errors)
└── static/             app css/js + vendored Bootstrap
uploads/                assignment submissions (uuid filenames)
instance/lms.db         SQLite database
```

## Notable Design Decisions

- **GPA only from finalized courses** — `Assessment` (weightage) + `Mark` + `CourseResult`
  tables; an unfinalized course shows "In Progress" instead of polluting GPA with partial marks.
- **Overdue is computed, never stored** — `Challan.is_overdue` = unpaid and due date passed,
  so seeded data stays correct forever without cron jobs.
- **Zero state ≠ 0%** — attendance percentage is `None` when no records exist, rendering
  "No records" instead of a false 0%/DEBARRED.
- **Security** — CSRF on every form, uuid upload filenames, extension whitelist + 16 MB limit,
  auth-checked downloads via `send_from_directory`, `PRAGMA foreign_keys=ON`, POST-only mutations.

## Out of Scope (future work)

- REST API endpoints for the main FYP integration (the model fields are ready)
- Teacher role, payment gateway, PDF generation (printable HTML page is sufficient), pagination
  at larger scale
