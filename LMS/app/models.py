from datetime import date, datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


def utcnow():
    return datetime.now(timezone.utc)


DEPARTMENTS = [
    "BS AI", "BS CS", "BSE", "BDS", "BCYS", "BE AV", "BE EL", "BE MECH"
]


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # student | admin | teacher
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    student = db.relationship(
        "Student", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    teacher = db.relationship(
        "Teacher", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_teacher(self):
        return self.role == "teacher"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False
    )
    roll_no = db.Column(db.String(30), unique=True, nullable=False, index=True)
    program = db.Column(db.String(60), nullable=False, default="BS Computer Science")
    semester = db.Column(db.Integer, nullable=False, default=1)
    phone = db.Column(db.String(20))

    user = db.relationship("User", back_populates="student")
    enrollments = db.relationship(
        "Enrollment", back_populates="student", cascade="all, delete-orphan"
    )
    challans = db.relationship(
        "Challan", back_populates="student", cascade="all, delete-orphan"
    )
    warnings = db.relationship(
        "Warning", back_populates="student", cascade="all, delete-orphan"
    )
    submissions = db.relationship(
        "Submission", back_populates="student", cascade="all, delete-orphan"
    )
    marks = db.relationship(
        "Mark", back_populates="student", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Student {self.roll_no}>"

    @property
    def finalized_results(self):
        return [e.result for e in self.enrollments if e.result and e.result.is_finalized]

    @property
    def gpa(self):
        """Semester GPA over finalized courses of the current semester. None if none finalized."""
        results = [
            r
            for r in self.finalized_results
            if r.enrollment.course.semester == self.semester
        ]
        return compute_gpa(results)

    @property
    def cgpa(self):
        return compute_gpa(self.finalized_results)

    @property
    def attendance_percentage(self):
        """Overall attendance across all enrollments. None when no records exist."""
        counts = {"counted": 0, "present": 0}
        for e in self.enrollments:
            for a in e.attendance_records:
                if a.status != "excused":
                    counts["counted"] += 1
                    if a.status in ("present", "late"):
                        counts["present"] += 1
        if counts["counted"] == 0:
            return None
        return round(counts["present"] / counts["counted"] * 100, 1)

    @property
    def unpaid_challans(self):
        return [c for c in self.challans if c.status == "unpaid"]

    @property
    def unread_warnings(self):
        return [w for w in self.warnings if not w.is_read]


class Teacher(db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False
    )
    department = db.Column(db.String(20), nullable=False, index=True)
    semester = db.Column(db.Integer, nullable=False, default=1)
    employee_id = db.Column(db.String(30), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))

    user = db.relationship("User", back_populates="teacher")
    courses = db.relationship("Course", back_populates="teacher_ref")

    def __repr__(self):
        return f"<Teacher {self.employee_id}>"


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(120), nullable=False)
    teacher = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=True, index=True)
    credit_hours = db.Column(db.Integer, nullable=False, default=3)
    semester = db.Column(db.Integer, nullable=False, default=1)
    department = db.Column(db.String(20), nullable=False, default="BS CS")

    enrollments = db.relationship(
        "Enrollment", back_populates="course", cascade="all, delete-orphan"
    )
    assignments = db.relationship(
        "Assignment", back_populates="course", cascade="all, delete-orphan"
    )
    assessments = db.relationship(
        "Assessment", back_populates="course", cascade="all, delete-orphan"
    )
    teacher_ref = db.relationship("Teacher", back_populates="courses")

    def __repr__(self):
        return f"<Course {self.code}>"


