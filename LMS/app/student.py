import os
import uuid
from datetime import date

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required

from app import db
from app.auth import student_required
from app.models import Announcement, Assignment, Challan, Submission, Warning

student_bp = Blueprint("student", __name__, url_prefix="/student")


def _current_student():
    if not current_user.is_authenticated or current_user.role != "student":
        abort(403)
    return current_user.student


@student_bp.route("/dashboard")
@login_required
@student_required
def dashboard():
    student = current_user.student
    enrollments = student.enrollments
    finalized = student.finalized_results
    announcements = (
        Announcement.query.filter(
            db.or_(
                Announcement.expires_on.is_(None),
                Announcement.expires_on >= date.today(),
            )
        )
        .order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())
        .limit(5)
        .all()
    )
    return render_template(
        "student/dashboard.html",
        student=student,
        enrollments=enrollments,
        finalized=finalized,
        announcements=announcements,
        upcoming=Assignment.query.filter(
            Assignment.course_id.in_([e.course_id for e in enrollments] or [0]),
            Assignment.due_date >= db.func.now(),
        )
        .order_by(Assignment.due_date)
        .limit(5)
        .all(),
    )


@student_bp.route("/courses")
@login_required
@student_required
def courses():
    student = current_user.student
    return render_template("student/courses.html", enrollments=student.enrollments)


@student_bp.route("/courses/<int:course_id>")
@login_required
@student_required
def course_detail(course_id):
    enrollment = next(
        (e for e in current_user.student.enrollments if e.course_id == course_id), None
    )
    if enrollment is None:
        abort(404)
    return render_template("student/course_detail.html", enrollment=enrollment)


@student_bp.route("/attendance")
@login_required
@student_required
def attendance():
    student = current_user.student
    return render_template("student/attendance.html", enrollments=student.enrollments)


@student_bp.route("/assignments")
@login_required
@student_required
def assignments():
    student = current_user.student
    course_ids = [e.course_id for e in student.enrollments] or [0]
    items = (
        Assignment.query.filter(Assignment.course_id.in_(course_ids))
        .order_by(Assignment.due_date.desc())
        .all()
    )
    submissions = {s.assignment_id: s for s in student.submissions}
    return render_template("student/assignments.html", items=items, submissions=submissions)


@student_bp.route("/assignments/<int:assignment_id>")
@login_required
@student_required
def assignment_detail(assignment_id):
    student = current_user.student
    assignment = Assignment.query.get_or_404(assignment_id)
    if assignment.course_id not in [e.course_id for e in student.enrollments]:
        abort(403)
    submission = next(
        (s for s in student.submissions if s.assignment_id == assignment_id), None
    )
    return render_template(
        "student/assignment_detail.html",
        assignment=assignment,
        submission=submission,
    )


def _allowed_file(filename):
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    return ext in current_app.config["ALLOWED_EXTENSIONS"] and ext != ""


@student_bp.route("/assignments/<int:assignment_id>/submit", methods=["POST"])
@login_required
@student_required
def submit_assignment(assignment_id):
    student = current_user.student
    assignment = Assignment.query.get_or_404(assignment_id)
    if assignment.course_id not in [e.course_id for e in student.enrollments]:
        abort(403)

    file = request.files.get("file")
    if file is None or file.filename == "":
        flash("Please choose a file to upload.", "warning")
        return redirect(url_for("student.assignment_detail", assignment_id=assignment_id))
    if not _allowed_file(file.filename):
        flash(
            "File type not allowed. Allowed: pdf, doc, docx, zip, png, jpg, jpeg, txt.",
            "danger",
        )
        return redirect(url_for("student.assignment_detail", assignment_id=assignment_id))

    existing = next(
        (s for s in student.submissions if s.assignment_id == assignment_id), None
    )

    ext = os.path.splitext(file.filename)[1].lower()
    stored = f"{uuid.uuid4().hex}{ext}"
    upload_path = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_path, exist_ok=True)
    file.save(os.path.join(upload_path, stored))

    if existing is None:
        submission = Submission(
            assignment_id=assignment_id,
            student_id=student.id,
            stored_filename=stored,
            original_filename=os.path.basename(file.filename)[:255],
        )
        db.session.add(submission)
    else:
        old_file = existing.stored_filename
        existing.stored_filename = stored
        existing.original_filename = os.path.basename(file.filename)[:255]
        existing.marks = None
        existing.feedback = None
        submission = existing
        if old_file:
            old_path = os.path.join(upload_path, old_file)
            if os.path.exists(old_path):
                os.remove(old_path)

    db.session.commit()
    flash("Assignment submitted successfully.", "success")
    return redirect(url_for("student.assignment_detail", assignment_id=assignment_id))


@student_bp.route("/submissions/<int:submission_id>/download")
@login_required
@student_required
def download_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    if submission.student_id != current_user.student.id and current_user.role != "admin":
        abort(403)
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        submission.stored_filename,
        as_attachment=True,
        download_name=submission.original_filename,
    )


@student_bp.route("/results")
@login_required
@student_required
def results():
    student = current_user.student
    return render_template("student/results.html", enrollments=student.enrollments)


@student_bp.route("/challans")
@login_required
@student_required
def challans():
    student = current_user.student
    items = sorted(student.challans, key=lambda c: c.issue_date, reverse=True)
    return render_template("student/challans.html", challans=items)


@student_bp.route("/challans/<int:challan_id>")
@login_required
@student_required
def challan_detail(challan_id):
    challan = Challan.query.get_or_404(challan_id)
    if challan.student_id != current_user.student.id:
        abort(403)
    return render_template("student/challan_detail.html", challan=challan)


@student_bp.route("/challans/<int:challan_id>/print")
@login_required
@student_required
def challan_print(challan_id):
    challan = Challan.query.get_or_404(challan_id)
    if challan.student_id != current_user.student.id:
        abort(403)
    return render_template("student/challan_print.html", challan=challan)


@student_bp.route("/warnings")
@login_required
@student_required
def warnings():
    student = current_user.student
    items = sorted(student.warnings, key=lambda w: w.created_at, reverse=True)
    return render_template("student/warnings.html", warnings=items)


@student_bp.route("/warnings/<int:warning_id>")
@login_required
@student_required
def warning_detail(warning_id):
    warning = Warning.query.get_or_404(warning_id)
    if warning.student_id != current_user.student.id:
        abort(403)
    if not warning.is_read:
        warning.is_read = True
        warning.read_at = db.func.now()
        db.session.commit()
    return render_template("student/warning_detail.html", warning=warning)


@student_bp.route("/warnings/read-all", methods=["POST"])
@login_required
@student_required
def warnings_read_all():
    student = current_user.student
    unread = [w for w in student.warnings if not w.is_read]
    for w in unread:
        w.is_read = True
        w.read_at = db.func.now()
    if unread:
        db.session.commit()
        flash(f"{len(unread)} warning(s) marked as read.", "success")
    return redirect(url_for("student.warnings"))


@student_bp.route("/announcements")
@login_required
@student_required
def announcements():
    items = (
        Announcement.query.filter(
            db.or_(
                Announcement.expires_on.is_(None),
                Announcement.expires_on >= date.today(),
            )
        )
        .order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())
        .all()
    )
    return render_template("student/announcements.html", announcements=items)


@student_bp.route("/profile", methods=["GET", "POST"])
@login_required
@student_required
def profile():
    student = current_user.student
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        student.phone = phone or None
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("student.profile"))
    return render_template("student/profile.html", student=student)
