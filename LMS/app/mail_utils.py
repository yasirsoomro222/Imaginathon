from pathlib import Path

from flask import current_app, render_template
from flask_mail import Message

from app import mail


def send_email(to, subject, html_body, attachment_path=None):
    """Send email via SMTP when configured; otherwise simulate to console.

    Keeps the demo fully functional without credentials.
    """
    if current_app.config.get("MAIL_SERVER") and current_app.config.get("MAIL_USERNAME"):
        try:
            msg = Message(
                subject=subject,
                recipients=[to],
                html=html_body,
                sender=current_app.config["MAIL_DEFAULT_SENDER"],
            )
            if attachment_path:
                path = Path(attachment_path)
                if path.is_file():
                    with path.open("rb") as file:
                        msg.attach(path.name, "image/jpeg", file.read())
            mail.send(msg)
            return True
        except Exception as exc:  # demo must not crash on SMTP hiccups
            current_app.logger.error("Email send failed: %s", exc)

    print(
        "\n" + "=" * 70 + f"\n[SIMULATED EMAIL]\nTo: {to}\nSubject: {subject}\n"
        + "=" * 70 + "\n",
        flush=True,
    )
    return False
