import base64
import json
import logging
import os
import threading
import urllib.error
import urllib.request
from pathlib import Path

logger = logging.getLogger("lms_integration")

LMS_API_URL = os.environ.get("LMS_API_URL", "http://127.0.0.1:5000")
LMS_API_TOKEN = os.environ.get("LMS_API_TOKEN", "campusguard-secret-token-2026")
LMS_TIMEOUT_SECONDS = 5


def _encode_image(image_path):
    if not image_path or not Path(image_path).is_file():
        return None

    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except OSError as error:
        logger.warning("Failed to read evidence image %s: %s", image_path, error)
        return None


def _post_to_lms(path, payload):
    url = f"{LMS_API_URL.rstrip('/')}{path}"
    headers = {
        "Authorization": f"Bearer {LMS_API_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=LMS_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        try:
            body = json.loads(error.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            body = {}
        return {
            "sent": False,
            "error": body.get("error") or body.get("detail") or f"LMS returned HTTP {error.code}",
        }
    except urllib.error.URLError as error:
        return {"sent": False, "error": f"Could not reach LMS: {error.reason}"}
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        return {"sent": False, "error": f"LMS delivery failed: {error}"}

    if not body.get("success"):
        return {"sent": False, "error": body.get("error") or "LMS rejected the request"}

    return {"sent": True, "response": body}


def send_warning_to_lms(
    camera,
    violation_type,
    confidence,
    timestamp_iso,
    image_path,
    student_roll_no,
    reason,
):
    payload = {
        "camera": camera,
        "violation_type": violation_type,
        "confidence": round(float(confidence), 2),
        "timestamp": timestamp_iso,
        "image_base64": _encode_image(image_path),
        "student_roll_no": student_roll_no,
        "send_email_notification": False,
        "source": "cva_admin",
        "admin_reason": reason,
    }
    return _post_to_lms("/api/detection", payload)


def send_challan_to_lms(camera, reason, amount, timestamp_iso, image_path, student_roll_no):
    payload = {
        "camera": camera,
        "reason": reason,
        "amount": amount,
        "timestamp": timestamp_iso,
        "image_base64": _encode_image(image_path),
        "student_roll_no": student_roll_no,
        "source": "cva_admin",
    }
    return _post_to_lms("/api/challan", payload)


def send_to_lms(
    camera,
    violation_type,
    confidence,
    timestamp_iso,
    image_path,
    student_roll_no=None,
    send_email_notification=True,
):
    """Send a legacy detection alert without blocking its caller."""
    thread = threading.Thread(
        target=_send_to_lms_async,
        args=(
            camera,
            violation_type,
            confidence,
            timestamp_iso,
            image_path,
            student_roll_no,
            send_email_notification,
        ),
        daemon=True,
    )
    thread.start()


def _send_to_lms_async(
    camera,
    violation_type,
    confidence,
    timestamp_iso,
    image_path,
    student_roll_no,
    send_email_notification,
):
    payload = {
        "camera": camera,
        "violation_type": violation_type,
        "confidence": round(float(confidence), 2),
        "timestamp": timestamp_iso,
        "image_base64": _encode_image(image_path),
        "send_email_notification": bool(send_email_notification),
    }
    if student_roll_no:
        payload["student_roll_no"] = student_roll_no

    result = _post_to_lms("/api/detection", payload)
    if result["sent"]:
        logger.info("Legacy alert sent to LMS: %s/%s", camera, violation_type)
    else:
        logger.warning("Legacy alert was not sent to LMS: %s", result["error"])
