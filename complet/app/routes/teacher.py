from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.forms.enrollment_forms import GradeForm
from app.models.course import Course
from app.models.enrollment import Enrollment, EnrollmentError
from app.utils.decorators import roles_required

teacher_bp = Blueprint("teacher", __name__, url_prefix="/formateur")


def _own_course_or_404(course_id):
    course = Course.get_by_id(course_id)
    if not course or str(course["formateur_id"]) != str(current_user.ref_id):
        abort(403)
    return course


@teacher_bp.route("/formations")
@login_required
@roles_required("formateur")
def my_courses():
    courses = Course.find_by_formateur(current_user.ref_id)
    for c in courses:
        c["nb_inscrits"] = Enrollment.count_active_for_course(c["_id"])
    return render_template("teacher/my_courses.html", courses=courses)


@teacher_bp.route("/formations/<course_id>/etudiants")
@login_required
@roles_required("formateur")
def course_students(course_id):
    course = _own_course_or_404(course_id)
    inscrits = Enrollment.find_by_course(course_id)
    moyenne_formation = None
    notes = [i["note"] for i in inscrits if i.get("note") is not None and i["statut"] == "active"]
    if notes:
        moyenne_formation = round(sum(notes) / len(notes), 2)
    return render_template(
        "teacher/course_students.html", course=course, inscrits=inscrits,
        moyenne_formation=moyenne_formation,
    )


@teacher_bp.route("/inscriptions/<inscription_id>/noter", methods=["GET", "POST"])
@login_required
@roles_required("formateur")
def grade_student(inscription_id):
    inscription = Enrollment.get_by_id(inscription_id)
    if not inscription:
        flash("Inscription introuvable.", "danger")
        return redirect(url_for("teacher.my_courses"))
    course = _own_course_or_404(inscription["formation_id"])

    form = GradeForm()
    if inscription.get("note") is not None:
        form.note.data = inscription["note"]

    if form.validate_on_submit():
        try:
            Enrollment.set_note(inscription_id, form.note.data, formateur_id=current_user.ref_id)
            flash("Note enregistrée avec succès.", "success")
            return redirect(url_for("teacher.course_students", course_id=str(course["_id"])))
        except EnrollmentError as e:
            flash(str(e), "danger")

    from app.models.student import Student
    etudiant = Student.get_by_id(inscription["etudiant_id"])
    return render_template(
        "teacher/grade_form.html", form=form, course=course,
        inscription=inscription, etudiant=etudiant,
    )
