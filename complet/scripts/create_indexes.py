#!/usr/bin/env python3
"""
Création des index MongoDB pour la plateforme de formation.

Index créés :
  etudiants   : email (unique)
  formateurs  : email (unique)
  formations  : categorie (simple) + statut+date_debut (composé) + texte sur titre/description
  inscriptions: etudiant_id (simple), formation_id (simple),
                (etudiant_id, formation_id) unique partiel (statut='active') -> empêche
                la double inscription active à la même formation,
                (formation_id, statut) composé -> accélère le comptage de places disponibles

Usage : python scripts/create_indexes.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import ASCENDING, TEXT
from pymongo.errors import OperationFailure

from config import Config
from pymongo import MongoClient


def get_db():
    client = MongoClient(Config.MONGO_URI)
    return client[Config.MONGO_DB_NAME]


def create_index_safe(collection, keys, **kwargs):
    try:
        name = collection.create_index(keys, **kwargs)
        print(f"  OK  {collection.name}.{name}")
    except OperationFailure as e:
        print(f"  ERREUR sur {collection.name} {keys}: {e}")


def main():
    db = get_db()
    print(f"Création des index sur la base '{db.name}'...\n")

    print("Collection 'etudiants' :")
    create_index_safe(db.etudiants, [("email", ASCENDING)], unique=True, name="uniq_email_etudiant")
    create_index_safe(db.etudiants, [("niveau", ASCENDING)], name="idx_niveau")

    print("\nCollection 'formateurs' :")
    create_index_safe(db.formateurs, [("email", ASCENDING)], unique=True, name="uniq_email_formateur")
    create_index_safe(db.formateurs, [("specialite", ASCENDING)], name="idx_specialite")

    print("\nCollection 'formations' :")
    create_index_safe(db.formations, [("categorie", ASCENDING)], name="idx_categorie")
    create_index_safe(db.formations, [("formateur_id", ASCENDING)], name="idx_formateur_id")
    create_index_safe(
        db.formations,
        [("statut", ASCENDING), ("date_debut", ASCENDING)],
        name="idx_statut_date_debut",
    )
    create_index_safe(
        db.formations,
        [("titre", TEXT), ("description", TEXT)],
        name="idx_texte_recherche",
    )

    print("\nCollection 'inscriptions' :")
    create_index_safe(db.inscriptions, [("etudiant_id", ASCENDING)], name="idx_etudiant_id")
    create_index_safe(db.inscriptions, [("formation_id", ASCENDING)], name="idx_formation_id")
    create_index_safe(
        db.inscriptions,
        [("etudiant_id", ASCENDING), ("formation_id", ASCENDING)],
        unique=True,
        partialFilterExpression={"statut": "active"},
        name="uniq_inscription_active",
    )
    create_index_safe(
        db.inscriptions,
        [("formation_id", ASCENDING), ("statut", ASCENDING)],
        name="idx_formation_statut",
    )

    print("\nIndex existants par collection :")
    for name in ("etudiants", "formateurs", "formations", "inscriptions"):
        print(f"\n  {name} :")
        for idx in db[name].list_indexes():
            print(f"    - {idx['name']} : {idx['key']}")

    print("\nTerminé.")


if __name__ == "__main__":
    main()
