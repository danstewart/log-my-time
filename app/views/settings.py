from decimal import Decimal

from flask import Blueprint, request

from app.controllers import settings
from app.controllers.user.util import admin_only, login_required
from app.lib.blocks import frame, render
from app.lib.logger import get_logger

v = Blueprint("settings", __name__)
logger = get_logger(__name__)


@v.route("/settings", methods=["GET", "POST"])
@v.route("/settings/general", methods=["GET", "POST"])
@login_required
@frame
def general_settings():
    if request.form:
        from flask import flash, redirect

        if request.form.get("validate"):
            from app.lib import validate as v

            validation = v.validate_form(
                values=dict(request.form),
                checks={
                    # TODO: Run this through arrow or pytz to validate
                    "timezone": v.Check(regex=r"\w+\/\w+"),
                    "holiday_location": v.Check(options=["GB/ENG", "GB/NIR", "GB/WLS", "GB/SCT"]),
                    "week_start": v.Check(options=["0", "1", "2", "3", "4", "5", "6"]),
                    "hours_per_day": v.Check(
                        func=lambda x: Decimal(x) > 0,
                        message="Must be a positive number",
                    ),
                },
            )
            return validation.errors or validation.success

        settings.update(**request.form)
        flash("Settings saved", "success")
        return redirect("/dash")

    return render("pages/settings.html.j2", settings=settings.fetch(), page="general")


@v.route("/settings/account", methods=["GET", "POST"])
@login_required
@frame
def account_settings():
    from app.controllers.user import update_email
    from app.controllers.user.util import get_user

    user = get_user()

    if request.form:
        from flask import flash, redirect

        has_changed = False
        submit = request.form.get("submit", "save")

        if submit == "delete-account":
            from app.controllers.user import delete_account, logout

            delete_account(user)
            logout()

            flash("Your account has been deleted", "success")
            return redirect("/login")
        elif submit == "export":
            from flask import make_response

            from app.controllers.user import export_data

            response = make_response(
                export_data(user),
            )
            response.headers["Content-Type"] = "application/json"
            return response

        if new_password := request.form.get("password"):
            has_changed = True
            user.set_password(new_password)
            flash("Password changed", "success")

        if new_email := request.form.get("email"):
            if new_email != user.email:
                has_changed = True
                update_email(user, new_email)
                flash("Email updated, please check your email to continue", "success")

        if not has_changed:
            flash("No changes made", "info")

        return redirect("/dash")

    return render("pages/settings.html.j2", page="account", email=user.email)


@v.route("/settings/admin", methods=["GET", "POST"])
@login_required
@admin_only
@frame
def admin_settings():
    if request.form:
        from flask import flash, redirect

        title = request.form.get("whats_new_title")
        content = request.form.get("whats_new_content")

        if not title or not content:
            flash("Please enter a title and content", "danger")
            return redirect("/settings/admin")

        settings.add_whats_new(title, content)
        flash(f"Added '{title}'", "success")

    return render("pages/settings.html.j2", page="admin")


@v.route("/settings/teams", methods=["GET", "POST"])
@login_required
@frame
def teams_list():
    return render("pages/settings.html.j2", page="teams")


@v.route("/settings/teams/add", methods=["GET", "POST"])
@login_required
@frame
def add_team():
    return render("pages/settings.html.j2", page="add_team")


@v.route("/settings/teams/invite", methods=["GET", "POST"])
@login_required
@frame
def invite_user():
    return render("pages/settings.html.j2", page="invite_user")


@v.route("/settings/teams/<string:team>", methods=["GET", "POST"])
@login_required
@frame
def team_settings(team):
    return render("pages/settings.html.j2", page="team", team=team)


@v.route("/settings/teams/<string:team>/user/<string:user>", methods=["GET", "POST"])
@login_required
@frame
def team_user_settings(team: str, user: str):
    return render("pages/settings.html.j2", page="user", team=team, user=user)
