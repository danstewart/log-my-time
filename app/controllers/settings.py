import sqlalchemy as sa
from flask import abort

from app import db
from app.lib.logger import get_logger
from app.models import Settings

logger = get_logger(__name__)


def fetch() -> Settings:
    from app.controllers.user.util import get_user

    user = get_user()
    settings = db.session.scalars(sa.select(Settings).filter(Settings.user == user)).first()

    if not settings:
        # These are the default settings
        settings = Settings(
            timezone="Europe/London",
            week_start=1,  # Monday
            hours_per_day=7.5,
            work_days="MTWTF--",
            user_id=user.id,
        )
        db.session.add(settings)
        db.session.commit()
    return settings


def update(**values):
    """Updates the settings row"""
    from app.controllers.user.util import get_user

    user = get_user()
    settings = db.session.scalars(sa.select(Settings).filter(Settings.user == user)).first()

    if not settings:
        abort(403)

    work_days = []
    has_work_days = False
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
        if values.get("work_day_" + day):
            work_days.append(day[0])
            values.pop("work_day_" + day)
            has_work_days = True
        else:
            work_days.append("-")

    # Only update if we have passed work days
    if has_work_days:
        values["work_days"] = "".join(work_days)

    settings.update(**values)
    db.session.commit()


def add_whats_new(title: str, content: str):
    import arrow

    from app.models import WhatsNew

    whats_new = WhatsNew(title=title, content=content, created_at=arrow.utcnow().int_timestamp)
    db.session.add(whats_new)
    db.session.commit()
