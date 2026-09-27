import os

from flask import Flask, render_template
from flask_login import AnonymousUserMixin
from flask_wtf import CSRFProtect
from sqlalchemy import event

from config import Config, INSTANCE_DIR

db = None
login_manager = None
mail = None
csrf = CSRFProtect()


class AnonymousUser(AnonymousUserMixin):
    role = None

    @property
    def student(self):
        return None


def create_app(config_class=Config):
    global db, login_manager, mail

    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(INSTANCE_DIR, exist_ok=True)

    from flask_mail import Mail
    from flask_sqlalchemy import SQLAlchemy
    from flask_login import LoginManager

    db = SQLAlchemy()
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"
    mail = Mail()

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    login_manager.anonymous_user = AnonymousUser

    with app.app_context():

        @event.listens_for(db.engine, "connect")
        def _fk_pragma_on_connect(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.auth import auth_bp
    from app.student import student_bp
    from app.admin import admin_bp
    from app.api import api_bp
    from app.teacher import teacher_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    csrf.exempt(api_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(teacher_bp)

    os.makedirs(app.config.get("DETECTION_IMAGE_FOLDER", ""), exist_ok=True)

    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()

    @app.template_filter("datefmt")
    def datefmt(value, fmt="%d %b %Y"):
        if value is None:
            return "—"
        return value.strftime(fmt)

    @app.template_filter("datetimefmt")
    def datetimefmt(value, fmt="%d %b %Y, %I:%M %p"):
        if value is None:
            return "—"
        return value.strftime(fmt)

    @app.template_filter("money")
    def money(value):
        if value is None:
            return "—"
        return f"Rs. {value:,.0f}"

    @app.context_processor
    def inject_globals():
        from app.models import Warning, PendingAlert

        unread_count = 0
        pending_count = 0
        if current_user.is_authenticated and current_user.role == "student":
            unread_count = Warning.query.filter_by(
                student_id=current_user.student.id, is_read=False
            ).count()
        if current_user.is_authenticated and current_user.role == "admin":
            pending_count = PendingAlert.query.filter_by(status="pending").count()
        return dict(unread_warnings_count=unread_count, pending_alerts_count=pending_count)

    from flask_login import current_user

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    @app.errorhandler(413)
    def too_large(e):
        from flask import flash, redirect, request

        flash("File is too large. Maximum allowed size is 16 MB.", "danger")
        return redirect(request.referrer or "/")

    return app