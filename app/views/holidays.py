from flask import Blueprint, flash, redirect, url_for

from app.controllers import holidays, settings
from app.controllers.user.util import login_required
from app.lib.blocks import render
from app.lib.logger import get_logger
from app.viewmodels import Holiday

v = Blueprint("holidays", __name__)
logger = get_logger(__name__)


@v.get("/holidays")
@v.get("/holidays/upcoming")
@login_required
def upcoming_holidays():
    import arrow

    from app.models import Leave

    _settings = settings.fetch()

    if not _settings.holiday_location:
        flash("Please set a holiday location to view the holidays list.", "warning")
        return redirect(url_for("settings.general_settings"))

    # TODO:
    # This isn't quite right
    # One list is the list of all public holidays and the other is the list the user has actually taken off
    # We should:
    # 1. Show these lists separately
    # 2. If a user has taken a public holiday we should pull the name of that holiday into the leave list
    upcoming_holidays: list[Holiday] = []

    upcoming_public_holidays = holidays.get_upcoming_holidays()
    for date, name in upcoming_public_holidays.items():
        upcoming_holidays.append(
            Holiday(
                name=name,
                date=date,
                public=True,
                duration=1,
            )
        )

    upcoming_al = Leave.since(arrow.utcnow().int_timestamp)
    for leave in upcoming_al:
        upcoming_holidays.append(
            Holiday(
                name=leave.note or "Annual Leave",
                date=arrow.get(leave.start).date(),
                public=bool(leave.public_holiday),
                duration=leave.duration,
            )
        )

    upcoming_holidays = sorted(upcoming_holidays, key=lambda x: x.date)

    return render(
        "pages/holidays.html.j2",
        page="upcoming",
        upcoming_holidays=upcoming_holidays,
    )


@v.get("/holidays/history")
@login_required
def previous_holidays():
    _settings = settings.fetch()

    if not _settings.holiday_location:
        flash("Please set a holiday location to view the holidays list.", "warning")
        return redirect(url_for("settings.general_settings"))

    return render(
        "pages/holidays.html.j2",
        page="history",
        previous_holidays=holidays.get_previous_holidays(),
    )
