import os 
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.environ.get("MONGO_URI")
db_name = os.environ.get("MONGO_DB_NAME")

client = MongoClient(uri, tlsCAFile=certifi.where())
db = client[db_name]

print("Connexion réussie, bases disponibles:", client.list_database_names())

collection = db["test_etudiants"]

nouveau_document = {
    "nom": "Dupont",
    "prenom": "Jean",
    "age": 22,
    "filiere": "Informatique"
}

resultat = collection.insert_one(nouveau_document)
print("Document inséré avec l'ID:", resultat.inserted_id)

document = collection.find_one({"nom": "Dupont"})
print("Document trouvé:", document)