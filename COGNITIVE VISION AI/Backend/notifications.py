import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except Exception:
    pass

from database import (
    add_warning,
    add_chalan,
    get_student,
    get_warnings,
    update_chalan_status,
)

# ---------------- Email config ----------------
# Set these via environment variables or edit directly.
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
UNIVERSITY_NAME = os.getenv("UNIVERSITY_NAME", "Air Uni")


def _send_email(to_email, subject, html_body):
    if not SMTP_USER or not SMTP_PASS:
        print("[email] SMTP credentials not configured; email not sent.")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{UNIVERSITY_NAME} <{FROM_EMAIL}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(FROM_EMAIL, [to_email], msg.as_string())
        print(f"[email] sent to {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"[email] failed to send to {to_email}: {e}")
        return False


def warning_email_body(student_name, roll_no, department, camera, reason, university):
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #c0392b;">Smoking Warning - {university}</h2>
        <p>Dear <strong>{student_name}</strong>,</p>
        <p>You have been observed violating the university no-smoking policy.</p>
        <ul>
          <li><strong>Roll No:</strong> {roll_no}</li>
          <li><strong>Department:</strong> {department}</li>
          <li><strong>Location:</strong> {camera}</li>
          <li><strong>Reason:</strong> {reason}</li>
          <li><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</li>
        </ul>
        <p>Please refrain from smoking on campus. Repeated violations will result in a fine.</p>
        <br>
        <p>Regards,<br><strong>{university} Administration</strong></p>
      </body>
    </html>
    """


def chalan_email_body(student_name, roll_no, department, amount, reason, due_date, university):
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #c0392b;">Fine / Chalan Issued - {university}</h2>
        <p>Dear <strong>{student_name}</strong>,</p>
        <p>A fine has been issued against you for repeated violation of the university no-smoking policy.</p>
        <ul>
          <li><strong>Roll No:</strong> {roll_no}</li>
          <li><strong>Department:</strong> {department}</li>
          <li><strong>Amount:</strong> Rs. {amount}</li>
          <li><strong>Reason:</strong> {reason}</li>
          <li><strong>Issued On:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</li>
          <li><strong>Due Date:</strong> {due_date}</li>
        </ul>
        <p>Please pay the fine within <strong>7 days</strong>. Failure to pay may result in further disciplinary action.</p>
        <br>
        <p>Regards,<br><strong>{university} Administration</strong></p>
      </body>
    </html>
    """


def send_warning(student_id, alert_id, camera, reason, send_email=False, send_portal=False):
    student = get_student(student_id=student_id)
    if not student:
        return None, "Student not found"

    existing_warnings = get_warnings(student_id=student_id)
    warning_number = len(existing_warnings) + 1

    message = (
        f"Warning #{warning_number}: Smoking detected at {camera}. Reason: {reason}. "
        f"Previous warnings: {len(existing_warnings)}. "
        "Repeated violation will result in a fine."
    )

    email_ok = False
    if send_email and student.get("email"):
        subject = f"Smoking Warning - {UNIVERSITY_NAME}"
        body = warning_email_body(
            student["name"], student["roll_no"], student.get("department", ""),
            camera, reason, UNIVERSITY_NAME,
        )
        email_ok = _send_email(student["email"], subject, body)

    warning_id = add_warning(
        student_id,
        alert_id,
        camera,
        message,
        sent_email=1 if email_ok else 0,
        sent_portal=1 if send_portal else 0,
    )

    return {
        "warning_id": warning_id,
        "sent_email": email_ok,
        "sent_portal": send_portal,
    }, None


def issue_chalan(student_id, alert_id, camera, reason, amount=5000, send_email=False, send_portal=False):
    student = get_student(student_id=student_id)
    if not student:
        return None, "Student not found"

    existing_warnings = get_warnings(student_id=student_id)
    due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    full_reason = (
        f"Repeated smoking violation at {camera}. {reason} "
        f"Total prior warnings: {len(existing_warnings)}."
    )

    email_ok = False
    if send_email and student.get("email"):
        subject = f"Fine / Chalan Issued - {UNIVERSITY_NAME}"
        body = chalan_email_body(
            student["name"], student["roll_no"], student.get("department", ""),
            amount, full_reason, due_date, UNIVERSITY_NAME,
        )
        email_ok = _send_email(student["email"], subject, body)

    chalan_id = add_chalan(
        student_id,
        alert_id,
        amount,
        full_reason,
        due_date,
        sent_email=1 if email_ok else 0,
        sent_portal=1 if send_portal else 0,
    )

    return {
        "chalan_id": chalan_id,
        "amount": amount,
        "due_date": due_date,
        "sent_email": email_ok,
        "sent_portal": send_portal,
    }, None


def mark_chalan_paid(chalan_id):
    return update_chalan_status(chalan_id, "paid")
