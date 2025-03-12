import sqlalchemy as sa
from flask import current_app as app
from flask import render_template

from app import db
from app.controllers.user.exceptions import UserAlreadyExistsError, UserAuthFailed, UserNotVerifiedError
from app.controllers.user.token import create_token
from app.lib.email import send_email
from app.models import LoginSession, User


def register(email: str, password: str) -> User:
    """
    Registers and returns a new user
    If the email is already in use, a UserAlreadyExistsError is raised
    """
    user = db.session.scalars(sa.select(User).filter_by(email=email)).one_or_none()

    # If a user already exists with this email then send them a password reset link instead
    if user:
        reset_token = create_token(
            {
                "type": "password-reset",
                "user_id": user.id,
            }
        )
        send_email(
            to_email=email,
            subject="Welcome to LogMyTime",
            html=render_template(
                "email/account_exists.html.j2",
                password_reset_url=f"{app.config['HOST']}/password-reset/{reset_token}",
            ),
        )
        raise UserAlreadyExistsError(email)

    # Otherwise create the new user
    new_user = User(email=email).set_password(password)
    db.session.add(new_user)
    db.session.commit()

    verify_token = create_token(
        payload={
            "type": "verify",
            "user_id": new_user.id,
        },
        timeout=604800,  # 7 days
    )

    send_email(
        to_email=email,
        subject="Welcome to LogMyTime",
        html=render_template(
            "email/welcome.html.j2",
            verify_url=f"{app.config['HOST']}/verify/{verify_token}",
        ),
    )

    return new_user


def login(email: str, password: str) -> LoginSession:
    """
    Authenticates a user and returns a LoginSession
    If the user cannot be authenticated a UserAuthFailed is raised
    If the user has not verified their email a UserNotVerifiedError is raised
    """
    import secrets

    import arrow

    from app.lib.util.security import generate_csrf_token

    user = db.session.scalars(sa.select(User).filter_by(email=email)).one_or_none()

    if not user:
        raise UserAuthFailed("User not found")

    if not user.verified:
        raise UserNotVerifiedError("User not verified")

    ok = user.check_password(password)
    if not ok:
        raise UserAuthFailed("Password mismatch")

    # Generate a new CSRF token for this session
    generate_csrf_token(user.id)

    # Log in
    session = LoginSession(
        key=secrets.token_hex(),
        expires=arrow.utcnow().shift(hours=7 * 24).int_timestamp,
        user_id=user.id,
    )

    # Set the last login time
    user.last_login_at = arrow.utcnow().int_timestamp

    # Clean up any expired sessions
    now = arrow.utcnow().int_timestamp
    db.session.execute(sa.delete(LoginSession).where(LoginSession.expires < now))

    db.session.add(session)
    db.session.commit()
    return session


def logout():
    from flask import session as flask_session

    if login_session_key := flask_session.get("login_session_key"):
        if login_session := db.session.scalars(sa.select(LoginSession).filter_by(key=login_session_key)).first():
            db.session.delete(login_session)
            db.session.commit()
        flask_session.pop("login_session_key")


def send_password_reset(email: str):
    """
    If an email exists in the system then send a password reset email
    """
    if user := db.session.scalars(sa.select(User).filter_by(email=email)).one_or_none():
        reset_token = create_token(
            {
                "type": "password-reset",
                "user_id": user.id,
            }
        )

        send_email(
            to_email=user.email,
            subject="LogMyTime: Password Reset",
            html=render_template(
                "email/password_reset.html.j2",
                password_reset_url=f"{app.config['HOST']}/password-reset/{reset_token}",
            ),
        )


def update_email(user: User, new_email: str):
    """
    Sends a user a verification email to verify their new email address
    If not clicked then nothing is changed
    """

    # If an account already exists for this email then send a different email advising the user to use the existing account
    if existing_user := db.session.scalars(sa.select(User).where(User.email == new_email)).first():
        reset_token = create_token(
            {
                "type": "password-reset",
                "user_id": existing_user.id,
            }
        )
        send_email(
            to_email=new_email,
            subject="Email change for LogMyTime",
            html=render_template(
                "email/email_change_already_exists.html.j2",
                password_reset_url=f"{app.config['HOST']}/password-reset/{reset_token}",
            ),
        )
        return

    verify_token = create_token(
        payload={
            "type": "verify",
            "user_id": user.id,
            "new_email": new_email,
        },
        timeout=604800,  # 7 days
    )

    send_email(
        to_email=new_email,
        subject="Email change for LogMyTime",
        html=render_template(
            "email/email_change.html.j2",
            verify_url=f"{app.config['HOST']}/verify/{verify_token}",
        ),
    )


def delete_account(user: User):
    """
    Deletes a user's account
    """
    from app.models import User

    # We have cascading deletes :)
    user = db.session.scalars(sa.select(User).where(User.id == user.id)).one()
    db.session.delete(user)
    db.session.commit()


def export_data(user: User) -> str:
    import json

    from app.controllers import settings, time

    time_records = []
    for t in time.all():
        rec = t.asdict(exclude=["id", "user"])
        rec["breaks"] = []
        for brk in t.breaks:
            rec["breaks"].append(brk.asdict(exclude=["id", "time"]))

        time_records.append(rec)

    export = {
        "time": time_records,
        "settings": settings.fetch().asdict(exclude=["id", "user"]),
        "user": user.asdict(exclude=["id", "password", "settings"]),
    }

    return json.dumps(export)
