# Plateforme de Gestion de Formations — École (Projet Master 1)

Application web complète permettant à une école de gérer ses étudiants, ses
formateurs, ses formations et les inscriptions aux formations, avec
authentification par rôles (administrateur, formateur, étudiant).

- **Backend / Frontend** : Python 3, Flask, Jinja2, Bootstrap 5, Chart.js
- **Base de données** : MongoDB (PyMongo, sans ORM)
- **Authentification** : Flask-Login (sessions), mots de passe hachés (Werkzeug PBKDF2)
- **Formulaires / sécurité** : Flask-WTF (validation + protection CSRF)

## 1. Structure du projet

```
.
├── app/
│   ├── __init__.py            # application factory Flask
│   ├── extensions.py          # connexion MongoDB, Flask-Login, CSRF
│   ├── models/                # accès aux données (etudiants, formateurs, formations, inscriptions, users)
│   ├── forms/                 # formulaires WTForms (validation + CSRF)
│   ├── routes/                # blueprints : auth, admin, formateur, etudiant, dashboard, main
│   ├── templates/              # gabarits Jinja2 (Bootstrap 5)
│   ├── static/                 # CSS
│   └── utils/                  # décorateurs de rôles, génération de mots de passe
├── scripts/
│   ├── seed_data.py            # génération/peuplement de la base (Faker)
│   ├── create_indexes.py       # création des index MongoDB
│   └── performance_explain.py  # comparaison COLLSCAN vs IXSCAN (explain)
├── docs/                       # cahier des charges, modèle de données, cas d'utilisation
├── report/                     # rapport technique
├── config.py
├── run.py
├── requirements.txt
└── .env.example
```

## 2. Prérequis

- Python 3.10+
- MongoDB en cours d'exécution (local sur `mongodb://localhost:27017`, ou une
  instance MongoDB Atlas)

## 3. Installation

```bash
# 1. Cloner le dépôt puis se placer dans le dossier du projet
cd "ProjetM1(02)"

# 2. Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate      # Windows : venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Copier le fichier d'environnement et l'adapter si besoin
cp .env.example .env
```

Le fichier `.env` contient :

```
FLASK_SECRET_KEY=change-this-secret-key-in-production
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=ecole_formation
```

## 4. Peuplement de la base de données

```bash
# Génère 20 formateurs, 100 étudiants, 30 formations et 200 inscriptions
python scripts/seed_data.py

# Pour repartir d'une base vide avant de la repeupler :
python scripts/seed_data.py --reset

# Création des index (email uniques, index composés, etc.)
python scripts/create_indexes.py

# (Optionnel) Démonstration COLLSCAN vs IXSCAN avec explain("executionStats")
python scripts/performance_explain.py
```

## 5. Lancer l'application

```bash
python run.py
```

L'application est accessible sur **http://localhost:5000**.

## 6. Comptes de démonstration

Générés par `scripts/seed_data.py` :

| Rôle       | Email                                    | Mot de passe    |
|------------|-------------------------------------------|-----------------|
| Admin      | admin@ecole-formation.edu                         | Admin123!       |
| Formateur  | (voir liste dans la collection `utilisateurs`, rôle `formateur`) | Formateur123!   |
| Étudiant   | (voir liste dans la collection `utilisateurs`, rôle `etudiant`)  | Etudiant123!    |

Pour retrouver rapidement un email de démonstration :

```js
// dans mongosh
use ecole_formation
db.utilisateurs.findOne({ role: "formateur" })
db.utilisateurs.findOne({ role: "etudiant" })
```

Lorsqu'un administrateur crée un nouvel étudiant ou formateur depuis
l'interface, un compte de connexion est automatiquement créé avec un mot de
passe temporaire généré aléatoirement, affiché une seule fois dans le message
de confirmation.

## 7. Fonctionnalités principales

- **Authentification & rôles** : connexion/déconnexion, sessions Flask-Login,
  mots de passe hachés, routes protégées par rôle (`@roles_required`).
- **Administrateur** : CRUD complet étudiants / formateurs / formations,
  gestion des inscriptions (annulation), gestion des comptes utilisateurs,
  tableau de bord avec statistiques et graphiques.
- **Formateur** : consultation de ses formations, liste des étudiants
  inscrits, attribution/modification des notes (0 à 20), consultation des
  moyennes par formation.
- **Étudiant** : recherche/filtrage des formations, inscription, annulation
  (si non notée), consultation de ses inscriptions, de ses notes et de sa
  moyenne générale.

## 8. Règles de gestion appliquées

- Emails étudiants et formateurs uniques (contrainte applicative + index
  MongoDB unique).
- Un étudiant ne peut avoir qu'une seule inscription **active** à une même
  formation (vérifié en base par un index unique partiel
  `{etudiant_id, formation_id}` filtré sur `statut = "active"`).
- Une formation ne peut pas dépasser sa `capacite_max` d'inscriptions actives.
- Une note doit être comprise entre 0 et 20.
- Un étudiant ne voit que ses propres inscriptions/notes.
- Un formateur ne peut noter que les étudiants inscrits à l'une de ses
  formations (vérifié côté serveur, indépendamment de l'interface).
- Seul un administrateur peut supprimer un étudiant, un formateur ou une
  formation.
- La suppression d'une formation ou d'un formateur est bloquée si des
  inscriptions actives / formations y sont encore rattachées.

## 9. Sécurité

- **Mots de passe** hachés avec `werkzeug.security.generate_password_hash`
  (PBKDF2-SHA256, salé).
- **CSRF** : jeton anti-CSRF sur tous les formulaires via Flask-WTF.
- **Injection** : toutes les requêtes MongoDB utilisent des requêtes
  paramétrées via PyMongo (dictionnaires Python), jamais de concaténation de
  chaînes -> pas d'injection NoSQL possible par construction.
- **XSS** : l'auto-échappement de Jinja2 est activé par défaut sur toutes
  les données affichées (`{{ variable }}`), ce qui joue le même rôle que
  `htmlspecialchars()` en PHP : les caractères spéciaux HTML (`<`, `>`, `&`,
  `"`, `'`) sont automatiquement convertis en entités, empêchant l'injection
  de scripts dans les pages.
- **Sessions** : cookies de session `HttpOnly` et `SameSite=Lax`.
- **Autorisations** : décorateur `@roles_required(...)` sur chaque route
  sensible ; les formateurs ne peuvent agir que sur leurs propres formations
  (vérification de propriété côté serveur), les étudiants uniquement sur
  leurs propres inscriptions.

## 10. Modèle de données MongoDB

Voir [`docs/modele_donnees.md`](docs/modele_donnees.md) pour le détail des
collections et la justification des choix (références plutôt que documents
imbriqués).

## 11. Tests manuels effectués

Voir la section « Tests » du rapport technique
([`report/RAPPORT_TECHNIQUE.md`](report/RAPPORT_TECHNIQUE.md)).

## 12. Auteurs / organisation du travail

- **Étudiant 1** — Base de données & backend : modélisation MongoDB,
  collections, script de peuplement, CRUD, agrégations, index et
  performances (`app/models/`, `scripts/`).
- **Étudiant 2** — Architecture applicative : authentification, rôles,
  règles de gestion, sécurité (`app/routes/`, `app/forms/`, `app/utils/`).
- **Étudiant 3** — Interface & statistiques : gabarits HTML/CSS, tableau de
  bord, graphiques, tests fonctionnels, documentation
  (`app/templates/`, `docs/`, `report/`).
