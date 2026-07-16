# Rapport technique

## Plateforme de gestion de formations — Projet Master 1 (Développement d'une application web avec base de données NoSQL)

**Groupe :** 3 étudiants
**Base de données :** MongoDB
**Langage / framework :** Python / Flask
**Dépôt Git :** _(lien à compléter par le groupe)_

---

## Table des matières

1. Présentation du projet et analyse des besoins
2. Cahier des charges fonctionnel
3. Architecture de l'application et choix technologiques
4. Modélisation MongoDB
5. Présentation des principales fonctionnalités
6. Pipelines d'agrégation
7. Index et performances
8. Sécurité de l'application
9. Organisation du travail en équipe
10. Difficultés rencontrées et solutions apportées
11. Tests réalisés
12. Conclusion et perspectives d'évolution

---

## 1. Présentation du projet et analyse des besoins

Ce projet fait suite à un premier TP d'exploitation de MongoDB avec PHP. Il a
pour objectif de transformer cette base technique en une véritable
application web complète, sécurisée et multi-utilisateurs, destinée à une
école pour gérer ses étudiants, ses formateurs, ses formations et les
inscriptions.

Trois profils d'utilisateurs ont des besoins différents :

- Un **administrateur** doit pouvoir piloter l'ensemble des données de
  l'établissement : créer/modifier/supprimer des étudiants, des formateurs,
  des formations, gérer les inscriptions, et disposer d'une vision globale
  via un tableau de bord statistique.
- Un **formateur** a besoin d'un accès restreint à ses propres formations,
  pour consulter la liste des étudiants inscrits et leur attribuer des
  notes.
- Un **étudiant** doit pouvoir rechercher des formations, s'y inscrire,
  annuler une inscription si les règles le permettent, et suivre ses
  résultats (notes, moyenne).

L'analyse des besoins a permis de dégager cinq collections MongoDB centrales
(`utilisateurs`, `etudiants`, `formateurs`, `formations`, `inscriptions`) et
un ensemble de règles de gestion garantissant la cohérence des données
(unicité des emails, unicité des inscriptions actives, capacité maximale des
formations, plage de notes valide, etc. — voir cahier des charges).

## 2. Cahier des charges fonctionnel

Le cahier des charges détaillé (acteurs, besoins fonctionnels et non
fonctionnels, règles de gestion, contraintes techniques, livrables) est
disponible dans [`docs/cahier_des_charges.md`](../docs/cahier_des_charges.md).
Le diagramme des cas d'utilisation est disponible dans
[`docs/cas_utilisation.md`](../docs/cas_utilisation.md).

## 3. Architecture de l'application et choix technologiques

### 3.1 Choix technologiques

| Composant            | Choix                       | Justification |
|-----------------------|-----------------------------|----------------|
| Langage               | Python 3.10+                | Imposé par le groupe, lisible, écosystème riche pour Flask/PyMongo |
| Framework web          | Flask 3                     | Léger, explicite, adapté à une application avec rendu serveur (Jinja2) et un besoin pédagogique de manipuler directement MongoDB sans ORM |
| Base de données        | MongoDB (PyMongo)           | Imposée par le sujet ; PyMongo choisi plutôt qu'un ODM (MongoEngine) pour manipuler explicitement documents, requêtes et pipelines d'agrégation |
| Authentification       | Flask-Login + sessions       | Gestion standard des sessions côté serveur, intégration simple des décorateurs `@login_required` |
| Formulaires / sécurité | Flask-WTF (WTForms)         | Validation serveur + protection CSRF intégrée sur tous les formulaires |
| Rendu HTML             | Jinja2 + Bootstrap 5         | Auto-échappement XSS natif, gabarits réutilisables, interface responsive |
| Graphiques             | Chart.js (CDN)               | Simple à intégrer côté client à partir de données JSON produites par les agrégations |
| Génération de données  | Faker (locale fr_FR)         | Génération réaliste de noms, emails, textes en français |

### 3.2 Architecture applicative

L'application suit une architecture en couches, organisée en package Flask
avec **blueprints** :

