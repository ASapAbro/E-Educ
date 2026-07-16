from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import get_db

ROLES = ("admin", "formateur", "etudiant")


class User(UserMixin):
    """Wraps a document from the 'utilisateurs' collection for Flask-Login."""

    def __init__(self, doc):
        self.doc = doc

    # -- Flask-Login required interface -------------------------------
    def get_id(self):
        return str(self.doc["_id"])

    @property
    def is_active(self):
        return self.doc.get("actif", True)

    # -- Convenience accessors ------------------------------------------
    @property
    def id(self):
        return self.doc["_id"]

    @property
    def email(self):
        return self.doc["email"]

    @property
    def role(self):
        return self.doc["role"]

    @property
    def ref_id(self):
        return self.doc.get("ref_id")

    @property
    def nom_complet(self):
        return self.doc.get("nom_complet", self.email)

    def check_password(self, password):
        return check_password_hash(self.doc["password_hash"], password)

    # -- Data access ------------------------------------------------------
    @staticmethod
    def collection():
        return get_db().utilisateurs

    @classmethod
    def get_by_id(cls, user_id):
        try:
            oid = ObjectId(user_id)
        except (InvalidId, TypeError):
            return None
        doc = cls.collection().find_one({"_id": oid})
        return cls(doc) if doc else None

    @classmethod
    def get_by_email(cls, email):
        doc = cls.collection().find_one({"email": email.lower().strip()})
        return cls(doc) if doc else None

    @classmethod
    def create(cls, email, password, role, ref_id=None, nom_complet=None):
        if role not in ROLES:
            raise ValueError("Rôle invalide")
        doc = {
            "email": email.lower().strip(),
            "password_hash": generate_password_hash(password),
            "role": role,
            "ref_id": ref_id,
            "nom_complet": nom_complet,
            "actif": True,
            "date_creation": datetime.now(timezone.utc),
        }
        result = cls.collection().insert_one(doc)
        doc["_id"] = result.inserted_id
        return cls(doc)

    @classmethod
    def email_exists(cls, email):
        return cls.collection().count_documents({"email": email.lower().strip()}) > 0

    @classmethod
    def set_active(cls, user_id, actif):
        cls.collection().update_one({"_id": ObjectId(user_id)}, {"$set": {"actif": actif}})

    @classmethod
    def find_all(cls):
        return list(cls.collection().find().sort("date_creation", -1))

    @classmethod
    def delete_by_ref(cls, ref_id):
        cls.collection().delete_many({"ref_id": ObjectId(ref_id)})
