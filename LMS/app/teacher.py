from datetime import date, datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db, csrf
from app.models import (
    Assessment,
    Assignment,
    Attendance,
    Course,
    CourseResult,
    Enrollment,
    Mark,
    Submission,
    Teacher,
    grade_for,
)

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")


@teacher_bp.before_request
@login_required
def _require_teacher():
    if not current_user.is_authenticated or current_user.role != "teacher":
        abort(403)


@teacher_bp.route("/dashboard")
def dashboard():
    teacher = current_user.teacher
    courses = Course.query.filter_by(teacher_id=teacher.id).all()
    total_students = sum(len(c.enrollments) for c in courses)
    pending_assignments = [a for c in courses for a in c.assignments if not a.is_past_due]
    ungraded_submissions = sum(
        1 for c in courses for a in c.assignments for s in a.submissions if not s.is_graded
    )

    return render_template(
        "teacher/dashboard.html",
        teacher=teacher,
        courses=courses,
        total_students=total_students,
        pending_assignments=len(pending_assignments),
        ungraded_submissions=ungraded_submissions,
    )


@teacher_bp.route("/courses")
def courses():
    teacher = current_user.teacher
    courses_list = Course.query.filter_by(teacher_id=teacher.id).order_by(Course.semester, Course.code).all()
    return render_template("teacher/courses.html", courses=courses_list)


@teacher_bp.route("/courses/<int:course_id>")
def course_detail(course_id):
    teacher = current_user.teacher
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != teacher.id:
        abort(403)

    enrollments = sorted(course.enrollments, key=lambda e: e.student.roll_no)
    return render_template("teacher/course_detail.html", course=course, enrollments=enrollments)


@teacher_bp.route("/attendance", methods=["GET", "POST"])
@csrf.exempt
def attendance_select():
    teacher = current_user.teacher
    courses_list = Course.query.filter_by(teacher_id=teacher.id).order_by(Course.code).all()

    if request.method == "POST":
        course_id = request.form.get("course_id", type=int)
        att_date = request.form.get("date")
        if course_id and att_date:
            return redirect(
                url_for("teacher.attendance_mark", course_id=course_id, date_str=att_date)
            )
        flash("Please select a course and a date.", "warning")

    return render_template(
        "teacher/attendance_select.html",
        courses=courses_list,
        default_date=date.today().isoformat(),
    )


@teacher_bp.route("/attendance/<int:course_id>/<date_str>", methods=["GET", "POST"])
@csrf.exempt
def attendance_mark(course_id, date_str):
    teacher = current_user.teacher
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != teacher.id:
        abort(403)

    try:
        att_date = date.fromisoformat(date_str)
    except ValueError:
        abort(404)

    enrollments = sorted(course.enrollments, key=lambda e: e.student.roll_no)
    existing = {
        a.enrollment_id: a.status
        for a in Attendance.query.filter_by(date=att_date).join(Enrollment).filter(Enrollment.course_id == course.id)
    }

    if request.method == "POST":
        for e in enrollments:
            status = request.form.get(f"status_{e.id}")
            if status not in ("present", "absent", "late", "excused"):
                continue
            record = Attendance.query.filter_by(enrollment_id=e.id, date=att_date).first()
            if record:
                record.status = status
            else:
                db.session.add(Attendance(enrollment_id=e.id, date=att_date, status=status))
        db.session.commit()
        flash(f"Attendance saved for {course.code} on {att_date.strftime('%d %b %Y')}.", "success")
        return redirect(url_for("teacher.attendance_report", course_id=course.id))

    statuses = ["present", "absent", "late", "excused"]
    return render_template(
        "teacher/attendance_mark.html",
        course=course,
        att_date=att_date,
        enrollments=enrollments,
        existing=existing,
        statuses=statuses,
    )


@teacher_bp.route("/attendance/report/<int:course_id>")
def attendance_report(course_id):
    teacher = current_user.teacher
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != teacher.id:
        abort(403)

    enrollments = sorted(course.enrollments, key=lambda e: e.student.roll_no)
    return render_template("teacher/attendance_report.html", course=course, enrollments=enrollments)


@teacher_bp.route("/assignments")
def assignments():
    teacher = current_user.teacher
    courses_list = Course.query.filter_by(teacher_id=teacher.id).all()
    course_ids = [c.id for c in courses_list]
    items = Assignment.query.filter(Assignment.course_id.in_(course_ids)).order_by(Assignment.due_date.desc()).all()
    return render_template("teacher/assignments.html", assignments=items)


