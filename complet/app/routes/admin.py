from bson import ObjectId
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.forms.auth_forms import UserForm
from app.forms.course_forms import CourseForm
from app.forms.student_forms import StudentForm
from app.forms.teacher_forms import TeacherForm
from app.models.course import Course
from app.models.enrollment import Enrollment, EnrollmentError
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User
from app.utils.decorators import roles_required
from app.utils.security import generate_temp_password

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _guard():
    return [login_required, roles_required("admin")]


# ======================================================================
# ETUDIANTS
# ======================================================================
@admin_bp.route("/etudiants")
@login_required
@roles_required("admin")
def students_list():
    search = request.args.get("q", "").strip() or None
    niveau = request.args.get("niveau", "").strip() or None
    statut = request.args.get("statut", "").strip() or None
    students = Student.find_all(search=search, niveau=niveau, statut=statut)
    return render_template(
        "admin/students_list.html",
        students=students,
        niveaux=Student.distinct_niveaux(),
        search=search or "",
        niveau=niveau or "",
        statut=statut or "",
    )


@admin_bp.route("/etudiants/ajouter", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def student_add():
    form = StudentForm()
    if form.validate_on_submit():
        if Student.email_exists(form.email.data):
            flash("Un étudiant avec cet email existe déjà.", "danger")
        elif User.email_exists(form.email.data):
            flash("Cet email est déjà utilisé par un compte utilisateur.", "danger")
        else:
            student = Student.create(
                form.nom.data, form.prenom.data, form.email.data,
                form.niveau.data, form.statut.data,
            )
            temp_password = generate_temp_password()
            User.create(
                form.email.data, temp_password, "etudiant",
                ref_id=student["_id"],
                nom_complet=f"{form.prenom.data} {form.nom.data}",
            )
            flash(
                f"Étudiant créé. Identifiants de connexion : {form.email.data} / {temp_password}",
                "success",
            )
            return redirect(url_for("admin.students_list"))
    return render_template("admin/student_form.html", form=form, title="Ajouter un étudiant")


@admin_bp.route("/etudiants/<student_id>/modifier", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def student_edit(student_id):
    student = Student.get_by_id(student_id)
    if not student:
        flash("Étudiant introuvable.", "danger")
        return redirect(url_for("admin.students_list"))
    form = StudentForm(data=student)
    if form.validate_on_submit():
        if Student.email_exists(form.email.data, exclude_id=student_id):
            flash("Un autre étudiant utilise déjà cet email.", "danger")
        else:
            Student.update(student_id, {
                "nom": form.nom.data, "prenom": form.prenom.data,
                "email": form.email.data, "niveau": form.niveau.data,
                "statut": form.statut.data,
            })
            flash("Étudiant mis à jour avec succès.", "success")
            return redirect(url_for("admin.students_list"))
    return render_template(
        "admin/student_form.html", form=form, title="Modifier l'étudiant", student=student
    )


@admin_bp.route("/etudiants/<student_id>/supprimer", methods=["POST"])
@login_required
@roles_required("admin")
def student_delete(student_id):
    Enrollment.collection().delete_many({"etudiant_id": ObjectId(student_id)})
    User.delete_by_ref(student_id)
    Student.delete(student_id)
    flash("Étudiant supprimé.", "info")
    return redirect(url_for("admin.students_list"))


# ======================================================================
# FORMATEURS
# ======================================================================
@admin_bp.route("/formateurs")
@login_required
@roles_required("admin")
def teachers_list():
    search = request.args.get("q", "").strip() or None
    specialite = request.args.get("specialite", "").strip() or None
    teachers = Teacher.find_all(search=search, specialite=specialite)
    teachers_with_courses = []
    for t in teachers:
        nb_formations = Course.collection().count_documents({"formateur_id": t["_id"]})
        teachers_with_courses.append({"teacher": t, "nb_formations": nb_formations})
    return render_template(
        "admin/teachers_list.html",
        teachers=teachers_with_courses,
        specialites=Teacher.distinct_specialites(),
        search=search or "",
        specialite=specialite or "",
    )


@admin_bp.route("/formateurs/ajouter", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def teacher_add():
    form = TeacherForm()
    if form.validate_on_submit():
        if Teacher.email_exists(form.email.data):
            flash("Un formateur avec cet email existe déjà.", "danger")
        elif User.email_exists(form.email.data):
            flash("Cet email est déjà utilisé par un compte utilisateur.", "danger")
        else:
            teacher = Teacher.create(
                form.nom.data, form.prenom.data, form.email.data,
                form.specialite.data, form.statut.data,
            )
            temp_password = generate_temp_password()
            User.create(
                form.email.data, temp_password, "formateur",
                ref_id=teacher["_id"],
                nom_complet=f"{form.prenom.data} {form.nom.data}",
            )
            flash(
                f"Formateur créé. Identifiants de connexion : {form.email.data} / {temp_password}",
                "success",
            )
            return redirect(url_for("admin.teachers_list"))
    return render_template("admin/teacher_form.html", form=form, title="Ajouter un formateur")


@admin_bp.route("/formateurs/<teacher_id>/modifier", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def teacher_edit(teacher_id):
    teacher = Teacher.get_by_id(teacher_id)
    if not teacher:
        flash("Formateur introuvable.", "danger")
        return redirect(url_for("admin.teachers_list"))
    form = TeacherForm(data=teacher)
    if form.validate_on_submit():
        if Teacher.email_exists(form.email.data, exclude_id=teacher_id):
            flash("Un autre formateur utilise déjà cet email.", "danger")
        else:
            Teacher.update(teacher_id, {
                "nom": form.nom.data, "prenom": form.prenom.data,
                "email": form.email.data, "specialite": form.specialite.data,
                "statut": form.statut.data,
            })
            flash("Formateur mis à jour avec succès.", "success")
            return redirect(url_for("admin.teachers_list"))
    return render_template(
        "admin/teacher_form.html", form=form, title="Modifier le formateur", teacher=teacher
    )


@admin_bp.route("/formateurs/<teacher_id>/supprimer", methods=["POST"])
@login_required
@roles_required("admin")
def teacher_delete(teacher_id):
    if Course.collection().count_documents({"formateur_id": ObjectId(teacher_id)}) > 0:
        flash(
            "Impossible de supprimer ce formateur : il est responsable d'au moins une formation.",
            "danger",
        )
        return redirect(url_for("admin.teachers_list"))
    User.delete_by_ref(teacher_id)
    Teacher.delete(teacher_id)
    flash("Formateur supprimé.", "info")
    return redirect(url_for("admin.teachers_list"))


# ======================================================================
# FORMATIONS
# ======================================================================
@admin_bp.route("/formations")
@login_required
@roles_required("admin")
def courses_list():
    search = request.args.get("q", "").strip() or None
    categorie = request.args.get("categorie", "").strip() or None
    statut = request.args.get("statut", "").strip() or None
    sort_field = request.args.get("sort", "date_debut")
    sort_dir = -1 if request.args.get("dir") == "desc" else 1
    courses = Course.find_all(
        search=search, categorie=categorie, statut=statut,
        sort_field=sort_field, sort_dir=sort_dir,
    )
    for c in courses:
        c["nb_inscrits"] = Enrollment.count_active_for_course(c["_id"])
    return render_template(
        "admin/courses_list.html",
        courses=courses,
        categories=Course.distinct_categories(),
        search=search or "",
        categorie=categorie or "",
        statut=statut or "",
        sort_field=sort_field,
    )


@admin_bp.route("/formations/ajouter", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def course_add():
    form = CourseForm()
    form.formateur_id.choices = [
        (str(t["_id"]), f"{t['prenom']} {t['nom']}") for t in Teacher.find_all()
    ]
    if form.validate_on_submit():
        if form.date_fin.data < form.date_debut.data:
            flash("La date de fin doit être postérieure à la date de début.", "danger")
        else:
            Course.create(
                form.titre.data, form.description.data, form.categorie.data,
                form.prix.data, form.duree.data, form.capacite_max.data,
                form.formateur_id.data, form.date_debut.data, form.date_fin.data,
                form.statut.data,
            )
            flash("Formation créée avec succès.", "success")
            return redirect(url_for("admin.courses_list"))
    return render_template("admin/course_form.html", form=form, title="Créer une formation")


@admin_bp.route("/formations/<course_id>/modifier", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def course_edit(course_id):
    course = Course.get_by_id(course_id)
    if not course:
        flash("Formation introuvable.", "danger")
        return redirect(url_for("admin.courses_list"))
    form = CourseForm(data=course)
    form.formateur_id.choices = [
        (str(t["_id"]), f"{t['prenom']} {t['nom']}") for t in Teacher.find_all()
    ]
    if request.method == "GET":
        form.formateur_id.data = str(course["formateur_id"])
    if form.validate_on_submit():
        if form.date_fin.data < form.date_debut.data:
            flash("La date de fin doit être postérieure à la date de début.", "danger")
        else:
            Course.update(course_id, {
                "titre": form.titre.data, "description": form.description.data,
                "categorie": form.categorie.data, "prix": form.prix.data,
                "duree": form.duree.data, "capacite_max": form.capacite_max.data,
                "formateur_id": form.formateur_id.data, "date_debut": form.date_debut.data,
                "date_fin": form.date_fin.data, "statut": form.statut.data,
            })
            flash("Formation mise à jour avec succès.", "success")
            return redirect(url_for("admin.courses_list"))
    return render_template(
        "admin/course_form.html", form=form, title="Modifier la formation", course=course
    )


@admin_bp.route("/formations/<course_id>")
@login_required
@roles_required("admin")
def course_detail(course_id):
    course = Course.get_with_formateur(course_id)
    if not course:
        flash("Formation introuvable.", "danger")
        return redirect(url_for("admin.courses_list"))
    inscrits = Enrollment.find_by_course(course_id)
    return render_template("admin/course_detail.html", course=course, inscrits=inscrits)


@admin_bp.route("/formations/<course_id>/supprimer", methods=["POST"])
@login_required
@roles_required("admin")
def course_delete(course_id):
    if Course.has_enrollments(course_id):
        flash(
            "Impossible de supprimer cette formation : des inscriptions actives y sont liées. "
            "Annulez-les au préalable.",
            "danger",
        )
        return redirect(url_for("admin.courses_list"))
    Enrollment.collection().delete_many({"formation_id": ObjectId(course_id)})
    Course.delete(course_id)
    flash("Formation supprimée.", "info")
    return redirect(url_for("admin.courses_list"))


# ======================================================================
# INSCRIPTIONS
# ======================================================================
@admin_bp.route("/inscriptions")
@login_required
@roles_required("admin")
def enrollments_list():
    from app.extensions import get_db

    statut = request.args.get("statut", "").strip() or None
    pipeline = []
    if statut:
        pipeline.append({"$match": {"statut": statut}})
    pipeline += [
        {"$lookup": {"from": "etudiants", "localField": "etudiant_id", "foreignField": "_id", "as": "etudiant"}},
        {"$unwind": "$etudiant"},
        {"$lookup": {"from": "formations", "localField": "formation_id", "foreignField": "_id", "as": "formation"}},
        {"$unwind": "$formation"},
        {"$sort": {"date_inscription": -1}},
        {"$limit": 300},
    ]
    inscriptions = list(get_db().inscriptions.aggregate(pipeline))
    return render_template("admin/enrollments_list.html", inscriptions=inscriptions, statut=statut or "")


@admin_bp.route("/inscriptions/<inscription_id>/annuler", methods=["POST"])
@login_required
@roles_required("admin")
def enrollment_cancel(inscription_id):
    try:
        Enrollment.cancel(inscription_id)
        flash("Inscription annulée.", "info")
    except EnrollmentError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.enrollments_list"))


# ======================================================================
# UTILISATEURS
# ======================================================================
@admin_bp.route("/utilisateurs")
@login_required
@roles_required("admin")
def users_list():
    users = User.find_all()
    return render_template("admin/users_list.html", users=users)


@admin_bp.route("/utilisateurs/ajouter", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def user_add():
    form = UserForm()
    if form.validate_on_submit():
        if User.email_exists(form.email.data):
            flash("Cet email est déjà utilisé.", "danger")
        elif not form.password.data:
            flash("Le mot de passe est obligatoire pour un nouvel utilisateur.", "danger")
        else:
            User.create(form.email.data, form.password.data, "admin", nom_complet=form.email.data)
            flash("Administrateur créé avec succès.", "success")
            return redirect(url_for("admin.users_list"))
    return render_template("admin/user_form.html", form=form, title="Ajouter un administrateur")


@admin_bp.route("/utilisateurs/<user_id>/desactiver", methods=["POST"])
@login_required
@roles_required("admin")
def user_toggle_active(user_id):
    user = User.get_by_id(user_id)
    if not user:
        flash("Utilisateur introuvable.", "danger")
    else:
        User.set_active(user_id, not user.is_active)
        flash("Statut du compte mis à jour.", "info")
    return redirect(url_for("admin.users_list"))
