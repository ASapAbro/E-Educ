#!/usr/bin/env python3
"""
Script de génération et de peuplement de la base MongoDB 'ecole_formation'.

Génère :
  - 1 compte administrateur
  - 20 formateurs (+ comptes utilisateurs liés)
  - 100 étudiants (+ comptes utilisateurs liés)
  - 30 formations
  - 200 inscriptions (avec un mélange de statuts et de notes)

Usage :
    python scripts/seed_data.py            # ajoute les données (sans supprimer l'existant)
    python scripts/seed_data.py --reset    # vide les collections puis les repeuple
"""
import argparse
import os
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faker import Faker
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

from config import Config

fake = Faker("fr_FR")


def now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


random.seed(42)

ADMIN_EMAIL = "admin@ecole-formation.edu"
ADMIN_PASSWORD = "Admin123!"
DEMO_PASSWORD_ETUDIANT = "Etudiant123!"
DEMO_PASSWORD_FORMATEUR = "Formateur123!"

CATEGORIES = [
    "Développement Web", "Data Science", "Cybersécurité", "Cloud Computing",
    "Intelligence Artificielle", "Réseaux & Systèmes", "Design UX/UI",
    "Gestion de Projet", "Marketing Digital", "DevOps",
]

NIVEAUX = ["Licence 1", "Licence 2", "Licence 3", "Master 1", "Master 2"]

COURSE_TITLES = {
    "Développement Web": ["HTML/CSS/JS avancé", "React & applications SPA", "API REST avec Flask",
                            "Développement Full-Stack Node.js", "PHP & Laravel"],
    "Data Science": ["Introduction à la Data Science", "Python pour la data", "Machine Learning appliqué",
                       "Visualisation de données", "Statistiques pour la data science"],
    "Cybersécurité": ["Fondamentaux de la cybersécurité", "Pentest & audit de sécurité",
                        "Sécurité des applications web", "Cryptographie appliquée"],
    "Cloud Computing": ["AWS Fondamentaux", "Architecture Cloud Azure", "Kubernetes en pratique",
                          "Infrastructure as Code avec Terraform"],
    "Intelligence Artificielle": ["Introduction au Deep Learning", "NLP et traitement du langage",
                                    "Vision par ordinateur", "IA générative"],
    "Réseaux & Systèmes": ["Administration Linux", "Réseaux TCP/IP", "Virtualisation & conteneurs"],
    "Design UX/UI": ["Design d'interfaces avec Figma", "UX Research", "Design Systems"],
    "Gestion de Projet": ["Méthodes Agiles & Scrum", "Gestion de projet informatique", "Product Management"],
    "Marketing Digital": ["SEO & référencement", "Growth Hacking", "Réseaux sociaux & community management"],
    "DevOps": ["CI/CD avec GitLab", "Docker en pratique", "Monitoring & observabilité"],
}

SPECIALITES = CATEGORIES


def get_db():
    client = MongoClient(Config.MONGO_URI)
    return client[Config.MONGO_DB_NAME]


def reset_collections(db):
    for name in ("utilisateurs", "etudiants", "formateurs", "formations", "inscriptions"):
        db[name].delete_many({})
    print("Collections vidées.")


def create_admin(db):
    if db.utilisateurs.find_one({"email": ADMIN_EMAIL}):
        print(f"Admin déjà présent : {ADMIN_EMAIL}")
        return
    db.utilisateurs.insert_one({
        "email": ADMIN_EMAIL,
        "password_hash": generate_password_hash(ADMIN_PASSWORD),
        "role": "admin",
        "ref_id": None,
        "nom_complet": "Administrateur Principal",
        "actif": True,
        "date_creation": now_utc(),
    })
    print(f"Admin créé : {ADMIN_EMAIL} / {ADMIN_PASSWORD}")


def create_teachers(db, n=20):
    teachers = []
    used_emails = set()
    for i in range(n):
        prenom, nom = fake.first_name(), fake.last_name()
        email = f"{prenom.lower()}.{nom.lower()}{i}@ecole-formation.edu".replace(" ", "-")
        used_emails.add(email)
        teacher_doc = {
            "nom": nom,
            "prenom": prenom,
            "email": email,
            "specialite": random.choice(SPECIALITES),
            "statut": "actif",
            "date_creation": now_utc() - timedelta(days=random.randint(30, 900)),
        }
        result = db.formateurs.insert_one(teacher_doc)
        teacher_doc["_id"] = result.inserted_id
        teachers.append(teacher_doc)

        db.utilisateurs.insert_one({
            "email": email,
            "password_hash": generate_password_hash(DEMO_PASSWORD_FORMATEUR),
            "role": "formateur",
            "ref_id": teacher_doc["_id"],
            "nom_complet": f"{prenom} {nom}",
            "actif": True,
            "date_creation": teacher_doc["date_creation"],
        })
    print(f"{n} formateurs créés (mot de passe démo : {DEMO_PASSWORD_FORMATEUR}).")
    return teachers


