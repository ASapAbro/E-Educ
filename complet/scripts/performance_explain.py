#!/usr/bin/env python3
"""
Compare les performances d'une requête AVANT et APRES la création d'un index,
en utilisant explain("executionStats") pour observer la bascule
COLLSCAN (parcours complet de la collection) -> IXSCAN (utilisation de l'index).

Deux scénarios sont testés :
  1. etudiants.find({"email": ...})                -> index simple unique
  2. inscriptions.find({"formation_id":..., "statut": "active"}) -> index composé

Usage : python scripts/performance_explain.py
Prérequis : la base doit être peuplée (scripts/seed_data.py).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import ASCENDING, MongoClient

from config import Config


def get_db():
    client = MongoClient(Config.MONGO_URI)
    return client[Config.MONGO_DB_NAME]


def explain_find(db, collection_name, query):
    return db.command(
        "explain",
        {"find": collection_name, "filter": query},
        verbosity="executionStats",
    )


def summarize(explain_result):
    stats = explain_result["executionStats"]
    winning_plan = explain_result["queryPlanner"]["winningPlan"]
    stage = winning_plan.get("inputStage", winning_plan).get("stage", winning_plan.get("stage"))
    return {
        "stage": stage,
        "nReturned": stats["nReturned"],
        "totalDocsExamined": stats["totalDocsExamined"],
        "totalKeysExamined": stats["totalKeysExamined"],
        "executionTimeMillis": stats["executionTimeMillis"],
    }


def print_summary(label, summary):
    print(f"  [{label}]")
    print(f"    Stage MongoDB (plan gagnant)  : {summary['stage']}")
    print(f"    Documents examinés            : {summary['totalDocsExamined']}")
    print(f"    Clés d'index examinées        : {summary['totalKeysExamined']}")
    print(f"    Documents retournés            : {summary['nReturned']}")
    print(f"    Temps d'exécution (ms)         : {summary['executionTimeMillis']}")


def scenario_email(db):
    print("\n=== Scénario 1 : recherche d'un étudiant par email ===")
    sample = db.etudiants.find_one()
    if not sample:
        print("Aucun étudiant en base. Exécutez d'abord scripts/seed_data.py.")
        return
    email = sample["email"]
    query = {"email": email}

    db.etudiants.drop_index("uniq_email_etudiant") if "uniq_email_etudiant" in [
        i["name"] for i in db.etudiants.list_indexes()
    ] else None

    before = explain_find(db, "etudiants", query)
    print_summary("AVANT index (COLLSCAN attendu)", summarize(before))

    db.etudiants.create_index([("email", ASCENDING)], unique=True, name="uniq_email_etudiant")

    after = explain_find(db, "etudiants", query)
    print_summary("APRES index (IXSCAN attendu)", summarize(after))


def scenario_inscriptions(db):
    print("\n=== Scénario 2 : inscriptions actives d'une formation ===")
    sample = db.formations.find_one()
    if not sample:
        print("Aucune formation en base. Exécutez d'abord scripts/seed_data.py.")
        return
    query = {"formation_id": sample["_id"], "statut": "active"}

    # On retire temporairement TOUS les index (hors _id) de 'inscriptions' pour
    # garantir un COLLSCAN authentique : sinon un autre index déjà présent
    # (ex. idx_formation_id) pourrait être choisi par l'optimiseur et fausser
    # la comparaison "avant / après" de ce scénario précis.
    existing_indexes = [i["name"] for i in db.inscriptions.list_indexes() if i["name"] != "_id_"]
    for name in existing_indexes:
        db.inscriptions.drop_index(name)

    before = explain_find(db, "inscriptions", query)
    print_summary("AVANT index composé (COLLSCAN attendu)", summarize(before))

    idx_name = "idx_formation_statut"
    db.inscriptions.create_index(
        [("formation_id", ASCENDING), ("statut", ASCENDING)], name=idx_name
    )

    after = explain_find(db, "inscriptions", query)
    print_summary("APRES index composé (IXSCAN attendu)", summarize(after))

    print("\n  (Les autres index de 'inscriptions' ont été supprimés pour ce test.")
    print("   Relancez scripts/create_indexes.py pour tous les recréer.)")


def main():
    db = get_db()
    print(f"Analyse des performances sur la base '{db.name}'...")
    scenario_email(db)
    scenario_inscriptions(db)
    print("\nConclusion : l'utilisation d'un index réduit fortement le nombre de documents")
    print("examinés (totalDocsExamined) et le temps d'exécution, en remplaçant un")
    print("parcours complet (COLLSCAN) par un accès direct via l'index (IXSCAN).")


if __name__ == "__main__":
    main()
