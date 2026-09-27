import os
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "campus_guard.db"

_db_lock = threading.Lock()


def _connect():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _db_lock, _connect() as conn:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                roll_no TEXT UNIQUE NOT NULL,
                department TEXT,
                email TEXT,
                warnings_count INTEGER DEFAULT 0,
                chalans_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                alert_id TEXT,
                camera TEXT,
                message TEXT NOT NULL,
                sent_email INTEGER DEFAULT 0,
                sent_portal INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS chalans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                alert_id TEXT,
                amount INTEGER DEFAULT 5000,
                reason TEXT NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT DEFAULT 'unpaid',
                sent_email INTEGER DEFAULT 0,
                sent_portal INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                reference_id INTEGER,
                reference_type TEXT,
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        """)

        conn.commit()


def row_to_dict(row):
    return {k: row[k] for k in row.keys()}


# ---------------- Students ----------------
def get_students():
    with _db_lock, _connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM students ORDER BY created_at DESC")
        return [row_to_dict(r) for r in cur.fetchall()]


def get_student(student_id=None, roll_no=None):
    with _db_lock, _connect() as conn:
        cur = conn.cursor()
        if student_id is not None:
            cur.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        elif roll_no is not None:
            cur.execute("SELECT * FROM students WHERE roll_no = ?", (roll_no,))
        else:
            return None
        row = cur.fetchone()
        return row_to_dict(row) if row else None


def add_student(name, roll_no, department, email):
    with _db_lock, _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO students (name, roll_no, department, email) VALUES (?, ?, ?, ?)",
            (name, roll_no, department, email),
        )
        conn.commit()
        return cur.lastrowid


def update_student(student_id, name=None, roll_no=None, department=None, email=None):
    with _db_lock, _connect() as conn:
        cur = conn.cursor()
        fields = []
        values = []
        if name is not None:
            fields.append("name = ?")
            values.append(name)
        if roll_no is not None:
            fields.append("roll_no = ?")
            values.append(roll_no)
        if department is not None:
            fields.append("department = ?")
            values.append(department)
        if email is not None:
            fields.append("email = ?")
            values.append(email)
        if not fields:
            return False
        values.append(student_id)
        cur.execute(f"UPDATE students SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
        return cur.rowcount > 0


def increment_warnings(student_id):
    with _db_lock, _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE students SET warnings_count = warnings_count + 1 WHERE id = ?",
            (student_id,),
        )
        conn.commit()


def increment_chalans(student_id):
    with _db_lock, _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE students SET chalans_count = chalans_count + 1 WHERE id = ?",
            (student_id,),
        )
        conn.commit()


# ---------------- Warnings ----------------
def add_warning(student_id, alert_id, camera, message, sent_email=0, sent_portal=0):
    with _db_lock, _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO warnings (student_id, alert_id, camera, message, sent_email, sent_portal) VALUES (?, ?, ?, ?, ?, ?)",
            (student_id, alert_id, camera, message, sent_email, sent_portal),
        )
        warning_id = cur.lastrowid
        conn.commit()
    increment_warnings(student_id)
    if sent_portal:
        add_notification(
            student_id,
            "warning",
            "Smoking Warning",
            message,
            reference_id=warning_id,
            reference_type="warning",
        )
    return warning_id


def update_warning_delivery(warning_id, sent_email, sent_portal):
    with _db_lock, _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE warnings SET sent_email = ?, sent_portal = ? WHERE id = ?",
            (int(bool(sent_email)), int(bool(sent_portal)), warning_id),
        )
        conn.commit()
        return cur.rowcount > 0


def get_warnings(student_id=None):
    with _db_lock, _connect() as conn:
        cur = conn.cursor()
        if student_id is not None:
            cur.execute(
                """
                SELECT w.*, s.name as student_name, s.roll_no, s.department
                FROM warnings w
                JOIN students s ON w.student_id = s.id
                WHERE w.student_id = ?
                ORDER BY w.created_at DESC
                """,
                (student_id,),
            )
        else:
            cur.execute(
                """
                SELECT w.*, s.name as student_name, s.roll_no, s.department
                FROM warnings w
                JOIN students s ON w.student_id = s.id
                ORDER BY w.created_at DESC
                """
            )
        return [row_to_dict(r) for r in cur.fetchall()]


# ---------------- Chalans ----------------
def add_chalan(student_id, alert_id, amount, reason, due_date, sent_email=0, sent_portal=0):
    with _db_lock, _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO chalans (student_id, alert_id, amount, reason, due_date, sent_email, sent_portal) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (student_id, alert_id, amount, reason, due_date, sent_email, sent_portal),
        )
        chalan_id = cur.lastrowid
        conn.commit()
    increment_chalans(student_id)
    if sent_portal:
        message = (
            f"A fine of Rs. {amount} has been issued by Air Uni. "
            f"Reason: {reason}. Due date: {due_date}. Please pay within 7 days."
        )
        add_notification(
            student_id,
            "chalan",
            "Fine / Chalan Issued",
            message,
            reference_id=chalan_id,
            reference_type="chalan",
        )
    return chalan_id


def update_chalan_delivery(chalan_id, sent_email, sent_portal):
    with _db_lock, _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE chalans SET sent_email = ?, sent_portal = ? WHERE id = ?",
            (int(bool(sent_email)), int(bool(sent_portal)), chalan_id),
        )
        conn.commit()
        return cur.rowcount > 0


def get_chalans(student_id=None):
    with _db_lock, _connect() as conn:
        cur = conn.cursor()
        if student_id is not None:
            cur.execute(
                """
                SELECT c.*, s.name as student_name, s.roll_no, s.department
                FROM chalans c
                JOIN students s ON c.student_id = s.id
                WHERE c.student_id = ?
                ORDER BY c.created_at DESC
                """,
                (student_id,),
            )
        else:
            cur.execute(
                """
                SELECT c.*, s.name as student_name, s.roll_no, s.department
                FROM chalans c
                JOIN students s ON c.student_id = s.id
                ORDER BY c.created_at DESC
                """
            )
        return [row_to_dict(r) for r in cur.fetchall()]


def update_chalan_status(chalan_id, status):
    with _db_lock, _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE chalans SET status = ? WHERE id = ?",
            (status, chalan_id),
        )
        conn.commit()
        return cur.rowcount > 0


# ---------------- Notifications ----------------
def add_notification(student_id, ntype, title, message, reference_id=None, reference_type=None):
    with _db_lock, _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO notifications (student_id, type, title, message, reference_id, reference_type)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (student_id, ntype, title, message, reference_id, reference_type),
        )
        conn.commit()
        return cur.lastrowid


def get_notifications(student_id):
    with _db_lock, _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM notifications WHERE student_id = ? ORDER BY created_at DESC",
            (student_id,),
        )
        return [row_to_dict(r) for r in cur.fetchall()]


def mark_notification_read(notification_id):
    with _db_lock, _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ?",
            (notification_id,),
        )
        conn.commit()
        return cur.rowcount > 0


def get_unread_count(student_id):
    with _db_lock, _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) as cnt FROM notifications WHERE student_id = ? AND is_read = 0",
            (student_id,),
        )
        row = cur.fetchone()
        return row["cnt"] if row else 0
