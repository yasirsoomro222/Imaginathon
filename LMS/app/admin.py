import os
import uuid
from datetime import date, timedelta

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
from app.auth import admin_required
from app.mail_utils import send_email
from app.models import (
    Announcement,
    Assessment,
    Assignment,
    Attendance,
    Challan,
    Course,
    CourseResult,
    DEPARTMENTS,
    Enrollment,
    Mark,
    PendingAlert,
    Student,
    Submission,
    Teacher,
    User,
    Warning,
    grade_for,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

FEE_TYPES = ["Tuition Fee", "Exam Fee", "Hostel Fee", "Library Fine", "Late Fee", "Admission Fee"]


@admin_bp.before_request
def _require_admin():
    if not current_user.is_authenticated or current_user.role != "admin":
        abort(403)


@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    students = Student.query.count()
    courses = Course.query.count()
    unpaid = Challan.query.filter_by(status="unpaid").count()
    overdue = [c for c in Challan.query.filter_by(status="unpaid") if c.is_overdue]
    warnings_unread = Warning.query.filter_by(is_read=False).count()
    enrollments = Enrollment.query.all()
    low_attendance = [e for e in enrollments if e.is_below_threshold]

    recent_challans = Challan.query.order_by(Challan.issue_date.desc()).limit(5).all()
    recent_warnings = Warning.query.order_by(Warning.created_at.desc()).limit(5).all()

    dept_stats = []
    for dept in DEPARTMENTS:
        count = Student.query.filter_by(program=dept).count()
        dept_stats.append({"name": dept, "students": count})

    return render_template(
        "admin/dashboard.html",
        students=students,
        courses=courses,
        unpaid=unpaid,
        overdue=len(overdue),
        warnings_unread=warnings_unread,
        low_attendance=low_attendance,
        recent_challans=recent_challans,
        recent_warnings=recent_warnings,
        dept_stats=dept_stats,
        departments=DEPARTMENTS,
    )


# ---------------------------------------------------------------- departments


@admin_bp.route("/departments")
@login_required
@admin_required
def departments():
    dept_data = []
    for dept in DEPARTMENTS:
        student_count = Student.query.filter_by(program=dept).count()
        course_count = Course.query.filter_by(department=dept).count()
        semesters = {}
        for sem in range(1, 9):
            sem_students = Student.query.filter_by(program=dept, semester=sem).count()
            sem_courses = Course.query.filter_by(department=dept, semester=sem).count()
            semesters[sem] = {"students": sem_students, "courses": sem_courses}
        dept_data.append({
            "name": dept,
            "students": student_count,
            "courses": course_count,
            "semesters": semesters,
        })
    return render_template("admin/departments.html", dept_data=dept_data)


# ---------------------------------------------------------------- students


@admin_bp.route("/students")
@login_required
@admin_required
def students():
    q = request.args.get("q", "").strip()
    dept = request.args.get("dept", "").strip()
    page = request.args.get("page", 1, type=int)
    query = Student.query.join(User).order_by(Student.roll_no)
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Student.roll_no.ilike(like), User.full_name.ilike(like), User.email.ilike(like))
        )
    if dept and dept in DEPARTMENTS:
        query = query.filter(Student.program == dept)
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    return render_template("admin/students.html", pagination=pagination, q=q, dept=dept, departments=DEPARTMENTS)


@admin_bp.route("/students/new", methods=["GET", "POST"])
@login_required
@admin_required
def student_new():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        full_name = request.form.get("full_name", "").strip()
        roll_no = request.form.get("roll_no", "").strip()
        password = request.form.get("password", "").strip()
        program = request.form.get("program", "").strip() or "BS CS"
        semester = request.form.get("semester", 1, type=int)
        phone = request.form.get("phone", "").strip()

        if User.query.filter_by(email=email).first():
            flash("A user with this email already exists.", "danger")
            return render_template("admin/student_form.html", form=request.form, departments=DEPARTMENTS)
        if Student.query.filter_by(roll_no=roll_no).first():
            flash("A student with this roll number already exists.", "danger")
            return render_template("admin/student_form.html", form=request.form, departments=DEPARTMENTS)
        if not all([email, full_name, roll_no, password]):
            flash("Email, full name, roll number and password are required.", "danger")
            return render_template("admin/student_form.html", form=request.form, departments=DEPARTMENTS)

        user = User(email=email, full_name=full_name, role="student")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        student = Student(
            user_id=user.id, roll_no=roll_no, program=program, semester=semester, phone=phone or None
        )
        db.session.add(student)
        db.session.commit()
        flash(f"Student {roll_no} created successfully.", "success")
        return redirect(url_for("admin.student_detail", student_id=student.id))

    return render_template("admin/student_form.html", form={}, departments=DEPARTMENTS)


