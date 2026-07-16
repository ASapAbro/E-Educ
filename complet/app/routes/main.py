from flask import Blueprint, redirect, url_for
from flask_login import current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("dashboard.admin_dashboard"))
        if current_user.role == "formateur":
            return redirect(url_for("dashboard.teacher_dashboard"))
        return redirect(url_for("dashboard.student_dashboard"))
    return redirect(url_for("auth.login"))
