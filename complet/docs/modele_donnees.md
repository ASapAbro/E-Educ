# Modèle de données MongoDB

## 1. Vue d'ensemble des collections

| Collection      | Rôle                                                             |
|-----------------|-------------------------------------------------------------------|
| `utilisateurs`  | Comptes de connexion (email, mot de passe haché, rôle, lien vers le profil) |
| `etudiants`     | Profils étudiants                                                  |
| `formateurs`    | Profils formateurs                                                 |
| `formations`    | Catalogue des formations proposées                                 |
| `inscriptions`  | Table de liaison étudiant ↔ formation, avec statut et note         |

## 2. Schémas de documents

### 2.1 `utilisateurs`
```json
{
  "_id": ObjectId,
  "email": "prenom.nom@ecole-formation.edu",
  "password_hash": "pbkdf2:sha256:...",
  "role": "admin | formateur | etudiant",
  "ref_id": ObjectId | null,   // pointe vers etudiants._id ou formateurs._id (null pour admin)
  "nom_complet": "Prénom Nom",
  "actif": true,
  "date_creation": ISODate
}
```

### 2.2 `etudiants`
```json
{
  "_id": ObjectId,
  "nom": "Dupont",
  "prenom": "Alice",
  "email": "alice.dupont@etu.ecole-formation.edu",
  "niveau": "Master 1",
  "statut": "actif | inactif",
  "date_creation": ISODate
}
```

### 2.3 `formateurs`
```json
{
  "_id": ObjectId,
  "nom": "Martin",
  "prenom": "Paul",
  "email": "paul.martin@ecole-formation.edu",
  "specialite": "Data Science",
  "statut": "actif | inactif",
  "date_creation": ISODate
}
```

### 2.4 `formations`
```json
{
  "_id": ObjectId,
  "titre": "Machine Learning appliqué",
  "description": "...",
  "categorie": "Data Science",
  "prix": 499.0,
  "duree": 80,                     // en heures
  "capacite_max": 25,
  "formateur_id": ObjectId,        // référence -> formateurs._id
  "date_debut": ISODate,
  "date_fin": ISODate,
  "statut": "ouverte | fermee | terminee",
  "date_creation": ISODate
}
```

### 2.5 `inscriptions`
```json
{
  "_id": ObjectId,
  "etudiant_id": ObjectId,         // référence -> etudiants._id
  "formation_id": ObjectId,        // référence -> formations._id
  "date_inscription": ISODate,
  "statut": "active | annulee",
  "note": 15.5 | null
}
```

## 3. Choix de modélisation : références plutôt que documents imbriqués

Le sujet impose de justifier le choix entre **imbrication** (embedding) et
**références** entre collections. Nous avons retenu une modélisation
**principalement en références**, pour les raisons suivantes :

1. **Relations many-to-many** : un étudiant peut s'inscrire à plusieurs
   formations, et une formation accueille plusieurs étudiants. Cette
   relation n'a pas de « propriétaire » naturel — l'imbrication d'un tableau
   d'inscriptions dans `etudiants` *et* dans `formations` dupliquerait la
   donnée et rendrait les mises à jour (annulation, notation) incohérentes
   entre les deux copies.
2. **Croissance non bornée** : le nombre d'inscriptions par formation ou par
   étudiant n'est pas plafonné a priori. MongoDB déconseille les tableaux
   imbriqués à croissance illimitée (risque de dépasser la taille maximale
   de document de 16 Mo, et dégradation des performances d'écriture au fil
   des `$push`).
3. **Écritures indépendantes et fréquentes** : une inscription, une
   annulation ou une notation sont des écritures ponctuelles et fréquentes.
   Les isoler dans leur propre collection `inscriptions` permet des
   `updateOne` ciblés, sans réécrire tout le document étudiant ou formation.
4. **Requêtes transversales** : le tableau de bord doit produire des
   statistiques globales (top formations, top étudiants, inscriptions par
   catégorie) qui nécessitent de parcourir *toutes* les inscriptions
   indépendamment de l'étudiant ou de la formation d'origine — une
   collection dédiée avec des pipelines `$group`/`$lookup` est plus adaptée
   qu'une donnée éclatée dans des sous-documents.
5. **Intégrité applicative** : les règles de gestion (unicité d'inscription
   active, capacité maximale) sont plus simples à garantir avec des
   requêtes `count_documents` / index uniques partiels sur une collection
   dédiée qu'avec des vérifications sur des tableaux imbriqués.

Nous avons cependant conservé un **léger niveau d'imbrication ponctuelle** —
non pas en base, mais **au niveau applicatif via `$lookup`** : les pages qui
affichent une formation avec son formateur, ou une inscription avec
l'étudiant et la formation associés, réalisent une jointure à la volée
(`$lookup` + `$unwind`) plutôt que de dupliquer ces informations dans les
documents stockés. Cela évite les incohérences (ex. changement de nom d'un
formateur) tout en conservant des documents sources compacts et
normalisés.

En résumé : **normalisation par référence** pour les entités métier
(étudiants, formateurs, formations, inscriptions), et **jointures à la
lecture** (`$lookup`) pour reconstituer les vues composites nécessaires à
l'interface, plutôt que de la dénormalisation écrite en base.

## 4. Index

Voir [`scripts/create_indexes.py`](../scripts/create_indexes.py) et la
section « Index et performances » du rapport technique.

| Collection      | Index                                                       | Objectif |
|-----------------|--------------------------------------------------------------|----------|
| `etudiants`     | `email` (unique)                                              | Unicité + recherche rapide par email (login) |
| `etudiants`     | `niveau`                                                       | Filtrage par niveau |
| `formateurs`    | `email` (unique)                                               | Unicité + recherche rapide (login) |
| `formateurs`    | `specialite`                                                    | Filtrage par spécialité |
| `formations`    | `categorie`                                                     | Filtrage par catégorie |
| `formations`    | `formateur_id`                                                  | Récupération des formations d'un formateur |
| `formations`    | composé `(statut, date_debut)`                                 | Catalogue trié/filtré par statut et date |
| `formations`    | texte `(titre, description)`                                   | Recherche plein texte |
| `inscriptions`  | `etudiant_id`                                                   | Historique d'un étudiant |
| `inscriptions`  | `formation_id`                                                  | Liste des inscrits à une formation |
| `inscriptions`  | unique partiel `(etudiant_id, formation_id)` où `statut=active`| Empêche la double inscription active (règle de gestion) |
| `inscriptions`  | composé `(formation_id, statut)`                                | Comptage rapide des places disponibles |
