from datetime import datetime, timezone

from bson import ObjectId

from app.extensions import get_db


class Teacher:
    """Data-access helper for the 'formateurs' collection."""

    @staticmethod
    def collection():
        return get_db().formateurs

    @classmethod
    def create(cls, nom, prenom, email, specialite, statut="actif"):
        doc = {
            "nom": nom.strip(),
            "prenom": prenom.strip(),
            "email": email.lower().strip(),
            "specialite": specialite.strip(),
            "date_creation": datetime.now(timezone.utc),
            "statut": statut,
        }
        result = cls.collection().insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    @classmethod
    def get_by_id(cls, teacher_id):
        try:
            return cls.collection().find_one({"_id": ObjectId(teacher_id)})
        except Exception:
            return None

    @classmethod
    def get_by_email(cls, email):
        return cls.collection().find_one({"email": email.lower().strip()})

    @classmethod
    def email_exists(cls, email, exclude_id=None):
        query = {"email": email.lower().strip()}
        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        return cls.collection().count_documents(query) > 0

    @classmethod
    def update(cls, teacher_id, data):
        data = {k: v for k, v in data.items() if v is not None}
        if "email" in data:
            data["email"] = data["email"].lower().strip()
        cls.collection().update_one({"_id": ObjectId(teacher_id)}, {"$set": data})

    @classmethod
    def delete(cls, teacher_id):
        cls.collection().delete_one({"_id": ObjectId(teacher_id)})

    @classmethod
    def find_all(cls, search=None, specialite=None, statut=None, sort_field="nom", sort_dir=1):
        query = {}
        if search:
            regex = {"$regex": search, "$options": "i"}
            query["$or"] = [{"nom": regex}, {"prenom": regex}, {"email": regex}]
        if specialite:
            query["specialite"] = specialite
        if statut:
            query["statut"] = statut
        return list(cls.collection().find(query).sort(sort_field, sort_dir))

    @classmethod
    def count(cls):
        return cls.collection().count_documents({})

    @classmethod
    def distinct_specialites(cls):
        return sorted(cls.collection().distinct("specialite"))