@admin_bp.route("/students/<int:student_id>")
@login_required
@admin_required
def student_detail(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template("admin/student_detail.html", student=student)


@admin_bp.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def student_edit(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        existing = User.query.filter(User.email == email, User.id != student.user_id).first()
        if existing:
            flash("Another user already uses this email.", "danger")
        elif not email or not request.form.get("full_name", "").strip():
            flash("Email and full name are required.", "danger")
        else:
            student.user.email = email
            student.user.full_name = request.form.get("full_name", "").strip()
            student.roll_no = request.form.get("roll_no", "").strip() or student.roll_no
            student.program = request.form.get("program", "").strip() or student.program
            student.semester = request.form.get("semester", 1, type=int)
            student.phone = request.form.get("phone", "").strip() or None
            db.session.commit()
            flash("Student updated.", "success")
            return redirect(url_for("admin.student_detail", student_id=student.id))
    return render_template("admin/student_form.html", student=student, form=request.form, departments=DEPARTMENTS)


@admin_bp.route("/students/<int:student_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def student_toggle_active(student_id):
    student = Student.query.get_or_404(student_id)
    student.user.is_active = not student.user.is_active
    db.session.commit()
    state = "activated" if student.user.is_active else "deactivated"
    flash(f"Account {state} for {student.roll_no}.", "info")
    return redirect(url_for("admin.student_detail", student_id=student.id))


@admin_bp.route("/students/<int:student_id>/reset-password", methods=["POST"])
@login_required
@admin_required
def student_reset_password(student_id):
    student = Student.query.get_or_404(student_id)
    new_password = "student123"
    student.user.set_password(new_password)
    db.session.commit()
    flash(f"Password for {student.roll_no} reset to '{new_password}'.", "success")
    return redirect(url_for("admin.student_detail", student_id=student.id))


# ---------------------------------------------------------------- teachers


@admin_bp.route("/teachers")
@login_required
@admin_required
def teachers():
    q = request.args.get("q", "").strip()
    dept = request.args.get("dept", "").strip()
    page = request.args.get("page", 1, type=int)
    query = Teacher.query.join(User).order_by(Teacher.employee_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Teacher.employee_id.ilike(like), User.full_name.ilike(like), User.email.ilike(like))
        )
    if dept and dept in DEPARTMENTS:
        query = query.filter(Teacher.department == dept)
    pagination = query.paginate(page=page, per_page=15, error_out=False)
    return render_template("admin/teachers.html", pagination=pagination, q=q, dept=dept, departments=DEPARTMENTS)


@admin_bp.route("/teachers/new", methods=["GET", "POST"])
@login_required
@admin_required
def teacher_new():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        full_name = request.form.get("full_name", "").strip()
        employee_id = request.form.get("employee_id", "").strip()
        password = request.form.get("password", "").strip()
        department = request.form.get("department", "").strip()
        semester = request.form.get("semester", 1, type=int)
        phone = request.form.get("phone", "").strip()

        if User.query.filter_by(email=email).first():
            flash("A user with this email already exists.", "danger")
            return render_template("admin/teacher_form.html", form=request.form, departments=DEPARTMENTS)
        if Teacher.query.filter_by(employee_id=employee_id).first():
            flash("A teacher with this employee ID already exists.", "danger")
            return render_template("admin/teacher_form.html", form=request.form, departments=DEPARTMENTS)
        if not all([email, full_name, employee_id, password, department]):
            flash("Email, full name, employee ID, password and department are required.", "danger")
            return render_template("admin/teacher_form.html", form=request.form, departments=DEPARTMENTS)

        user = User(email=email, full_name=full_name, role="teacher")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        teacher = Teacher(
            user_id=user.id,
            department=department,
            semester=semester,
            employee_id=employee_id,
            phone=phone or None,
        )
        db.session.add(teacher)
        db.session.commit()
        flash(f"Teacher {employee_id} created successfully.", "success")
        return redirect(url_for("admin.teacher_detail", teacher_id=teacher.id))

    return render_template("admin/teacher_form.html", form={}, departments=DEPARTMENTS)


@admin_bp.route("/teachers/<int:teacher_id>")
@login_required
@admin_required
def teacher_detail(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    courses = Course.query.filter_by(teacher_id=teacher.id).all()
    return render_template("admin/teacher_detail.html", teacher=teacher, courses=courses)


@admin_bp.route("/teachers/<int:teacher_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def teacher_edit(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        existing = User.query.filter(User.email == email, User.id != teacher.user_id).first()
        if existing:
            flash("Another user already uses this email.", "danger")
        elif not email or not request.form.get("full_name", "").strip():
            flash("Email and full name are required.", "danger")
        else:
            teacher.user.email = email
            teacher.user.full_name = request.form.get("full_name", "").strip()
            teacher.employee_id = request.form.get("employee_id", "").strip() or teacher.employee_id
            teacher.department = request.form.get("department", "").strip() or teacher.department
            teacher.semester = request.form.get("semester", 1, type=int)
            teacher.phone = request.form.get("phone", "").strip() or None
            db.session.commit()
            flash("Teacher updated.", "success")
            return redirect(url_for("admin.teacher_detail", teacher_id=teacher.id))
    return render_template("admin/teacher_form.html", teacher=teacher, form=request.form, departments=DEPARTMENTS)


@admin_bp.route("/teachers/<int:teacher_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def teacher_toggle_active(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    teacher.user.is_active = not teacher.user.is_active
    db.session.commit()
    state = "activated" if teacher.user.is_active else "deactivated"
    flash(f"Account {state} for {teacher.employee_id}.", "info")
    return redirect(url_for("admin.teacher_detail", teacher_id=teacher.id))


@admin_bp.route("/teachers/<int:teacher_id>/reset-password", methods=["POST"])
@login_required
@admin_required
def teacher_reset_password(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    new_password = "teacher123"
    teacher.user.set_password(new_password)
    db.session.commit()
    flash(f"Password for {teacher.employee_id} reset to '{new_password}'.", "success")
    return redirect(url_for("admin.teacher_detail", teacher_id=teacher.id))


@admin_bp.route("/teachers/export")
@login_required
@admin_required
def teachers_export():
    teachers_list = Teacher.query.join(User).order_by(Teacher.department, Teacher.employee_id).all()
    return render_template("admin/teachers_export.html", teachers=teachers_list)


# ---------------------------------------------------------------- courses


@admin_bp.route("/courses")
@login_required
@admin_required
def courses():
    dept = request.args.get("dept", "").strip()
    sem = request.args.get("sem", "", type=str)
    query = Course.query.order_by(Course.department, Course.semester, Course.code)
    if dept and dept in DEPARTMENTS:
        query = query.filter(Course.department == dept)
    if sem:
        try:
            query = query.filter(Course.semester == int(sem))
        except ValueError:
            pass
    items = query.all()
    return render_template("admin/courses.html", courses=items, departments=DEPARTMENTS, dept=dept, sem=sem)


@admin_bp.route("/courses/new", methods=["GET", "POST"])
@login_required
@admin_required
def course_new():
    teachers_list = Teacher.query.join(User).order_by(User.full_name).all()
    if request.method == "POST":
        code = request.form.get("code", "").strip()
        title = request.form.get("title", "").strip()
        teacher_id = request.form.get("teacher_id", type=int)
        department = request.form.get("department", "").strip() or "BS CS"
        if not all([code, title, teacher_id]):
            flash("Code, title and teacher are required.", "danger")
        elif Course.query.filter_by(code=code).first():
            flash("A course with this code already exists.", "danger")
        else:
            teacher = Teacher.query.get(teacher_id)
            course = Course(
                code=code,
                title=title,
                teacher=teacher.user.full_name,
                teacher_id=teacher_id,
                credit_hours=request.form.get("credit_hours", 3, type=int) or 3,
                semester=request.form.get("semester", 1, type=int) or 1,
                department=department,
            )
            db.session.add(course)
            db.session.commit()
            flash(f"Course {code} created.", "success")
            return redirect(url_for("admin.courses"))
    return render_template("admin/course_form.html", course=None, departments=DEPARTMENTS, teachers=teachers_list)


@admin_bp.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def course_edit(course_id):
    course = Course.query.get_or_404(course_id)
    teachers_list = Teacher.query.join(User).order_by(User.full_name).all()
    if request.method == "POST":
        code = request.form.get("code", "").strip()
        clash = Course.query.filter(Course.code == code, Course.id != course.id).first()
        if clash:
            flash("Another course uses this code.", "danger")
        else:
            teacher_id = request.form.get("teacher_id", type=int)
            teacher = Teacher.query.get(teacher_id) if teacher_id else None
            course.code = code or course.code
            course.title = request.form.get("title", "").strip() or course.title
            if teacher:
                course.teacher = teacher.user.full_name
                course.teacher_id = teacher_id
            course.credit_hours = request.form.get("credit_hours", 3, type=int) or 3
            course.semester = request.form.get("semester", 1, type=int) or 1
            course.department = request.form.get("department", "").strip() or course.department
            db.session.commit()
            flash("Course updated.", "success")
            return redirect(url_for("admin.courses"))
    return render_template("admin/course_form.html", course=course, departments=DEPARTMENTS, teachers=teachers_list)


@admin_bp.route("/courses/<int:course_id>/delete", methods=["POST"])
@login_required
@admin_required
def course_delete(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash(f"Course {course.code} deleted along with its enrollments.", "info")
    return redirect(url_for("admin.courses"))


@admin_bp.route("/courses/<int:course_id>/enroll", methods=["GET", "POST"])
@login_required
@admin_required
def course_enroll(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == "POST":
        selected = request.form.getlist("student_ids")
        added = 0
        for sid in selected:
            student = Student.query.get(int(sid))
            if student and not any(e.course_id == course.id for e in student.enrollments):
                db.session.add(Enrollment(student_id=student.id, course_id=course.id))
                added += 1
        db.session.commit()
        flash(f"{added} student(s) enrolled in {course.code}.", "success")
        return redirect(url_for("admin.course_enroll", course_id=course.id))

    enrolled_ids = [e.student_id for e in course.enrollments]
    available = Student.query.filter(Student.id.notin_(enrolled_ids)).order_by(Student.roll_no).all()
    return render_template("admin/course_enroll.html", course=course, available=available)


@admin_bp.route("/courses/<int:course_id>/unenroll/<int:enrollment_id>", methods=["POST"])
@login_required
@admin_required
def course_unenroll(course_id, enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    db.session.delete(enrollment)
    db.session.commit()
    flash("Student unenrolled.", "info")
    return redirect(url_for("admin.course_enroll", course_id=course_id))


# ---------------------------------------------------------------- attendance


@admin_bp.route("/attendance", methods=["GET", "POST"])
@login_required
@admin_required
def attendance_select():
    if request.method == "POST":
        course_id = request.form.get("course_id", type=int)
        att_date = request.form.get("date")
        if course_id and att_date:
            return redirect(
                url_for("admin.attendance_mark", course_id=course_id, date_str=att_date)
            )
        flash("Please select a course and a date.", "warning")
    courses_list = Course.query.order_by(Course.code).all()
    return render_template(
        "admin/attendance_select.html",
        courses=courses_list,
        default_date=date.today().isoformat(),
    )


@admin_bp.route("/attendance/<int:course_id>/<date_str>", methods=["GET", "POST"])
@login_required
@admin_required
def attendance_mark(course_id, date_str):
    course = Course.query.get_or_404(course_id)
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
        return redirect(url_for("admin.attendance_report", course_id=course.id))

    statuses = ["present", "absent", "late", "excused"]
    return render_template(
        "admin/attendance_mark.html",
        course=course,
        att_date=att_date,
        enrollments=enrollments,
        existing=existing,
        statuses=statuses,
    )


@admin_bp.route("/attendance/report/<int:course_id>")
@login_required
@admin_required
def attendance_report(course_id):
    course = Course.query.get_or_404(course_id)
    enrollments = sorted(course.enrollments, key=lambda e: e.student.roll_no)
    return render_template("admin/attendance_report.html", course=course, enrollments=enrollments, today=date.today().isoformat())


# ---------------------------------------------------------------- assignments


@admin_bp.route("/assignments")
@login_required
@admin_required
def assignments():
    items = Assignment.query.order_by(Assignment.due_date.desc()).all()
    return render_template("admin/assignments.html", assignments=items)


@admin_bp.route("/assignments/new", methods=["GET", "POST"])
@admin_bp.route("/assignments/<int:assignment_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def assignment_form(assignment_id=None):
    assignment = Assignment.query.get_or_404(assignment_id) if assignment_id else None
    courses_list = Course.query.order_by(Course.code).all()

    if request.method == "POST":
        course_id = request.form.get("course_id", type=int)
        title = request.form.get("title", "").strip()
        due_date = request.form.get("due_date")
        if not course_id or not title or not due_date:
            flash("Course, title and due date are required.", "danger")
        else:
            from datetime import datetime

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
            return redirect(url_for("admin.assignments"))

    return render_template("admin/assignment_form.html", assignment=assignment, courses=courses_list)


@admin_bp.route("/assignments/<int:assignment_id>/submissions")
@login_required
@admin_required
def assignment_submissions(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    enrollments = sorted(assignment.course.enrollments, key=lambda e: e.student.roll_no)
    subs = {s.student_id: s for s in assignment.submissions}
    return render_template("admin/submissions.html", assignment=assignment, enrollments=enrollments, subs=subs)


@admin_bp.route("/submissions/<int:submission_id>/download")
@login_required
@admin_required
def download_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        submission.stored_filename,
        as_attachment=True,
        download_name=submission.original_filename,
    )


@admin_bp.route("/submissions/<int:submission_id>/grade", methods=["GET", "POST"])
@login_required
@admin_required
def submission_grade(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    if request.method == "POST":
        marks = request.form.get("marks", type=float)
        if marks is None or marks < 0 or marks > submission.assignment.total_marks:
            flash(f"Marks must be between 0 and {submission.assignment.total_marks}.", "danger")
        else:
            submission.marks = int(marks) if marks == int(marks) else marks
            submission.feedback = request.form.get("feedback", "").strip() or None
            db.session.commit()
            flash("Submission graded.", "success")
            return redirect(url_for("admin.assignment_submissions", assignment_id=submission.assignment_id))
    return render_template("admin/grade_form.html", submission=submission)


# ---------------------------------------------------------------- assessments & results


@admin_bp.route("/courses/<int:course_id>/assessments")
@login_required
@admin_required
def assessments(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template("admin/assessments.html", course=course)


@admin_bp.route("/courses/<int:course_id>/assessments/new", methods=["GET", "POST"])
@login_required
@admin_required
def assessment_new(course_id):
    course = Course.query.get_or_404(course_id)
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
            return redirect(url_for("admin.assessments", course_id=course.id))
    return render_template("admin/assessment_form.html", course=course, assessment=None)


@admin_bp.route("/assessments/<int:assessment_id>/marks", methods=["GET", "POST"])
@login_required
@admin_required
def marks_entry(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
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
        return redirect(url_for("admin.marks_entry", assessment_id=assessment.id))

    return render_template(
        "admin/marks_entry.html",
        assessment=assessment,
        enrollments=enrollments,
        existing=existing,
    )


@admin_bp.route("/courses/<int:course_id>/finalize", methods=["POST"])
@login_required
@admin_required
def finalize_results(course_id):
    course = Course.query.get_or_404(course_id)
    finalized = 0
    for e in course.enrollments:
        pct = CourseResult.compute_percentage(e)
        if pct is None:
            continue
        letter, points = grade_for(pct)
        result = e.result
        if result is None:
            result = CourseResult(enrollment_id=e.id)
            db.session.add(result)
        result.percentage = pct
        result.grade_letter = letter
        result.grade_points = points
        result.is_finalized = True
        result.finalized_on = db.func.now()
        finalized += 1
    db.session.commit()
    flash(f"{finalized} result(s) finalized for {course.code}.", "success")
    return redirect(url_for("admin.assessments", course_id=course.id))


# ---------------------------------------------------------------- challans


def _next_challan_no():
    today = date.today()
    prefix = f"CH-{today.strftime('%Y%m')}-"
    last = (
        Challan.query.filter(Challan.challan_no.like(prefix + "%"))
        .order_by(Challan.challan_no.desc())
        .first()
    )
    seq = int(last.challan_no.split("-")[-1]) + 1 if last else 1
    return f"{prefix}{seq:04d}"


@admin_bp.route("/challans")
@login_required
@admin_required
def challans():
    status = request.args.get("status", "").strip()
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    query = Challan.query.join(Student).order_by(Challan.issue_date.desc())
    if status in ("unpaid", "paid", "cancelled"):
        query = query.filter(Challan.status == status)
    if q:
        query = query.filter(
            db.or_(Challan.challan_no.ilike(f"%{q}%"), Student.roll_no.ilike(f"%{q}%"))
        )
    pagination = query.paginate(page=page, per_page=15, error_out=False)
    return render_template(
        "admin/challans.html", pagination=pagination, status=status, q=q, fee_types=FEE_TYPES
    )


@admin_bp.route("/challans/new", methods=["GET", "POST"])
@login_required
@admin_required
def challan_new():
    students_list = Student.query.order_by(Student.roll_no).all()
    if request.method == "POST":
        student_ids = [int(s) for s in request.form.getlist("student_ids")]
        fee_type = request.form.get("fee_type", "").strip()
        amount = request.form.get("amount", type=float)
        due_date = request.form.get("due_date")
        description = request.form.get("description", "").strip()

        if not student_ids or not fee_type or not amount or not due_date:
            flash("Student(s), fee type, amount and due date are required.", "danger")
        elif amount <= 0:
            flash("Amount must be greater than zero.", "danger")
        else:
            due = date.fromisoformat(due_date)
            created = []
            for sid in student_ids:
                challan = Challan(
                    student_id=sid,
                    challan_no=_next_challan_no(),
                    fee_type=fee_type,
                    description=description or None,
                    amount=round(amount, 2),
                    due_date=due,
                )
                db.session.add(challan)
                created.append(challan)
            db.session.commit()

            for challan in created:
                student = challan.student
                html = render_template(
                    "email/challan.html",
                    student=student,
                    challan=challan,
                )
                send_email(
                    student.user.email,
                    f"Fee Challan {challan.challan_no} — {fee_type}",
                    html,
                )

            flash(f"{len(created)} challan(s) issued and emailed.", "success")
            return redirect(url_for("admin.challans"))

    selected_id = request.args.get("student_id", type=int)
    return render_template(
        "admin/challan_form.html",
        students=students_list,
        fee_types=FEE_TYPES,
        selected_id=selected_id,
        default_due=(date.today() + timedelta(days=14)).isoformat(),
    )


@admin_bp.route("/challans/<int:challan_id>/mark-paid", methods=["POST"])
@login_required
@admin_required
def challan_mark_paid(challan_id):
    challan = Challan.query.get_or_404(challan_id)
    if challan.status != "unpaid":
        flash("Only unpaid challans can be marked as paid.", "warning")
    else:
        receipt_no = request.form.get("receipt_no", "").strip() or f"RC-{challan.challan_no}"
        challan.status = "paid"
        challan.paid_date = date.today()
        challan.receipt_no = receipt_no
        db.session.commit()
        flash(f"Challan {challan.challan_no} marked as paid.", "success")
    return redirect(url_for("admin.challans"))


@admin_bp.route("/challans/<int:challan_id>/cancel", methods=["POST"])
@login_required
@admin_required
def challan_cancel(challan_id):
    challan = Challan.query.get_or_404(challan_id)
    if challan.status == "paid":
        flash("A paid challan cannot be cancelled.", "warning")
    else:
        challan.status = "cancelled"
        db.session.commit()
        flash(f"Challan {challan.challan_no} cancelled.", "info")
    return redirect(url_for("admin.challans"))


@admin_bp.route("/challans/<int:challan_id>/print")
@login_required
@admin_required
def challan_print(challan_id):
    challan = Challan.query.get_or_404(challan_id)
    return render_template("student/challan_print.html", challan=challan)


# ---------------------------------------------------------------- warnings


@admin_bp.route("/warnings")
@login_required
@admin_required
def warnings():
    wtype = request.args.get("type", "").strip()
    page = request.args.get("page", 1, type=int)
    query = Warning.query.join(Student).order_by(Warning.created_at.desc())
    if wtype in ("attendance", "fee", "disciplinary"):
        query = query.filter(Warning.type == wtype)
    pagination = query.paginate(page=page, per_page=15, error_out=False)
    return render_template("admin/warnings.html", pagination=pagination, wtype=wtype)


@admin_bp.route("/warnings/new", methods=["GET", "POST"])
@login_required
@admin_required
def warning_new():
    students_list = Student.query.order_by(Student.roll_no).all()
    challans_list = Challan.query.filter_by(status="unpaid").order_by(Challan.issue_date.desc()).all()
    if request.method == "POST":
        student_ids = [int(s) for s in request.form.getlist("student_ids")]
        wtype = request.form.get("type", "").strip()
        severity = request.form.get("severity", "warning")
        title = request.form.get("title", "").strip()
        message = request.form.get("message", "").strip()
        related_challan_id = request.form.get("related_challan_id", type=int)

        if not student_ids or not title or not message or wtype not in ("attendance", "fee", "disciplinary"):
            flash("Student(s), type, title and message are required.", "danger")
        else:
            created = []
            for sid in student_ids:
                warning = Warning(
                    student_id=sid,
                    type=wtype,
                    severity=severity,
                    title=title,
                    message=message,
                    source="manual",
                    related_challan_id=related_challan_id if wtype == "fee" else None,
                )
                db.session.add(warning)
                created.append(warning)
            db.session.commit()

            for warning in created:
                send_email(
                    warning.student.user.email,
                    f"Warning: {warning.title}",
                    render_template("email/warning.html", warning=warning),
                )
            flash(f"{len(created)} warning(s) issued and emailed.", "success")
            return redirect(url_for("admin.warnings"))

    selected_id = request.args.get("student_id", type=int)
    return render_template("admin/warning_form.html", students=students_list, challans=challans_list, selected_id=selected_id)


@admin_bp.route("/warnings/bulk-attendance", methods=["GET", "POST"])
@login_required
@admin_required
def warnings_bulk_attendance():
    enrollments = Enrollment.query.all()
    below = [e for e in enrollments if e.is_below_threshold]
    if request.method == "POST":
        count = 0
        for e in below:
            pct = e.attendance_percentage
            title = f"Low Attendance Warning — {e.course.code}"
            message = (
                f"Dear {e.student.user.full_name},\n\n"
                f"Your attendance in {e.course.code} ({e.course.title}) is {pct}%, "
                f"which is below the required 75%. You are at risk of being debarred "
                f"from the final exam of this course. Please improve your attendance "
                f"and contact your course instructor or the department office immediately."
            )
            warning = Warning(
                student_id=e.student_id,
                type="attendance",
                severity="critical" if pct < 65 else "warning",
                title=title,
                message=message,
                source="system",
            )
            db.session.add(warning)
            send_email(
                e.student.user.email,
                f"Warning: {title}",
                render_template("email/warning.html", warning=warning),
            )
            count += 1
        db.session.commit()
        flash(f"{count} attendance warning(s) issued to students below 75%.", "success")
        return redirect(url_for("admin.warnings"))

    return render_template("admin/bulk_warnings.html", below=below)


# ---------------------------------------------------------------- announcements


@admin_bp.route("/announcements")
@login_required
@admin_required
def announcements():
    items = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template("admin/announcements.html", announcements=items)


@admin_bp.route("/announcements/new", methods=["GET", "POST"])
@admin_bp.route("/announcements/<int:announcement_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def announcement_form(announcement_id=None):
    announcement = Announcement.query.get_or_404(announcement_id) if announcement_id else None
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        expires_on = request.form.get("expires_on", "").strip()
        if not title or not body:
            flash("Title and body are required.", "danger")
        else:
            if announcement is None:
                announcement = Announcement()
                db.session.add(announcement)
            announcement.title = title
            announcement.body = body
            announcement.is_pinned = request.form.get("is_pinned") == "on"
            announcement.expires_on = date.fromisoformat(expires_on) if expires_on else None
            db.session.commit()
            flash("Announcement saved.", "success")
            return redirect(url_for("admin.announcements"))
    return render_template("admin/announcement_form.html", announcement=announcement)


@admin_bp.route("/announcements/<int:announcement_id>/delete", methods=["POST"])
@login_required
@admin_required
def announcement_delete(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    db.session.delete(announcement)
    db.session.commit()
    flash("Announcement deleted.", "info")
    return redirect(url_for("admin.announcements"))


# ---------------------------------------------------------------- pending alerts (CampusGuard AI)


@admin_bp.route("/pending-alerts")
@login_required
@admin_required
def pending_alerts():
    items = PendingAlert.query.order_by(PendingAlert.created_at.desc()).all()
    students = Student.query.join(User).order_by(User.full_name).all()
    return render_template("admin/pending_alerts.html", alerts=items, students=students)


@admin_bp.route("/pending-alerts/<int:alert_id>/confirm", methods=["POST"])
@login_required
@admin_required
def pending_alert_confirm(alert_id):
    alert = PendingAlert.query.get_or_404(alert_id)
    if alert.status != "pending":
        flash("This alert has already been processed.", "warning")
        return redirect(url_for("admin.pending_alerts"))

    student_id = request.form.get("student_id")
    if not student_id:
        flash("Please select a student.", "danger")
        return redirect(url_for("admin.pending_alerts"))

    student = Student.query.get_or_404(int(student_id))

    violation_labels = {
        "smoking": "Smoking Violation",
        "id_card_missing": "ID Card Missing",
    }
    label = violation_labels.get(alert.violation_type, alert.violation_type.replace("_", " ").title())
    title = f"{label} — {alert.camera.title()} Camera"
    message = (
        f"Violation detected by CampusGuard AI:\n\n"
        f"Type: {label}\n"
        f"Camera: {alert.camera.title()}\n"
        f"Confidence: {alert.confidence * 100:.0f}%\n"
        f"Detected at: {alert.detected_at.strftime('%d %b %Y, %I:%M %p') if alert.detected_at else 'N/A'}\n\n"
        f"This violation was automatically detected by the campus surveillance system."
    )

    warning = Warning(
        student_id=student.id,
        type="disciplinary",
        severity="warning",
        title=title,
        message=message,
        source="api",
        image_filename=alert.image_filename,
    )
    db.session.add(warning)
    db.session.flush()

    alert.status = "confirmed"
    alert.confirmed_by = current_user.id
    alert.warning_id = warning.id

    db.session.commit()

    image_path = (
        os.path.join(current_app.config["DETECTION_IMAGE_FOLDER"], alert.image_filename)
        if alert.image_filename
        else None
    )
    send_email(
        student.user.email,
        f"Warning: {title}",
        render_template("email/warning.html", warning=warning),
        attachment_path=image_path,
    )

    flash(f"Warning issued to {student.user.full_name} ({student.roll_no}).", "success")
    return redirect(url_for("admin.pending_alerts"))


@admin_bp.route("/pending-alerts/<int:alert_id>/dismiss", methods=["POST"])
@login_required
@admin_required
def pending_alert_dismiss(alert_id):
    alert = PendingAlert.query.get_or_404(alert_id)
    if alert.status != "pending":
        flash("This alert has already been processed.", "warning")
        return redirect(url_for("admin.pending_alerts"))

    alert.status = "dismissed"
    alert.confirmed_by = current_user.id
    db.session.commit()

    flash("Alert dismissed.", "info")
    return redirect(url_for("admin.pending_alerts"))


@admin_bp.route("/detection-image/<filename>")
@login_required
@admin_required
def detection_image(filename):
    image_folder = current_app.config["DETECTION_IMAGE_FOLDER"]
    return send_from_directory(image_folder, filename)