class Enrollment(db.Model):
    __tablename__ = "enrollments"
    __table_args__ = (db.UniqueConstraint("student_id", "course_id"),)

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id"), nullable=False, index=True
    )
    course_id = db.Column(
        db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True
    )
    enrolled_on = db.Column(db.Date, nullable=False, default=date.today)

    student = db.relationship("Student", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")
    attendance_records = db.relationship(
        "Attendance", back_populates="enrollment", cascade="all, delete-orphan"
    )
    result = db.relationship(
        "CourseResult", back_populates="enrollment", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def attendance_percentage(self):
        """None when no classes held yet — distinguishes 'new' from '0%'."""
        records = [a for a in self.attendance_records if a.status != "excused"]
        if not records:
            return None
        present = sum(1 for a in records if a.status in ("present", "late"))
        return round(present / len(records) * 100, 1)

    @property
    def is_below_threshold(self):
        pct = self.attendance_percentage
        return pct is not None and pct < 75.0


class Attendance(db.Model):
    __tablename__ = "attendance"
    __table_args__ = (db.UniqueConstraint("enrollment_id", "date"),)

    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(
        db.Integer, db.ForeignKey("enrollments.id"), nullable=False, index=True
    )
    date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(10), nullable=False)  # present | absent | late | excused

    enrollment = db.relationship("Enrollment", back_populates="attendance_records")


class Assignment(TimestampMixin, db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(
        db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True
    )
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime, nullable=False)
    total_marks = db.Column(db.Integer, nullable=False, default=100)

    course = db.relationship("Course", back_populates="assignments")
    submissions = db.relationship(
        "Submission", back_populates="assignment", cascade="all, delete-orphan"
    )

    @property
    def is_past_due(self):
        due = self.due_date if self.due_date.tzinfo else self.due_date.replace(tzinfo=timezone.utc)
        return utcnow() > due


class Submission(TimestampMixin, db.Model):
    __tablename__ = "submissions"
    __table_args__ = (db.UniqueConstraint("assignment_id", "student_id"),)

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(
        db.Integer, db.ForeignKey("assignments.id"), nullable=False, index=True
    )
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id"), nullable=False, index=True
    )
    stored_filename = db.Column(db.String(120), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    marks = db.Column(db.Integer)
    feedback = db.Column(db.Text)

    assignment = db.relationship("Assignment", back_populates="submissions")
    student = db.relationship("Student", back_populates="submissions")

    @property
    def is_graded(self):
        return self.marks is not None


class Assessment(db.Model):
    __tablename__ = "assessments"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(
        db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True
    )
    title = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # quiz | midterm | final | project
    total_marks = db.Column(db.Integer, nullable=False)
    weightage = db.Column(db.Float, nullable=False)  # percent contribution to final grade

    course = db.relationship("Course", back_populates="assessments")
    marks = db.relationship(
        "Mark", back_populates="assessment", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Assessment {self.title}>"


class Mark(db.Model):
    __tablename__ = "marks"
    __table_args__ = (db.UniqueConstraint("assessment_id", "student_id"),)

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(
        db.Integer, db.ForeignKey("assessments.id"), nullable=False, index=True
    )
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id"), nullable=False, index=True
    )
    obtained_marks = db.Column(db.Float, nullable=False)

    assessment = db.relationship("Assessment", back_populates="marks")
    student = db.relationship("Student", back_populates="marks")


# HEC 4.0 scale — descending thresholds
GRADE_SCALE = [
    (85, "A", 4.00),
    (80, "A-", 3.67),
    (75, "B+", 3.33),
    (71, "B", 3.00),
    (68, "B-", 2.67),
    (64, "C+", 2.33),
    (60, "C", 2.00),
    (57, "C-", 1.67),
    (53, "D+", 1.33),
    (50, "D", 1.00),
    (0, "F", 0.00),
]


def grade_for(percentage):
    for threshold, letter, points in GRADE_SCALE:
        if percentage >= threshold:
            return letter, points
    return "F", 0.00


def compute_gpa(results):
    """Credit-hour weighted GPA. F counts in the denominator. None when empty."""
    total_credits = sum(r.enrollment.course.credit_hours for r in results)
    if total_credits == 0:
        return None
    total_points = sum(
        r.grade_points * r.enrollment.course.credit_hours for r in results
    )
    return round(total_points / total_credits, 2)


class CourseResult(db.Model):
    __tablename__ = "course_results"

    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(
        db.Integer, db.ForeignKey("enrollments.id"), unique=True, nullable=False
    )
    percentage = db.Column(db.Float, nullable=False)
    grade_letter = db.Column(db.String(3), nullable=False)
    grade_points = db.Column(db.Float, nullable=False)
    is_finalized = db.Column(db.Boolean, nullable=False, default=False)
    finalized_on = db.Column(db.DateTime)

    enrollment = db.relationship("Enrollment", back_populates="result")

    @property
    def course(self):
        return self.enrollment.course

    @property
    def student(self):
        return self.enrollment.student

    @staticmethod
    def compute_percentage(enrollment):
        """Weighted percentage from assessment marks. None when no marks entered."""
        marks = (
            Mark.query.join(Assessment)
            .filter(
                Mark.student_id == enrollment.student_id,
                Assessment.course_id == enrollment.course_id,
            )
            .all()
        )
        marks_by_assessment = {m.assessment_id: m for m in marks}
        total_weight_earned = 0.0
        total_weight_possible = 0.0
        for assessment in enrollment.course.assessments:
            mark = marks_by_assessment.get(assessment.id)
            if mark is not None:
                total_weight_earned += (mark.obtained_marks / assessment.total_marks) * assessment.weightage
            total_weight_possible += assessment.weightage
        if total_weight_possible == 0:
            return None
        return round(total_weight_earned / total_weight_possible * 100, 1)


class Challan(TimestampMixin, db.Model):
    __tablename__ = "challans"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id"), nullable=False, index=True
    )
    challan_no = db.Column(db.String(30), unique=True, nullable=False)
    fee_type = db.Column(db.String(60), nullable=False)  # tuition | exam | hostel | library | late fee
    description = db.Column(db.String(200))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    issue_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(12), nullable=False, default="unpaid")  # unpaid | paid | cancelled
    paid_date = db.Column(db.Date)
    receipt_no = db.Column(db.String(40))

    student = db.relationship("Student", back_populates="challans")

    def __repr__(self):
        return f"<Challan {self.challan_no}>"

    @property
    def is_overdue(self):
        return self.status == "unpaid" and self.due_date < date.today()

    @property
    def display_status(self):
        if self.status == "paid":
            return "Paid"
        if self.status == "cancelled":
            return "Cancelled"
        return "Overdue" if self.is_overdue else "Unpaid"


