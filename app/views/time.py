from flask import Blueprint, redirect, render_template, request

from app.controllers import time
from app.controllers.user.util import login_required
from app.lib.logger import get_logger

v = Blueprint("time", __name__)
logger = get_logger(__name__)


@v.post("/time/add")
@login_required
def add_time():
    if request.form:

        values = dict(request.form)
        clock = values.pop("clock")

        match clock:
            case "manual":
                time.create(start=values["start"], end=values["end"] if "end" in values else None, note=values["note"])
            case "in":
                time.create(start=values["time"])
            case "out":
                time.clock_out(end=values["time"])
            case "break:start":
                time.break_start(start=values["time"])
            case "break:end":
                time.break_end(end=values["time"])

    return redirect("/dash")


@v.delete("/time/delete/<row_id>")
@login_required
def delete_time(row_id):
    time.delete(row_id)
    return "OK", 200


# FRAMES
@v.get("/frames/clock_in_form")
@login_required
def clock_in_form():
    clocked_in = time.current() is not None
    on_break = time.current_break() is not None

    return render_template("frames/clock_in_form.html.j2", clocked_in=clocked_in, on_break=on_break)


@v.route("/frames/time_form/", methods=["GET", "POST"])
@v.route("/frames/time_form/<row_id>", methods=["GET", "POST"])
@login_required
def time_form(row_id: str = ""):
    from app.lib.util.ensure import ensure_list
    from datetime import datetime

    if request.method == "POST" and request.json:
        from collections import defaultdict

        if row_id:
            time.update(
                row_id,
                start=request.json["start"],
                end=request.json["end"],
                note=request.json["note"],
            )

            breaks = defaultdict(dict)

            # Handle any edits to existing breaks
            for key, value in request.json.items():
                if key.startswith("break-"):
                    _, field, break_id = key.split("-")
                    breaks[break_id][field] = value

            time.bulk_update(table="break", data=breaks)

            # Handle any new breaks
            new_breaks_starts = ensure_list(request.json.get("new-break-start", []))
            new_breaks_ends = ensure_list(request.json.get("new-break-end", []))
            new_breaks = zip(new_breaks_starts, new_breaks_ends)

            for new_break in new_breaks:
                time.add_break(
                    time_id=row_id,
                    break_start=new_break[0],
                    break_end=new_break[1],
                )

        else:
            time.create(
                start=request.json["start"],
                end=request.json["end"],
                note=request.json["note"],
            )
        return "", 200

    return render_template(
        "frames/time_form.html.j2",
        row_id=row_id,
        time=time.get(row_id) if row_id else None,
        now=datetime.now(),
    )
