import datetime as dt

from bson import ObjectId

from app.extensions import get_db


def _to_datetime(value):
    """BSON only stores datetime.datetime, not datetime.date (WTForms DateField)."""
    if isinstance(value, dt.datetime):
        return value
    if isinstance(value, dt.date):
        return dt.datetime.combine(value, dt.time.min)
    return value


class Course:
    """Data-access helper for the 'formations' collection."""

    @staticmethod
    def collection():
        return get_db().formations

    @classmethod
    def create(cls, titre, description, categorie, prix, duree, capacite_max,
               formateur_id, date_debut, date_fin, statut="ouverte"):
        doc = {
            "titre": titre.strip(),
            "description": description.strip(),
            "categorie": categorie.strip(),
            "prix": float(prix),
            "duree": int(duree),
            "capacite_max": int(capacite_max),
            "formateur_id": ObjectId(formateur_id),
            "date_debut": _to_datetime(date_debut),
            "date_fin": _to_datetime(date_fin),
            "statut": statut,
            "date_creation": dt.datetime.now(dt.timezone.utc),
        }
        result = cls.collection().insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    @classmethod
    def get_by_id(cls, course_id):
        try:
            return cls.collection().find_one({"_id": ObjectId(course_id)})
        except Exception:
            return None

    @classmethod
    def get_with_formateur(cls, course_id):
        try:
            oid = ObjectId(course_id)
        except Exception:
            return None
        pipeline = [
            {"$match": {"_id": oid}},
            {"$lookup": {
                "from": "formateurs",
                "localField": "formateur_id",
                "foreignField": "_id",
                "as": "formateur",
            }},
            {"$unwind": {"path": "$formateur", "preserveNullAndEmptyArrays": True}},
        ]
        results = list(cls.collection().aggregate(pipeline))
        return results[0] if results else None

    @classmethod
    def update(cls, course_id, data):
        data = {k: v for k, v in data.items() if v is not None}
        if "formateur_id" in data:
            data["formateur_id"] = ObjectId(data["formateur_id"])
        if "prix" in data:
            data["prix"] = float(data["prix"])
        if "duree" in data:
            data["duree"] = int(data["duree"])
        if "capacite_max" in data:
            data["capacite_max"] = int(data["capacite_max"])
        if "date_debut" in data:
            data["date_debut"] = _to_datetime(data["date_debut"])
        if "date_fin" in data:
            data["date_fin"] = _to_datetime(data["date_fin"])
        cls.collection().update_one({"_id": ObjectId(course_id)}, {"$set": data})

    @classmethod
    def delete(cls, course_id):
        cls.collection().delete_one({"_id": ObjectId(course_id)})

    @classmethod
    def has_enrollments(cls, course_id):
        return get_db().inscriptions.count_documents(
            {"formation_id": ObjectId(course_id), "statut": "active"}
        ) > 0

    @classmethod
    def find_all(cls, search=None, categorie=None, formateur_id=None, statut=None,
                  prix_min=None, prix_max=None, sort_field="date_debut", sort_dir=1):
        query = {}
        if search:
            query["$or"] = [
                {"titre": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
            ]
        if categorie:
            query["categorie"] = categorie
        if formateur_id:
            query["formateur_id"] = ObjectId(formateur_id)
        if statut:
            query["statut"] = statut
        if prix_min is not None or prix_max is not None:
            prix_query = {}
            if prix_min is not None:
                prix_query["$gte"] = float(prix_min)
            if prix_max is not None:
                prix_query["$lte"] = float(prix_max)
            query["prix"] = prix_query

        pipeline = [
            {"$match": query},
            {"$lookup": {
                "from": "formateurs",
                "localField": "formateur_id",
                "foreignField": "_id",
                "as": "formateur",
            }},
            {"$unwind": {"path": "$formateur", "preserveNullAndEmptyArrays": True}},
            {"$sort": {sort_field: sort_dir}},
        ]
        return list(cls.collection().aggregate(pipeline))

    @classmethod
    def find_by_formateur(cls, formateur_id):
        return list(cls.collection().find({"formateur_id": ObjectId(formateur_id)}).sort("date_debut", -1))

    @classmethod
    def count(cls):
        return cls.collection().count_documents({})

    @classmethod
    def distinct_categories(cls):
        return sorted(cls.collection().distinct("categorie"))

    @classmethod
    def count_by_categorie(cls):
        pipeline = [
            {"$group": {"_id": "$categorie", "total": {"$sum": 1}}},
            {"$sort": {"total": -1}},
        ]
        return list(cls.collection().aggregate(pipeline))

    @classmethod
    def prix_moyen(cls):
        pipeline = [{"$group": {"_id": None, "moyenne": {"$avg": "$prix"}}}]
        result = list(cls.collection().aggregate(pipeline))
        return round(result[0]["moyenne"], 2) if result else 0
