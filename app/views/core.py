from flask import Blueprint, render_template, request

from app.controllers import core, leave, time
from app.controllers.user.util import login_required
from app.lib.logger import get_logger

v = Blueprint("core", __name__)
logger = get_logger(__name__)


@v.get("/")
def home():
    from flask import current_app as app

    return app.send_static_file("html/home.html")


@v.get("/dash")
@login_required
def dash():
    return render_template(
        "pages/dash.html.j2",
        week_list=core.week_list(),
    )


@v.get("/whats_new")
@login_required
def whats_new():
    return render_template(
        "pages/whats_new.html.j2",
        whats_new=core.whats_new(),
    )


@v.get("/contact")
def contact_page():
    return render_template("pages/contact.html.j2")


@v.get("/about")
def about_page():
    return render_template("pages/about.html.j2")


@v.get("/privacy")
def privacy_page():
    return render_template("pages/privacy.html.j2")


# FRAMES
@v.get("/frames/entries")
@login_required
def time_log_table():
    week_number = request.args.get("week")

    time_entries = time.all_for_week(week_number)
    leave_entries = leave.all_for_week(week_number)

    records = sorted((time_entries + leave_entries), key=lambda x: x.start, reverse=True)

    return render_template("frames/entries_table.html.j2", records=records, type_of=lambda thing: type(thing).__name__)


@v.get("/frames/stats")
@login_required
def stats():
    time_stats = core.stats()
    return render_template("frames/time_stats.html.j2", stats=time_stats)
