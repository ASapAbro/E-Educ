from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.course import Course
from app.models.enrollment import Enrollment, EnrollmentError
from app.utils.decorators import roles_required

student_bp = Blueprint("student", __name__, url_prefix="/etudiant")


@student_bp.route("/formations")
@login_required
@roles_required("etudiant")
def courses_catalog():
    search = request.args.get("q", "").strip() or None
    categorie = request.args.get("categorie", "").strip() or None
    prix_max = request.args.get("prix_max", "").strip() or None
    sort_field = request.args.get("sort", "date_debut")
    courses = Course.find_all(
        search=search, categorie=categorie, statut="ouverte",
        prix_max=prix_max, sort_field=sort_field, sort_dir=1,
    )
    mes_inscriptions = {
        str(i["formation_id"]) for i in Enrollment.find_by_student(current_user.ref_id)
        if i["statut"] == "active"
    }
    for c in courses:
        c["nb_inscrits"] = Enrollment.count_active_for_course(c["_id"])
        c["deja_inscrit"] = str(c["_id"]) in mes_inscriptions
        c["complet"] = c["nb_inscrits"] >= c["capacite_max"]
    return render_template(
        "student/courses_catalog.html",
        courses=courses,
        categories=Course.distinct_categories(),
        search=search or "", categorie=categorie or "", prix_max=prix_max or "",
    )


@student_bp.route("/formations/<course_id>/inscrire", methods=["POST"])
@login_required
@roles_required("etudiant")
def enroll(course_id):
    try:
        Enrollment.create(current_user.ref_id, course_id)
        flash("Inscription réussie !", "success")
    except EnrollmentError as e:
        flash(str(e), "danger")
    return redirect(url_for("student.courses_catalog"))


@student_bp.route("/inscriptions")
@login_required
@roles_required("etudiant")
def my_enrollments():
    inscriptions = Enrollment.find_by_student(current_user.ref_id)
    return render_template("student/my_enrollments.html", inscriptions=inscriptions)


@student_bp.route("/inscriptions/<inscription_id>/annuler", methods=["POST"])
@login_required
@roles_required("etudiant")
def cancel_enrollment(inscription_id):
    try:
        Enrollment.cancel(inscription_id, etudiant_id=current_user.ref_id)
        flash("Inscription annulée.", "info")
    except EnrollmentError as e:
        flash(str(e), "danger")
    return redirect(url_for("student.my_enrollments"))


@student_bp.route("/notes")
@login_required
@roles_required("etudiant")
def my_grades():
    inscriptions = [
        i for i in Enrollment.find_by_student(current_user.ref_id)
        if i["statut"] == "active"
    ]
    moyenne = Enrollment.moyenne_etudiant(current_user.ref_id)
    return render_template("student/my_grades.html", inscriptions=inscriptions, moyenne=moyenne)
