import base64
import os
import uuid
from datetime import date, datetime, timedelta
from functools import wraps

from flask import Blueprint, current_app, jsonify, request

from app import db

api_bp = Blueprint("api", __name__, url_prefix="/api")



def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "")
        if token.startswith("Bearer "):
            token = token[7:]
        if not token or token != current_app.config["API_KEY"]:
            return jsonify({"success": False, "error": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return decorated


def _save_detection_image(image_base64):
    if not image_base64:
        return None

    try:
        image_bytes = base64.b64decode(image_base64)
        image_filename = f"{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(current_app.config["DETECTION_IMAGE_FOLDER"], image_filename)
        with open(filepath, "wb") as image_file:
            image_file.write(image_bytes)
        return image_filename
    except Exception as error:
        current_app.logger.error("Failed to save detection image: %s", error)
        return None


def _next_challan_no():
    from app.models import Challan

    prefix = f"CH-{date.today().strftime('%Y%m')}-"
    last = (
        Challan.query.filter(Challan.challan_no.like(prefix + "%"))
        .order_by(Challan.challan_no.desc())
        .first()
    )
    sequence = int(last.challan_no.split("-")[-1]) + 1 if last else 1
    return f"{prefix}{sequence:04d}"


@api_bp.route("/detection", methods=["POST"])
@require_api_key
def receive_detection():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "JSON body required"}), 400

    camera = data.get("camera")
    violation_type = data.get("violation_type")
    confidence = data.get("confidence")
    timestamp_str = data.get("timestamp")
    image_base64 = data.get("image_base64")
    send_email_notification = data.get("send_email_notification", True)
    source = data.get("source")
    admin_reason = str(data.get("admin_reason") or "").strip()

    if not camera or not violation_type:
        return jsonify({"success": False, "error": "camera and violation_type are required"}), 400

    if confidence is None:
        confidence = 0.0

    try:
        detected_at = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()
    except (ValueError, TypeError):
        detected_at = datetime.now()

    from app.models import PendingAlert, Student, Warning

    student_roll_no = str(data.get("student_roll_no") or "").strip()
    student = Student.query.filter_by(roll_no=student_roll_no).first() if student_roll_no else None

    if source == "cva_admin" and not student:
        return jsonify({"success": False, "error": "Student roll number was not found in LMS"}), 404

    image_filename = _save_detection_image(image_base64)

    if student:
        violation_labels = {
            "smoking": "Smoking Violation",
            "id_card_missing": "ID Card Missing",
        }
        label = violation_labels.get(violation_type, violation_type.replace("_", " ").title())
        title = f"{label} — {camera.title()} Camera"
        if admin_reason:
            message = (
                f"Disciplinary warning issued by Campus Administration:\n\n"
                f"Type: {label}\n"
                f"Camera: {camera.title()}\n"
                f"Reason: {admin_reason}\n"
                f"Detected at: {detected_at.strftime('%d %b %Y, %I:%M %p')}"
            )
        else:
            message = (
                f"Violation detected by CampusGuard AI:\n\n"
                f"Type: {label}\n"
                f"Camera: {camera.title()}\n"
                f"Confidence: {round(float(confidence) * 100)}%\n"
                f"Detected at: {detected_at.strftime('%d %b %Y, %I:%M %p')}\n\n"
                f"This violation was automatically detected by the campus surveillance system."
            )

        warning = Warning(
            student_id=student.id,
            type="disciplinary",
            severity="warning",
            title=title,
            message=message,
            source="api",
            image_filename=image_filename,
        )
        db.session.add(warning)
        db.session.commit()

        if send_email_notification:
            try:
                from app.mail_utils import send_email
                from flask import render_template
                image_path = (
                    os.path.join(current_app.config["DETECTION_IMAGE_FOLDER"], image_filename)
                    if image_filename
                    else None
                )
                send_email(
                    student.user.email,
                    f"Warning: {title}",
                    render_template("email/warning.html", warning=warning),
                    attachment_path=image_path,
                )
            except Exception as error:
                current_app.logger.warning("Email failed for auto-warning: %s", error)

        return jsonify({"success": True, "warning_id": warning.id, "student": student_roll_no}), 201

    alert = PendingAlert(
        camera=camera,
        violation_type=violation_type,
        confidence=round(float(confidence), 2),
        detected_at=detected_at,
        image_filename=image_filename,
        status="pending",
    )
    db.session.add(alert)
    db.session.commit()

    return jsonify({"success": True, "alert_id": alert.id}), 201


@api_bp.route("/challan", methods=["POST"])
@require_api_key
def receive_challan():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "JSON body required"}), 400

    student_roll_no = str(data.get("student_roll_no") or "").strip()
    reason = str(data.get("reason") or "").strip()
    camera = str(data.get("camera") or "classroom").strip()

    try:
        amount = round(float(data.get("amount")), 2)
    except (TypeError, ValueError):
        amount = 0

    if not student_roll_no or not reason or amount <= 0:
        return jsonify({"success": False, "error": "student_roll_no, reason, and a positive amount are required"}), 400

    from app.models import Challan, Student

    student = Student.query.filter_by(roll_no=student_roll_no).first()
    if not student:
        return jsonify({"success": False, "error": "Student roll number was not found in LMS"}), 404

    image_filename = _save_detection_image(data.get("image_base64"))
    challan = Challan(
        student_id=student.id,
        challan_no=_next_challan_no(),
        fee_type="Disciplinary Fine",
        description=f"Camera: {camera.title()}. Reason: {reason}"[:200],
        amount=amount,
        due_date=date.today() + timedelta(days=7),
    )
    db.session.add(challan)
    db.session.commit()

    return jsonify({
        "success": True,
        "challan_id": challan.id,
        "challan_no": challan.challan_no,
        "evidence_image": image_filename,
    }), 201


@api_bp.route("/pending-alerts", methods=["GET"])
@require_api_key
def list_pending_alerts():
    from app.models import PendingAlert

    alerts = PendingAlert.query.filter_by(status="pending").order_by(PendingAlert.created_at.desc()).all()
    return jsonify({
        "alerts": [
            {
                "id": alert.id,
                "camera": alert.camera,
                "violation_type": alert.violation_type,
                "confidence": alert.confidence,
                "detected_at": alert.detected_at.isoformat() if alert.detected_at else None,
                "image_filename": alert.image_filename,
                "status": alert.status,
            }
            for alert in alerts
        ],
        "count": len(alerts),
    })
