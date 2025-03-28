from typing import Optional

import arrow
import sqlalchemy as sa

from app import db
from app.controllers import settings
from app.controllers.user.util import get_user
from app.models import Break, Leave, Time, WhatsNew
from app.types import DayOfWeek0Indexed, TimeInSeconds
from app.viewmodels import TimeStats


def _get_first_record_time() -> int | None:
    """
    Returns the timestamp of the first time or leave record
    """
    first_time = db.session.scalars(sa.select(Time).filter(Time.user == get_user()).order_by(Time.start)).first()
    first_leave = db.session.scalars(sa.select(Leave).filter(Leave.user == get_user()).order_by(Leave.start)).first()

    to_check = []
    if first_time:
        to_check.append(first_time.start)
    if first_leave:
        to_check.append(first_leave.start)

    if not to_check:
        return None

    return min(to_check)


# TODO: Need to break this out into smaller functions
def stats() -> TimeStats:
    """Return the weekly stats"""
    from app.lib.util.date import humanize_seconds

    _settings = settings.fetch()
    _tz = _settings.timezone

    now = arrow.now(tz=_tz)
    today_start = now.replace(hour=0, minute=0, second=0)
    today_end = now.replace(hour=23, minute=59, second=59)

    # Set the start point to the first working day of the current week
    if now.weekday() != _settings.week_start_0:
        week_start = today_start.shift(weekday=_settings.week_start_0).shift(days=-7)
    else:
        week_start = today_start

    # Time logged
    entries_today = [
        *Time.between(today_start.int_timestamp, today_end.int_timestamp),
        *Leave.between(today_start.int_timestamp, today_end.int_timestamp),
    ]
    logged_today = sum([rec.logged() for rec in entries_today])

    entries_this_week = [*Time.since(week_start.int_timestamp), *Leave.since(week_start.int_timestamp)]
    logged_this_week = sum([rec.logged() for rec in entries_this_week])

    # Time to do
    current_day = now.format("dddd")
    work_days = _settings.work_days_list()
    total_work_days = _settings.total_work_days()

    todo_today = _settings.hours_per_day * 60 * 60 if current_day in work_days else 0
    todo_this_week = (_settings.hours_per_day * 60 * 60) * total_work_days

    # Time remaining
    remaining_today = todo_today - logged_today
    remaining_this_week = todo_this_week - logged_this_week

    # You can't have negative time remaining
    # Any extra time is displayed as overtime
    if remaining_today < 0:
        remaining_today = 0

    if remaining_this_week < 0:
        remaining_this_week = 0

    # Overtime (all time)
    # TODO: This is a little inefficient as it must go through all records from the beginning
    # It would probably be better to save the overtime each week in a background task
    # Though this is nice and simple
    overtime = 0

    if first_time := _get_first_record_time():
        from app.lib.util.date import calculate_expected_hours

        first_day = arrow.get(first_time).to(_tz)
        expected_hours = calculate_expected_hours(
            start=first_day,
            end=today_end,
            hours_per_day=_settings.hours_per_day,
            days_worked=_settings.work_days,
        )

        # First take off the time we _should_ have worked
        overtime = -(expected_hours * 60 * 60)  # Convert to seconds

        # Now add on what we have worked/taken as leave
        overtime += sum([rec.logged() for rec in Time.between(0, today_end.int_timestamp)])
        overtime += sum([rec.logged() for rec in Leave.between(0, today_end.int_timestamp)])

    # Calculate estimated finish time
    estimated_finish_time = "N/A"
    if _settings.is_work_day(now.weekday()):
        breaks_taken_today = db.session.scalars(
            sa.select(Break).filter(
                Break.user_id == get_user().id,
                Break.start >= today_start.int_timestamp,
                Break.start <= today_end.int_timestamp,
            )
        ).all()

        breaks_taken_today = sum(b.duration * 60 for b in breaks_taken_today)
        expected_break_duration_today = _average_break_duration_for_day(now, 2)
        expected_break_duration_today -= breaks_taken_today

        # We've already taken our expected breaks today
        if expected_break_duration_today < 0:
            expected_break_duration_today = 0

        time_left_with_breaks = remaining_today + expected_break_duration_today

        if time_left_with_breaks <= 0:
            estimated_finish_time = "Now"
        else:
            estimated_finish_time = now.shift(seconds=time_left_with_breaks).format("HH:mm")

    return TimeStats(
        logged_this_week=humanize_seconds(logged_this_week, short=True),
        logged_today=humanize_seconds(logged_today, short=True),
        remaining_this_week=humanize_seconds(remaining_this_week, short=True),
        remaining_today=humanize_seconds(remaining_today, short=True),
        overtime=humanize_seconds(overtime, short=True),
        estimated_finish_time=estimated_finish_time,
    )


def week_list() -> list[str]:
    """
    Returns a list of weeks since the first record in the format ${year}-W${week}, eg. 2022-W25
    """
    _settings = settings.fetch()
    _tz = _settings.timezone

    # TODO: How do we view future logs?
    first_time = _get_first_record_time()
    if not first_time:
        return []

    first = arrow.get(first_time)
    now = arrow.now(tz=_tz)

    # Adjust the starting day to the first working day of the week
    while first.weekday() > _settings.week_start_0:
        first = first.shift(days=-1)

    # Go through each week since the first time record until now
    weeks = []
    while first <= now:
        weeks.append(first.format("W").rsplit("-", 1)[0])
        first = first.shift(weeks=1)

    return list(reversed(weeks))


def whats_new(limit: Optional[int] = None) -> list[WhatsNew]:
    user = get_user()

    whats_new = db.session.query(WhatsNew).order_by(WhatsNew.id.desc())

    new = whats_new.all()
    if not new:
        return []

    # Update the users last seen "What's New"
    latest_new = new[0]
    if not user.last_seen_whats_new or latest_new.id > user.last_seen_whats_new:
        user.last_seen_whats_new = latest_new.id
        db.session.commit()

    return new


def _average_break_duration_for_day(now: arrow.Arrow, day: DayOfWeek0Indexed) -> TimeInSeconds:
    """
    Get the average total break duration for a given day over the last 5 weeks
    """
    break_durations = []

    while now.weekday() != day:
        now = now.shift(days=-1)

    for _ in range(5):
        now = now.shift(weeks=-1)
        start = now.replace(hour=0, minute=0, second=0).int_timestamp
        end = now.replace(hour=23, minute=59, second=59).int_timestamp

        breaks = db.session.scalars(
            sa.select(Break).filter(
                Break.user_id == get_user().id,
                Break.start >= start,
                Break.start <= end,
            )
        ).all()

        if not breaks:
            continue

        break_durations.append(sum(b.duration for b in breaks))

    if not break_durations:
        return 0

    average_breaks_for_day = int(sum(break_durations) / len(break_durations))
    return average_breaks_for_day
