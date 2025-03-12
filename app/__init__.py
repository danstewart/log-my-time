import os

import rollbar
import rollbar.contrib.flask
from flask import Flask, got_request_exception
from flask_alembic import Alembic
from flask_sqlalchemy_lite import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

from app.lib.util.lenient import lenient_wrap
from app.lib.util.security import MissingCSRFToken


class Model(DeclarativeBase):
    pass


Model.metadata.naming_convention = {
    "ix": "ix_%(table_name)s_%(column_0_N_label)s",
    "uq": "uc_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


db = SQLAlchemy()
alembic = Alembic(metadatas=Model.metadata)


def create_app(test_mode: bool = False):
    app = Flask(__name__)
    app.config.from_pyfile("../config/app_config.py")

    app.config.update(
        SESSION_COOKIE_SECURE=not bool(os.getenv("FLASK_DEBUG")),  # Cookies are secure when not running debug mode
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    # Initialise database
    app.config["SQLALCHEMY_ENGINES"] = {"default": "sqlite:////home/app/log-my-time/db/time.db"}

    if test_mode or os.getenv("TEST_MODE") == "yes":
        app.testing = True
        app.config["SQLALCHEMY_ENGINES"] = {"default": "sqlite:////home/app/log-my-time/db/time.test.db"}

    db.init_app(app)
    alembic.init_app(app)

    app.jinja_env.add_extension("jinja2.ext.do")
    app.jinja_env.add_extension("jinja2.ext.loopcontrols")
    app.jinja_env.add_extension("jinja2.ext.debug")
    app.jinja_env.globals["lenient_wrap"] = lenient_wrap

    with app.app_context():
        from app.cli import data
        from app.lib.util.security import enable_csrf_protection
        from app.views import callback, core, holidays, leave, settings, time, user

        init_rollbar(app)
        enable_csrf_protection(app)

        app.register_blueprint(time.v)
        app.register_blueprint(leave.v)
        app.register_blueprint(settings.v)
        app.register_blueprint(user.v)
        app.register_blueprint(core.v)
        app.register_blueprint(data.v)
        app.register_blueprint(callback.v)

        app.register_blueprint(holidays.v)

        add_error_handlers(app)
        add_globals(app)
        add_jinja_filters(app)

    return app


def init_rollbar(app):
    if not app.config.get("ROLLBAR_SERVER_TOKEN"):
        return

    if app.testing:
        return

    if os.getenv("ENVIRONMENT") == "local":
        return

    rollbar.init(
        app.config["ROLLBAR_SERVER_TOKEN"],
        os.getenv("ENVIRONMENT", "local"),
        root=os.path.dirname(os.path.realpath(__file__)),
        allow_logging_basic_config=False,
    )

    def inject_user_to_rollbar_payload(payload, **kw):
        from app.controllers.user.util import get_user, is_logged_in

        if is_logged_in():
            u = get_user()
            payload["data"]["user_id"] = u.id

        return payload

    got_request_exception.connect(rollbar.contrib.flask.report_exception, app)
    got_request_exception.connect(rollbar.contrib.flask.report_exception, app)
    got_request_exception.connect(rollbar.contrib.flask.report_exception, app)
    rollbar.events.add_payload_handler(inject_user_to_rollbar_payload)


def add_error_handlers(app):
    @app.errorhandler(MissingCSRFToken)
    def handle_missing_csrf_token(e):
        from flask import make_response
        from flask import session as flask_session

        response = make_response("Missing CSRF token")
        flask_session.pop("login_session_key", None)
        response.headers["X-Dynamic-Frame-Page-Redirect"] = "/login"
        return response


def add_globals(app):
    # Inject some values into ALL templates
    @app.context_processor
    def inject_globals():
        import arrow
        from flask import has_request_context
        from flask import session as flask_session

        from app.controllers.settings import fetch
        from app.controllers.user.util import get_user, is_admin, is_logged_in, unseen_whats_new
        from app.lib.util.date import humanize_seconds
        from app.lib.util.security import get_csrf_token

        globals = {
            "theme": "light",
            "arrow": arrow,
            "humanize_seconds": humanize_seconds,
            "is_logged_in": is_logged_in(),
            "is_admin": is_logged_in() and is_admin(),
            "unseen_whats_new": is_logged_in() and unseen_whats_new(),
            "settings": None,
            "host": app.config["HOST"],
            "csrf_token": get_csrf_token,
            "FLASK_DEBUG": os.getenv("FLASK_DEBUG") == "1",
            "ROLLBAR_CLIENT_TOKEN": app.config.get("ROLLBAR_CLIENT_TOKEN"),
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "local"),
            "CF_TURNSTILE_SITE_KEY": app.config.get("CF_TURNSTILE_SITE_KEY"),
        }

        # If we have a request context then check for a theme in browser session
        if has_request_context():
            if flask_session.get("theme"):
                globals["theme"] = flask_session.get("theme")

        # If we are logged in then inject the settings
        if globals["is_logged_in"]:
            globals["settings"] = fetch()

            # Theme from settings takes priority
            if globals["settings"].theme:
                flask_session["theme"] = globals["settings"].theme
                globals["theme"] = globals["settings"].theme

            u = get_user()
            globals["user_id"] = u.id

        return globals


def add_jinja_filters(app):
    @app.template_filter("unix_to_datetime")
    def unix_to_datetime(stamp: int | None) -> str:
        import arrow

        if not stamp:
            return "None"

        return arrow.get(stamp).format("YYYY-MM-DD HH:mm")

    @app.template_filter("bool_to_icon")
    def bool_to_icon(value: bool) -> str:
        if value:
            return "<span class='bi bi-check text-success'></span>"
        return "<span class='bi bi-x text-danger'></span>"
