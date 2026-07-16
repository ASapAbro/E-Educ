from flask_login import LoginManager
from flask_wtf import CSRFProtect
from pymongo import MongoClient

login_manager = LoginManager()
csrf = CSRFProtect()

_client = None
_db = None


def init_mongo(app):
    global _client, _db
    _client = MongoClient(app.config["MONGO_URI"])
    _db = _client[app.config["MONGO_DB_NAME"]]
    app.mongo_client = _client
    app.db = _db
    return _db


def get_db():
    """Return the active MongoDB database handle."""
    if _db is None:
        raise RuntimeError("MongoDB non initialisé. Appelez init_mongo(app) d'abord.")
    return _db


@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User

    return User.get_by_id(user_id)
