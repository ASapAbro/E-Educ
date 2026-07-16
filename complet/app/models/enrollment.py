from datetime import datetime, timezone

from bson import ObjectId

from app.extensions import get_db


class EnrollmentError(Exception):
    """Raised when a business rule prevents an enrollment operation."""


class Enrollment:
    """Data-access helper for the 'inscriptions' collection.

    Business rules enforced here:
      - a student cannot have two ACTIVE enrollments in the same course
      - a course cannot exceed its capacite_max of active enrollments
      - a grade (note) must be between 0 and 20
    """

    @staticmethod
    def collection():
        return get_db().inscriptions

    # ------------------------------------------------------------------
    @classmethod
    def create(cls, etudiant_id, formation_id):
        from app.models.course import Course

        formation = Course.get_by_id(formation_id)
        if not formation:
            raise EnrollmentError("Formation introuvable.")
        if formation.get("statut") == "fermee":
            raise EnrollmentError("Cette formation n'accepte plus d'inscriptions.")

        etudiant_oid = ObjectId(etudiant_id)
        formation_oid = ObjectId(formation_id)

        existing = cls.collection().find_one({
            "etudiant_id": etudiant_oid,
            "formation_id": formation_oid,
            "statut": "active",
        })
        if existing:
            raise EnrollmentError("Cet étudiant est déjà inscrit à cette formation.")

        nb_actifs = cls.collection().count_documents({
            "formation_id": formation_oid,
            "statut": "active",
        })
        if nb_actifs >= formation.get("capacite_max", 0):
            raise EnrollmentError("La capacité maximale de cette formation est atteinte.")

        doc = {
            "etudiant_id": etudiant_oid,
            "formation_id": formation_oid,
            "date_inscription": datetime.now(timezone.utc),
            "statut": "active",
            "note": None,
        }
        result = cls.collection().insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    @classmethod
    def cancel(cls, inscription_id, etudiant_id=None):
        query = {"_id": ObjectId(inscription_id)}
        if etudiant_id:
            query["etudiant_id"] = ObjectId(etudiant_id)
        insc = cls.collection().find_one(query)
        if not insc:
            raise EnrollmentError("Inscription introuvable.")
        if insc["statut"] == "annulee":
            raise EnrollmentError("Cette inscription est déjà annulée.")
        if insc.get("note") is not None:
            raise EnrollmentError("Impossible d'annuler une inscription déjà notée.")
        cls.collection().update_one(
            {"_id": insc["_id"]}, {"$set": {"statut": "annulee"}}
        )

    @classmethod
    def set_note(cls, inscription_id, note, formateur_id=None):
        note = float(note)
        if note < 0 or note > 20:
            raise EnrollmentError("La note doit être comprise entre 0 et 20.")
        insc = cls.collection().find_one({"_id": ObjectId(inscription_id)})
        if not insc:
            raise EnrollmentError("Inscription introuvable.")
        if formateur_id:
            from app.models.course import Course
            formation = Course.get_by_id(insc["formation_id"])
            if not formation or str(formation["formateur_id"]) != str(formateur_id):
                raise EnrollmentError("Vous ne pouvez noter que les étudiants de vos formations.")
        cls.collection().update_one(
            {"_id": insc["_id"]}, {"$set": {"note": note}}
        )

    @classmethod
    def get_by_id(cls, inscription_id):
        try:
            return cls.collection().find_one({"_id": ObjectId(inscription_id)})
        except Exception:
            return None

    # -- Listings with $lookup -----------------------------------------
    @classmethod
    def find_by_student(cls, etudiant_id):
        pipeline = [
            {"$match": {"etudiant_id": ObjectId(etudiant_id)}},
            {"$lookup": {
                "from": "formations",
                "localField": "formation_id",
                "foreignField": "_id",
                "as": "formation",
            }},
            {"$unwind": "$formation"},
            {"$lookup": {
                "from": "formateurs",
                "localField": "formation.formateur_id",
                "foreignField": "_id",
                "as": "formation.formateur",
            }},
            {"$unwind": {"path": "$formation.formateur", "preserveNullAndEmptyArrays": True}},
            {"$sort": {"date_inscription": -1}},
        ]
        return list(cls.collection().aggregate(pipeline))

    @classmethod
    def find_by_course(cls, formation_id):
        pipeline = [
            {"$match": {"formation_id": ObjectId(formation_id)}},
            {"$lookup": {
                "from": "etudiants",
                "localField": "etudiant_id",
                "foreignField": "_id",
                "as": "etudiant",
            }},
            {"$unwind": "$etudiant"},
            {"$sort": {"date_inscription": -1}},
        ]
        return list(cls.collection().aggregate(pipeline))

    @classmethod
    def count_active_for_course(cls, formation_id):
        return cls.collection().count_documents({
            "formation_id": ObjectId(formation_id), "statut": "active"
        })

    @classmethod
    def moyenne_etudiant(cls, etudiant_id):
        pipeline = [
            {"$match": {
                "etudiant_id": ObjectId(etudiant_id),
                "statut": "active",
                "note": {"$ne": None},
            }},
            {"$group": {"_id": None, "moyenne": {"$avg": "$note"}}},
        ]
        result = list(cls.collection().aggregate(pipeline))
        return round(result[0]["moyenne"], 2) if result else None

    @classmethod
    def count(cls):
        return cls.collection().count_documents({})

    @classmethod
    def count_by_statut(cls):
        pipeline = [{"$group": {"_id": "$statut", "total": {"$sum": 1}}}]
        return {row["_id"]: row["total"] for row in cls.collection().aggregate(pipeline)}

    @classmethod
    def moyenne_generale(cls):
        pipeline = [
            {"$match": {"note": {"$ne": None}}},
            {"$group": {"_id": None, "moyenne": {"$avg": "$note"}}},
        ]
        result = list(cls.collection().aggregate(pipeline))
        return round(result[0]["moyenne"], 2) if result else 0

    @classmethod
    def top_formations(cls, limit=5):
        """Top formations by number of active enrollments."""
        pipeline = [
            {"$match": {"statut": "active"}},
            {"$group": {"_id": "$formation_id", "nb_inscrits": {"$sum": 1}}},
            {"$sort": {"nb_inscrits": -1}},
            {"$limit": limit},
            {"$lookup": {
                "from": "formations",
                "localField": "_id",
                "foreignField": "_id",
                "as": "formation",
            }},
            {"$unwind": "$formation"},
            {"$project": {
                "_id": 0,
                "titre": "$formation.titre",
                "categorie": "$formation.categorie",
                "nb_inscrits": 1,
            }},
        ]
        return list(cls.collection().aggregate(pipeline))

    @classmethod
    def inscriptions_par_formation(cls):
        pipeline = [
            {"$match": {"statut": "active"}},
            {"$group": {"_id": "$formation_id", "nb_inscrits": {"$sum": 1}}},
            {"$lookup": {
                "from": "formations",
                "localField": "_id",
                "foreignField": "_id",
                "as": "formation",
            }},
            {"$unwind": "$formation"},
            {"$project": {"_id": 0, "titre": "$formation.titre", "nb_inscrits": 1}},
            {"$sort": {"nb_inscrits": -1}},
        ]
        return list(cls.collection().aggregate(pipeline))

    @classmethod
    def top_etudiants(cls, limit=5):
        """Top students by average grade (only counting graded, active enrollments)."""
        pipeline = [
            {"$match": {"statut": "active", "note": {"$ne": None}}},
            {"$group": {
                "_id": "$etudiant_id",
                "moyenne": {"$avg": "$note"},
                "nb_notes": {"$sum": 1},
            }},
            {"$sort": {"moyenne": -1}},
            {"$limit": limit},
            {"$lookup": {
                "from": "etudiants",
                "localField": "_id",
                "foreignField": "_id",
                "as": "etudiant",
            }},
            {"$unwind": "$etudiant"},
            {"$project": {
                "_id": 0,
                "nom": "$etudiant.nom",
                "prenom": "$etudiant.prenom",
                "moyenne": {"$round": ["$moyenne", 2]},
                "nb_notes": 1,
            }},
        ]
        return list(cls.collection().aggregate(pipeline))