```
run.py                     -> point d'entrée (app factory)
config.py                  -> configuration (variables d'environnement)
app/
 ├── extensions.py          -> connexion MongoDB (PyMongo), Flask-Login, CSRF
 ├── models/                -> couche d'accès aux données (une classe par collection métier)
 │    ├── user.py            (utilisateurs)
 │    ├── student.py         (etudiants)
 │    ├── teacher.py         (formateurs)
 │    ├── course.py          (formations)
 │    └── enrollment.py      (inscriptions + règles de gestion)
 ├── forms/                 -> validation des formulaires (WTForms)
 ├── routes/                -> contrôleurs (blueprints Flask)
 │    ├── auth.py            (connexion / déconnexion)
 │    ├── admin.py           (CRUD étudiants/formateurs/formations/inscriptions/utilisateurs)
 │    ├── teacher.py         (mes formations, notation)
 │    ├── student.py         (catalogue, inscriptions, notes)
 │    └── dashboard.py       (tableaux de bord + statistiques)
 ├── templates/              -> gabarits Jinja2 (Bootstrap 5)
 └── utils/                  -> décorateurs de rôle, génération de mots de passe
```

Cette séparation **modèles / routes / gabarits** permet à chaque membre du
groupe de travailler sur une couche indépendante (voir section 9), tout en
gardant une base de code cohérente. La logique métier sensible (unicité des
inscriptions, capacité, plage de notes) est centralisée dans
`app/models/enrollment.py` plutôt que dispersée dans les routes, afin d'être
appliquée quel que soit le point d'entrée.

### 3.3 Flux d'authentification

1. L'utilisateur soumet le formulaire de connexion (`auth.login`).
2. `User.get_by_email()` récupère le document `utilisateurs` correspondant.
3. Le mot de passe est vérifié avec `check_password_hash`.
4. Si valide, `login_user()` (Flask-Login) crée la session ; l'utilisateur
   est redirigé vers le tableau de bord correspondant à son `role`.
5. Chaque route protégée est décorée par `@login_required` puis
   `@roles_required(...)`, qui renvoie une erreur 403 si le rôle ne
   correspond pas.

## 4. Modélisation MongoDB

Voir le détail complet, les schémas de documents et la justification du
choix **références plutôt que documents imbriqués** dans
[`docs/modele_donnees.md`](../docs/modele_donnees.md).

En synthèse : les quatre entités métier (étudiants, formateurs, formations,
inscriptions) sont normalisées dans des collections séparées reliées par des
`ObjectId`, car la relation étudiant ↔ formation est **many-to-many**, à
croissance non bornée, avec des écritures fréquentes et indépendantes
(inscription, annulation, notation). Les vues composites nécessaires à
l'interface (une formation avec son formateur, une inscription avec
l'étudiant et la formation) sont reconstituées **à la lecture** via des
pipelines `$lookup`/`$unwind`, ce qui évite la duplication de données et les
incohérences de mise à jour tout en conservant des documents source
compacts.

## 5. Présentation des principales fonctionnalités

### 5.1 Authentification et rôles
Connexion/déconnexion, sessions Flask-Login, redirection automatique vers le
tableau de bord adapté au rôle, protection de toutes les routes privées.

### 5.2 Gestion des étudiants (admin)
Liste avec recherche (nom/prénom/email, expression régulière insensible à la
casse) et filtres (niveau, statut), formulaire d'ajout/modification validé
côté serveur, suppression avec nettoyage des inscriptions et du compte
utilisateur associés.

### 5.3 Gestion des formateurs (admin)
Mêmes principes que les étudiants ; affichage du nombre de formations
dont chaque formateur est responsable ; suppression bloquée si le formateur
est encore rattaché à au moins une formation.

### 5.4 Gestion des formations (admin)
Création/modification avec sélection du formateur responsable, recherche
textuelle, filtres (catégorie, statut, prix), tri (date, titre, prix),
fiche détaillée listant les inscrits. La suppression est bloquée si des
inscriptions actives existent.

### 5.5 Gestion des inscriptions
- **Étudiant** : catalogue des formations ouvertes avec indication des
  places restantes, inscription en un clic (règles de gestion vérifiées
  côté serveur), annulation si la note n'a pas encore été saisie.