class Warning(TimestampMixin, db.Model):
    __tablename__ = "warnings"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id"), nullable=False, index=True
    )
    type = db.Column(db.String(20), nullable=False)  # attendance | fee | disciplinary
    severity = db.Column(db.String(12), nullable=False, default="warning")  # info | warning | critical
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(10), nullable=False, default="manual")  # manual | system | api
    related_challan_id = db.Column(db.Integer, db.ForeignKey("challans.id"))
    image_filename = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    read_at = db.Column(db.DateTime)

    student = db.relationship("Student", back_populates="warnings")
    related_challan = db.relationship("Challan")

    def __repr__(self):
        return f"<Warning {self.type}:{self.student.roll_no}>"


class PendingAlert(TimestampMixin, db.Model):
    __tablename__ = "pending_alerts"

    id = db.Column(db.Integer, primary_key=True)
    camera = db.Column(db.String(30), nullable=False)
    violation_type = db.Column(db.String(30), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    detected_at = db.Column(db.DateTime, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(12), nullable=False, default="pending")  # pending | confirmed | dismissed
    confirmed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    warning_id = db.Column(db.Integer, db.ForeignKey("warnings.id"), nullable=True)

    confirmer = db.relationship("User")
    warning = db.relationship("Warning")

    @property
    def violation_label(self):
        labels = {"smoking": "Smoking Detected", "id_card_missing": "ID Card Missing"}
        return labels.get(self.violation_type, self.violation_type.replace("_", " ").title())


class Announcement(TimestampMixin, db.Model):
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_pinned = db.Column(db.Boolean, nullable=False, default=False)
    expires_on = db.Column(db.Date)

    @property
    def is_expired(self):
        return self.expires_on is not None and self.expires_on < date.today()