def create_students(db, n=100):
    students = []
    for i in range(n):
        prenom, nom = fake.first_name(), fake.last_name()
        email = f"{prenom.lower()}.{nom.lower()}{i}@etu.ecole-formation.edu".replace(" ", "-")
        student_doc = {
            "nom": nom,
            "prenom": prenom,
            "email": email,
            "niveau": random.choice(NIVEAUX),
            "statut": random.choices(["actif", "inactif"], weights=[92, 8])[0],
            "date_creation": now_utc() - timedelta(days=random.randint(1, 700)),
        }
        result = db.etudiants.insert_one(student_doc)
        student_doc["_id"] = result.inserted_id
        students.append(student_doc)

        db.utilisateurs.insert_one({
            "email": email,
            "password_hash": generate_password_hash(DEMO_PASSWORD_ETUDIANT),
            "role": "etudiant",
            "ref_id": student_doc["_id"],
            "nom_complet": f"{prenom} {nom}",
            "actif": True,
            "date_creation": student_doc["date_creation"],
        })
    print(f"{n} étudiants créés (mot de passe démo : {DEMO_PASSWORD_ETUDIANT}).")
    return students


def create_courses(db, teachers, n=30):
    courses = []
    used_titles = set()
    for i in range(n):
        categorie = CATEGORIES[i % len(CATEGORIES)]
        candidates = [t for t in COURSE_TITLES[categorie] if t not in used_titles]
        if not candidates:
            candidates = COURSE_TITLES[categorie]
        titre = random.choice(candidates)
        used_titles.add(titre)

        formateurs_categorie = [t for t in teachers if t["specialite"] == categorie]
        formateur = random.choice(formateurs_categorie) if formateurs_categorie else random.choice(teachers)

        date_debut = now_utc() + timedelta(days=random.randint(-120, 150))
        duree_semaines = random.randint(2, 12)
        date_fin = date_debut + timedelta(weeks=duree_semaines)

        statut = "ouverte"
        if date_fin < now_utc():
            statut = "terminee"
        elif random.random() < 0.08:
            statut = "fermee"

        course_doc = {
            "titre": titre,
            "description": fake.paragraph(nb_sentences=5),
            "categorie": categorie,
            "prix": float(random.choice([199, 249, 299, 349, 399, 449, 499, 599, 699, 899])),
            "duree": duree_semaines * 10,
            "capacite_max": random.choice([15, 20, 25, 30, 35, 40]),
            "formateur_id": formateur["_id"],
            "date_debut": date_debut,
            "date_fin": date_fin,
            "statut": statut,
            "date_creation": date_debut - timedelta(days=30),
        }
        result = db.formations.insert_one(course_doc)
        course_doc["_id"] = result.inserted_id
        courses.append(course_doc)
    print(f"{n} formations créées.")
    return courses


def create_enrollments(db, students, courses, target=200):
    inscriptions = []
    active_count_by_course = {c["_id"]: 0 for c in courses}
    used_pairs = set()

    attempts = 0
    while len(inscriptions) < target and attempts < target * 20:
        attempts += 1
        student = random.choice(students)
        course = random.choice(courses)
        pair = (student["_id"], course["_id"])
        if pair in used_pairs:
            continue
        if active_count_by_course[course["_id"]] >= course["capacite_max"]:
            continue

        statut = random.choices(["active", "annulee"], weights=[88, 12])[0]
        note = None
        if statut == "active" and random.random() < 0.55:
            note = round(random.uniform(4, 20) * 2) / 2  # pas de 0.5

        doc = {
            "etudiant_id": student["_id"],
            "formation_id": course["_id"],
            "date_inscription": course["date_debut"] - timedelta(days=random.randint(1, 45)),
            "statut": statut,
            "note": note,
        }
        db.inscriptions.insert_one(doc)
        inscriptions.append(doc)
        used_pairs.add(pair)
        if statut == "active":
            active_count_by_course[course["_id"]] += 1

    print(f"{len(inscriptions)} inscriptions créées.")
    return inscriptions


def main():
    parser = argparse.ArgumentParser(description="Peuplement de la base MongoDB de l'école.")
    parser.add_argument("--reset", action="store_true", help="Vide les collections avant de les repeupler.")
    parser.add_argument("--etudiants", type=int, default=100)
    parser.add_argument("--formateurs", type=int, default=20)
    parser.add_argument("--formations", type=int, default=30)
    parser.add_argument("--inscriptions", type=int, default=200)
    args = parser.parse_args()

    db = get_db()
    print(f"Connecté à la base '{db.name}'.")

    if args.reset:
        reset_collections(db)

    create_admin(db)
    teachers = create_teachers(db, args.formateurs)
    students = create_students(db, args.etudiants)
    courses = create_courses(db, teachers, args.formations)
    create_enrollments(db, students, courses, args.inscriptions)

    print("\nPeuplement terminé.")
    print(f"  Admin      : {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"  Formateurs : <email> / {DEMO_PASSWORD_FORMATEUR}")
    print(f"  Étudiants  : <email> / {DEMO_PASSWORD_ETUDIANT}")
    print("Pensez à exécuter scripts/create_indexes.py pour créer les index.")


if __name__ == "__main__":
    main()
