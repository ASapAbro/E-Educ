from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.forms.auth_forms import LoginForm
from app.models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _redirect_for_role(role):
    if role == "admin":
        return redirect(url_for("dashboard.admin_dashboard"))
    if role == "formateur":
        return redirect(url_for("dashboard.teacher_dashboard"))
    return redirect(url_for("dashboard.student_dashboard"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _redirect_for_role(current_user.role)

    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_email(form.email.data)
        if user and user.is_active and user.check_password(form.password.data):
            login_user(user)
            flash(f"Bienvenue, {user.nom_complet} !", "success")
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return _redirect_for_role(user.role)
        flash("Email ou mot de passe incorrect.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for("auth.login"))