- **Admin** : vue globale de toutes les inscriptions, annulation possible.
- **Formateur** : liste des inscrits par formation, saisie des notes.

### 5.6 Notation
Le formateur attribue une note (0 à 20) à un étudiant inscrit à l'une de ses
formations. La vérification de propriété (le formateur ne peut noter que ses
propres formations) est effectuée côté serveur indépendamment de
l'affichage, pour empêcher tout contournement par manipulation directe
d'URL.

### 5.7 Tableau de bord et statistiques
Voir section suivante.

## 6. Pipelines d'agrégation

Les statistiques du tableau de bord et plusieurs listages reposent sur des
pipelines d'agrégation MongoDB combinant `$match`, `$group`, `$project`,
`$sort`, `$limit`, `$lookup` et `$unwind` (voir `app/models/enrollment.py`
et `app/models/course.py`). Exemples :

**Top 5 des formations les plus demandées** (`Enrollment.top_formations`) :
```python
[
    {"$match": {"statut": "active"}},
    {"$group": {"_id": "$formation_id", "nb_inscrits": {"$sum": 1}}},
    {"$sort": {"nb_inscrits": -1}},
    {"$limit": 5},
    {"$lookup": {
        "from": "formations", "localField": "_id",
        "foreignField": "_id", "as": "formation",
    }},
    {"$unwind": "$formation"},
    {"$project": {"_id": 0, "titre": "$formation.titre",
                  "categorie": "$formation.categorie", "nb_inscrits": 1}},
]
```

**Top 5 des meilleurs étudiants** (`Enrollment.top_etudiants`) :
```python
[
    {"$match": {"statut": "active", "note": {"$ne": None}}},
    {"$group": {"_id": "$etudiant_id", "moyenne": {"$avg": "$note"},
                "nb_notes": {"$sum": 1}}},
    {"$sort": {"moyenne": -1}},
    {"$limit": 5},
    {"$lookup": {"from": "etudiants", "localField": "_id",
                 "foreignField": "_id", "as": "etudiant"}},
    {"$unwind": "$etudiant"},
    {"$project": {"_id": 0, "nom": "$etudiant.nom", "prenom": "$etudiant.prenom",
                  "moyenne": {"$round": ["$moyenne", 2]}, "nb_notes": 1}},
]
```

**Nombre de formations par catégorie** (`Course.count_by_categorie`) :
```python
[
    {"$group": {"_id": "$categorie", "total": {"$sum": 1}}},
    {"$sort": {"total": -1}},
]
```

**Fiche formation avec formateur** (`Course.get_with_formateur`) :
```python
[
    {"$match": {"_id": course_oid}},
    {"$lookup": {"from": "formateurs", "localField": "formateur_id",
                 "foreignField": "_id", "as": "formateur"}},
    {"$unwind": {"path": "$formateur", "preserveNullAndEmptyArrays": True}},
]
```

Les opérateurs `find()`, `findOne()`, `insertOne()`, `updateOne()`,
`updateMany()`, `deleteOne()`, `deleteMany()` ainsi que `$gt`, `$gte`, `$lt`,
`$lte`, `$in`, `$and`, `$or` et les expressions régulières (`$regex`) sont
utilisés dans les modèles pour les opérations CRUD, la recherche et le
filtrage (voir par exemple `Student.find_all`, `Course.find_all`,
`Enrollment.create`).

## 7. Index et performances

Le script [`scripts/create_indexes.py`](../scripts/create_indexes.py) crée
les index suivants :

- `etudiants.email` (unique) et `etudiants.niveau`
- `formateurs.email` (unique) et `formateurs.specialite`
- `formations.categorie`, `formations.formateur_id`, index composé
  `(statut, date_debut)`, index texte `(titre, description)`
- `inscriptions.etudiant_id`, `inscriptions.formation_id`, index **unique
  partiel** `(etudiant_id, formation_id)` filtré sur `statut = "active"`
  (garantit au niveau base la règle de non double-inscription active), et
  index composé `(formation_id, statut)` pour accélérer le comptage des
  places disponibles.