@teacher_bp.route("/assignments/new", methods=["GET", "POST"])
@teacher_bp.route("/assignments/<int:assignment_id>/edit", methods=["GET", "POST"])
@csrf.exempt
def assignment_form(assignment_id=None):
    teacher = current_user.teacher
    courses_list = Course.query.filter_by(teacher_id=teacher.id).order_by(Course.code).all()
    assignment = Assignment.query.get_or_404(assignment_id) if assignment_id else None

    if assignment and assignment.course.teacher_id != teacher.id:
        abort(403)

    if request.method == "POST":
        course_id = request.form.get("course_id", type=int)
        title = request.form.get("title", "").strip()
        due_date = request.form.get("due_date")
        if not course_id or not title or not due_date:
            flash("Course, title and due date are required.", "danger")
        else:
            course = Course.query.get(course_id)
            if course.teacher_id != teacher.id:
                abort(403)

            due = datetime.fromisoformat(due_date)
            if assignment is None:
                assignment = Assignment(course_id=course_id)
            assignment.course_id = course_id
            assignment.title = title
            assignment.description = request.form.get("description", "").strip()
            assignment.due_date = due
            assignment.total_marks = request.form.get("total_marks", 100, type=int) or 100
            db.session.add(assignment)
            db.session.commit()
            flash("Assignment saved.", "success")
            return redirect(url_for("teacher.assignments"))

    return render_template("teacher/assignment_form.html", assignment=assignment, courses=courses_list)


@teacher_bp.route("/assignments/<int:assignment_id>/submissions")
def assignment_submissions(assignment_id):
    teacher = current_user.teacher
    assignment = Assignment.query.get_or_404(assignment_id)
    if assignment.course.teacher_id != teacher.id:
        abort(403)

    enrollments = sorted(assignment.course.enrollments, key=lambda e: e.student.roll_no)
    subs = {s.student_id: s for s in assignment.submissions}
    return render_template("teacher/submissions.html", assignment=assignment, enrollments=enrollments, subs=subs)


@teacher_bp.route("/submissions/<int:submission_id>/grade", methods=["GET", "POST"])
@csrf.exempt
def submission_grade(submission_id):
    teacher = current_user.teacher
    submission = Submission.query.get_or_404(submission_id)
    if submission.assignment.course.teacher_id != teacher.id:
        abort(403)

    if request.method == "POST":
        marks = request.form.get("marks", type=float)
        if marks is None or marks < 0 or marks > submission.assignment.total_marks:
            flash(f"Marks must be between 0 and {submission.assignment.total_marks}.", "danger")
        else:
            submission.marks = int(marks) if marks == int(marks) else marks
            submission.feedback = request.form.get("feedback", "").strip() or None
            db.session.commit()
            flash("Submission graded.", "success")
            return redirect(url_for("teacher.assignment_submissions", assignment_id=submission.assignment_id))
    return render_template("teacher/grade_form.html", submission=submission)


@teacher_bp.route("/courses/<int:course_id>/assessments")
def assessments(course_id):
    teacher = current_user.teacher
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != teacher.id:
        abort(403)

    return render_template("teacher/assessments.html", course=course)


@teacher_bp.route("/courses/<int:course_id>/assessments/new", methods=["GET", "POST"])
@csrf.exempt
def assessment_new(course_id):
    teacher = current_user.teacher
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != teacher.id:
        abort(403)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        atype = request.form.get("type", "quiz")
        total_marks = request.form.get("total_marks", type=int)
        weightage = request.form.get("weightage", type=float)
        if not title or not total_marks or weightage is None:
            flash("Title, total marks and weightage are required.", "danger")
        else:
            db.session.add(
                Assessment(
                    course_id=course.id,
                    title=title,
                    type=atype,
                    total_marks=total_marks,
                    weightage=weightage,
                )
            )
            db.session.commit()
            flash("Assessment added.", "success")
            return redirect(url_for("teacher.assessments", course_id=course.id))
    return render_template("teacher/assessment_form.html", course=course, assessment=None)


@teacher_bp.route("/assessments/<int:assessment_id>/marks", methods=["GET", "POST"])
@csrf.exempt
def marks_entry(assessment_id):
    teacher = current_user.teacher
    assessment = Assessment.query.get_or_404(assessment_id)
    if assessment.course.teacher_id != teacher.id:
        abort(403)

    enrollments = sorted(assessment.course.enrollments, key=lambda e: e.student.roll_no)
    existing = {m.student_id: m for m in assessment.marks}

    if request.method == "POST":
        saved = 0
        for e in enrollments:
            raw = request.form.get(f"marks_{e.student_id}", "").strip()
            if raw == "":
                continue
            try:
                value = float(raw)
            except ValueError:
                continue
            if value < 0 or value > assessment.total_marks:
                flash(f"Invalid marks for {e.student.roll_no} — skipped.", "danger")
                continue
            mark = existing.get(e.student_id)
            if mark:
                mark.obtained_marks = value
            else:
                db.session.add(Mark(assessment_id=assessment.id, student_id=e.student_id, obtained_marks=value))
            saved += 1
        db.session.commit()
        flash(f"{saved} mark(s) saved.", "success")
        return redirect(url_for("teacher.marks_entry", assessment_id=assessment.id))

    return render_template(
        "teacher/marks_entry.html",
        assessment=assessment,
        enrollments=enrollments,
        existing=existing,
    )