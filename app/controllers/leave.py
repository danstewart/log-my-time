from typing import Optional, Sequence

import arrow
import sqlalchemy as sa
from flask import abort

from app import db
from app.controllers import settings
from app.controllers.user.util import get_user
from app.models import Leave


def get(row_id: int) -> Leave:
    return db.session.scalars(sa.select(Leave).filter(Leave.id == row_id)).one()


def delete(row_id: int) -> bool:
    """
    Deletes a time record by ID
    Returns True if deleted and False if not
    """
    if record := db.session.scalars(sa.select(Leave).filter(Leave.id == row_id, Leave.user == get_user())).first():
        db.session.delete(record)
        db.session.commit()
        return True
    return False


def create(leave_type: str, start: int, duration: float, note: str = "", public_holiday: bool = False) -> Leave:
    _settings = settings.fetch()
    _tz = _settings.timezone
    start_dt = arrow.get(start, tzinfo=_tz).int_timestamp

    leave = Leave(
        leave_type=leave_type,
        start=start_dt,
        duration=duration,
        note=note,
        user_id=get_user().id,
        public_holiday=public_holiday,
    )
    db.session.add(leave)
    db.session.commit()

    return leave


def update(
    row_id: int, leave_type: str, start: int, duration: float, note: Optional[str] = None, public_holiday: bool = False
) -> Leave:
    leave = db.session.scalars(sa.select(Leave).where(Leave.id == row_id)).first()
    if not leave:
        abort(403)

    _settings = settings.fetch()
    _tz = _settings.timezone
    start_dt = arrow.get(start, tzinfo=_tz).int_timestamp

    leave.leave_type = leave_type
    leave.start = start_dt
    leave.duration = duration
    leave.note = note
    leave.public_holiday = public_holiday
    db.session.commit()

    return leave


def all_for_week(week: Optional[str] = None) -> Sequence[Leave]:
    """
    Return all leave records sorted by start date for the given week

    Week should be in the format ${YEAR}-W${WEEK_NUMBER}, eg 2022-W25
    """

    # TODO: A lot of duplicated logic between this and `time.all_for_week()`
    _settings = settings.fetch()
    _tz = _settings.timezone

    local_now = arrow.now(tz=_tz)

    if not week:
        now = arrow.utcnow()

        # Adjust the starting day to the first working day of the week
        while now.weekday() > _settings.week_start_0:
            now = now.shift(days=-1)

        week = now.format("W").rsplit("-", 1)[0]

    week_start = arrow.get(week)

    # Adjust for `settings.week_start`
    if _settings.week_start_0 > 0:
        week_start = week_start.shift(weekday=_settings.week_start_0)

        if _settings.week_start_0 > local_now.weekday():
            week_start = week_start.shift(weeks=-1)

    week_end = week_start.shift(days=7)

    return db.session.scalars(
        sa.select(Leave)
        .filter(
            Leave.user == get_user(),
            Leave.start >= week_start.int_timestamp,
            Leave.start < week_end.int_timestamp,
        )
        .order_by(Leave.start.desc(), Leave.id.desc())
    ).all()