Le script [`scripts/performance_explain.py`](../scripts/performance_explain.py)
compare, via `explain("executionStats")`, l'exécution d'une requête avant
et après la création d'un index. Sur une base peuplée par
`scripts/seed_data.py` (100 étudiants, 30 formations, 200 inscriptions),
les résultats observés sont typiquement :

| Requête | Sans index | Avec index |
|---|---|---|
| `etudiants.find({"email": ...})` | `COLLSCAN`, ~100 documents examinés | `IXSCAN`, 1 document examiné |
| `inscriptions.find({"formation_id":..., "statut":"active"})` | `COLLSCAN`, ~200 documents examinés | `IXSCAN`, documents examinés ≈ documents retournés |

Cette comparaison illustre concrètement le gain apporté par l'indexation :
le champ `totalDocsExamined` chute de l'ordre de grandeur de la collection à
l'ordre de grandeur du résultat, et `executionTimeMillis` diminue en
conséquence. Sur les faibles volumes du projet (quelques centaines de
documents) le gain absolu reste modeste, mais le principe — et son intérêt
pour un passage à l'échelle — est clairement démontré par le changement de
stage du plan d'exécution (`COLLSCAN` → `IXSCAN`).

## 8. Sécurité de l'application

- **Mots de passe** : hachés avec `werkzeug.security.generate_password_hash`
  (PBKDF2-SHA256 salé), jamais stockés en clair, jamais journalisés.
- **CSRF** : Flask-WTF ajoute un jeton anti-CSRF (`{{ form.hidden_tag() }}`)
  sur chaque formulaire ; toute soumission sans jeton valide est rejetée.
