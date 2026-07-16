from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.teacher import Teacher
from app.utils.decorators import roles_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/admin")
@login_required
@roles_required("admin")
def admin_dashboard():
    stats = {
        "nb_etudiants": Student.count(),
        "nb_formateurs": Teacher.count(),
        "nb_formations": Course.count(),
        "nb_inscriptions": Enrollment.count(),
        "prix_moyen": Course.prix_moyen(),
        "moyenne_generale": Enrollment.moyenne_generale(),
        "par_categorie": Course.count_by_categorie(),
        "inscriptions_par_formation": Enrollment.inscriptions_par_formation(),
        "top_formations": Enrollment.top_formations(5),
        "top_etudiants": Enrollment.top_etudiants(5),
        "par_statut_inscription": Enrollment.count_by_statut(),
    }
    return render_template("dashboard/admin_dashboard.html", stats=stats)


@dashboard_bp.route("/formateur")
@login_required
@roles_required("formateur")
def teacher_dashboard():
    mes_formations = Course.find_by_formateur(current_user.ref_id)
    formations_stats = []
    for f in mes_formations:
        nb = Enrollment.count_active_for_course(f["_id"])
        formations_stats.append({"formation": f, "nb_inscrits": nb})
    return render_template(
        "dashboard/teacher_dashboard.html", formations_stats=formations_stats
    )


@dashboard_bp.route("/etudiant")
@login_required
@roles_required("etudiant")
def student_dashboard():
    mes_inscriptions = Enrollment.find_by_student(current_user.ref_id)
    moyenne = Enrollment.moyenne_etudiant(current_user.ref_id)
    nb_actives = sum(1 for i in mes_inscriptions if i["statut"] == "active")
    return render_template(
        "dashboard/student_dashboard.html",
        inscriptions=mes_inscriptions,
        moyenne=moyenne,
        nb_actives=nb_actives,
    )