- **Injection NoSQL** : toutes les requêtes PyMongo utilisent des
  dictionnaires Python typés (jamais de construction de requête par
  concaténation de chaînes provenant de l'utilisateur), ce qui élimine par
  construction les injections de type `$where`/opérateurs arbitraires.
- **XSS et `htmlspecialchars()`** : Jinja2 échappe automatiquement toute
  variable insérée avec `{{ }}` (conversion de `<`, `>`, `&`, `"`, `'` en
  entités HTML). C'est l'équivalent direct de l'appel systématique à
  `htmlspecialchars()` en PHP, mais appliqué de façon automatique et
  systématique par le moteur de gabarits, ce qui supprime le risque d'oubli
  humain propre à un appel manuel.
- **Sessions** : cookies `HttpOnly` (inaccessibles en JavaScript) et
  `SameSite=Lax` (limite les envois cross-site), clé secrète Flask issue
  d'une variable d'environnement (`FLASK_SECRET_KEY`), jamais commitée en
  clair dans le dépôt (`.env` est dans `.gitignore`).
- **Autorisations** : décorateur `@roles_required(*roles)` sur chaque route
  sensible (retour HTTP 403 si le rôle ne correspond pas) ; vérification
  supplémentaire de propriété pour les formateurs (ils ne peuvent agir que
  sur leurs propres formations) et pour les étudiants (ils ne voient/annulent
  que leurs propres inscriptions), indépendamment de ce que montre
  l'interface — un utilisateur ne peut donc pas contourner ces règles en
  modifiant une URL.
- **Validation des formulaires** : WTForms valide types, longueurs,
  formats email et plages numériques (ex. note entre 0 et 20) côté serveur,
  en complément de la validation HTML5 côté client.

## 9. Organisation du travail en équipe

| Membre | Périmètre |
|---|---|
| Étudiant 1 | Modélisation MongoDB, `app/models/`, script de peuplement (`scripts/seed_data.py`), agrégations, index et performances (`scripts/create_indexes.py`, `scripts/performance_explain.py`) |
| Étudiant 2 | Architecture applicative, `app/routes/`, `app/forms/`, authentification, rôles, règles de gestion, sécurité |
| Étudiant 3 | `app/templates/`, tableau de bord et graphiques, tests fonctionnels, documentation (README, cahier des charges, rapport) |

Chaque membre a néanmoins revu et compris l'ensemble du code, conformément à
la consigne du sujet (toute question de soutenance peut porter sur
n'importe quelle partie du projet).

Le suivi du travail a été assuré via Git : commits réguliers par
fonctionnalité, une branche par domaine (`feature/backend-mongo`,
`feature/auth-securite`, `feature/ui-dashboard`), fusionnées via des pull
requests sur `main` après relecture croisée.

## 10. Difficultés rencontrées et solutions apportées

- **Modélisation many-to-many** : le choix initial d'imbriquer les
  inscriptions dans le document étudiant a été abandonné au profit d'une
  collection `inscriptions` séparée, pour les raisons détaillées en section
  4 — cela a nécessité de revoir les premières maquettes de schéma.
- **Unicité applicative vs. unicité en base** : s'assurer qu'un étudiant ne
  soit jamais inscrit deux fois activement à la même formation ne peut pas
  reposer uniquement sur une vérification applicative (risque de conditions
  de concurrence). La solution retenue est un **index unique partiel**
  MongoDB (`{etudiant_id, formation_id}` filtré sur `statut = "active"`),
  qui garantit la contrainte au niveau base tout en autorisant plusieurs
  inscriptions *annulées* historiques pour un même couple étudiant/formation.
- **Types de dates WTForms/BSON** : le champ `DateField` de WTForms renvoie
  un objet `datetime.date`, alors que BSON (le format de stockage MongoDB)
  n'accepte que `datetime.datetime`. Une fonction de conversion
  (`_to_datetime`) a été ajoutée dans `app/models/course.py` pour convertir
  systématiquement les dates avant écriture.
- **Séparation des responsabilités formateur/étudiant** : garantir qu'un
  formateur ne puisse noter que ses propres étudiants a nécessité une
  vérification explicite de propriété (`formation.formateur_id ==
  current_user.ref_id`) à la fois dans les routes et dans la couche modèle
  (`Enrollment.set_note`), pour que la règle soit appliquée même en cas
  d'appel direct au modèle (tests, scripts).

## 11. Tests réalisés

Tests manuels effectués sur l'application déployée localement (MongoDB +
Flask en mode développement) :

- Connexion avec chacun des trois rôles (admin, formateur, étudiant) et
  vérification de la redirection vers le bon tableau de bord.
- Tentative d'accès direct à une route admin en étant connecté en tant
  qu'étudiant → réponse HTTP 403.
- Création d'un étudiant avec un email déjà utilisé → message d'erreur,
  aucune écriture en base.
- Inscription d'un étudiant à une formation déjà complète → refus avec
  message explicite.
- Double inscription active du même étudiant à la même formation → refus
  (vérifié à la fois applicativement et par l'index unique partiel).
- Attribution d'une note hors de la plage [0, 20] → rejet par la validation
  WTForms.
- Annulation d'une inscription déjà notée → refus (règle de gestion).
- Suppression d'une formation possédant des inscriptions actives → refus.
- Suppression d'un formateur responsable d'au moins une formation → refus.
- Recherche et filtres (étudiants par niveau, formations par catégorie/prix,
  formateurs par spécialité) → résultats cohérents avec le contenu de la
  base générée par `scripts/seed_data.py`.
- Vérification visuelle des trois graphiques du tableau de bord
  (répartition par catégorie, top formations, top étudiants) après
  peuplement de la base.
- Exécution de `scripts/performance_explain.py` pour confirmer le passage
  de `COLLSCAN` à `IXSCAN` après création des index.

## 12. Conclusion et perspectives d'évolution

Ce projet a permis de transformer la base technique du TP MongoDB/PHP en une
application web complète répondant aux besoins réels d'une école :
authentification par rôles, CRUD complet sur les entités métier, gestion des
inscriptions avec règles de gestion appliquées au niveau base et
applicatif, tableau de bord statistique fondé sur des pipelines
d'agrégation, et sécurisation des données et des sessions.

Perspectives d'évolution possibles :
- Passage à une architecture API REST + frontend découplé (React/Vue) pour
  une expérience plus dynamique.
- Envoi d'emails de confirmation d'inscription et de notification de note.
- Export PDF/CSV des relevés de notes et des listes d'inscrits.
- Conteneurisation (Docker) de l'application et de MongoDB pour faciliter le
  déploiement.
- Ajout de tests automatisés (pytest + `mongomock` ou conteneur MongoDB
  éphémère) pour sécuriser les évolutions futures.
