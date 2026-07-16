# Cahier des charges — Plateforme de gestion de formations

## 1. Contexte et objectifs

Une école souhaite disposer d'une plateforme web lui permettant de gérer de
façon centralisée ses étudiants, ses formateurs, ses formations et les
inscriptions à ces formations. L'application doit remplacer des processus
manuels (tableurs, échanges d'emails) par un outil unique, sécurisé et
accessible à trois catégories d'utilisateurs : administrateurs, formateurs
et étudiants.

## 2. Périmètre fonctionnel

### 2.1 Acteurs

| Acteur         | Description                                                                 |
|----------------|-------------------------------------------------------------------------------|
| Administrateur | Gère l'ensemble des données : comptes, étudiants, formateurs, formations, inscriptions. Consulte toutes les statistiques. |
| Formateur      | Consulte ses formations et les étudiants inscrits, attribue des notes, consulte les moyennes. |
| Étudiant       | Recherche des formations, s'inscrit, annule une inscription, consulte ses notes et sa moyenne. |

### 2.2 Besoins fonctionnels

1. **Authentification** : connexion/déconnexion sécurisées, sessions,
   protection des pages selon le rôle.
2. **Gestion des étudiants** (admin) : lister, rechercher, filtrer par
   niveau, ajouter, modifier, supprimer.
3. **Gestion des formateurs** (admin) : lister, rechercher, ajouter,
   modifier, supprimer, voir leurs formations.
4. **Gestion des formations** (admin) : créer, modifier, supprimer,
   consulter, rechercher, filtrer par catégorie/prix/statut, trier.
5. **Gestion des inscriptions** : un étudiant s'inscrit/se désinscrit à une
   formation ; l'administrateur peut consulter/annuler toute inscription ;
   le formateur consulte les inscrits à ses formations.
6. **Notation** (formateur) : attribuer/modifier une note (0-20) à un
   étudiant inscrit à l'une de ses formations.
7. **Tableau de bord et statistiques** (admin principalement) : effectifs,
   répartition par catégorie, prix moyen, moyenne générale, top formations,
   top étudiants, graphiques.

### 2.3 Besoins non fonctionnels

- **Sécurité** : mots de passe hachés, protection CSRF, échappement
  systématique des sorties HTML, contrôle d'accès par rôle sur chaque route.
- **Ergonomie** : interface responsive (Bootstrap 5), messages de
  confirmation/erreur explicites, navigation cohérente par rôle.
- **Performance** : les recherches et jointures fréquentes (emails,
  inscriptions par formation) doivent être indexées.
- **Maintenabilité** : séparation claire modèles / routes / gabarits,
  architecture en blueprints Flask.

## 3. Règles de gestion

1. L'email d'un étudiant est unique.
2. L'email d'un formateur est unique.
3. Un étudiant ne peut pas avoir deux inscriptions actives à la même
   formation.
4. Une formation ne peut pas dépasser sa capacité maximale de participants
   actifs.
5. Une note est nécessairement comprise entre 0 et 20.
6. Un étudiant ne peut consulter que ses propres notes et inscriptions.
7. Un formateur ne peut noter que les étudiants inscrits à l'une de ses
   formations.
8. Seul un administrateur peut supprimer un étudiant, un formateur ou une
   formation.
9. La suppression d'une formation ou d'un formateur ayant des inscriptions
   ou des formations actives est bloquée.
10. Toute donnée saisie côté utilisateur est validée côté serveur avant
    écriture en base.

## 4. Contraintes techniques

- Base de données NoSQL obligatoire : **MongoDB**.
- Langage : **Python** (framework **Flask**).
- Accès aux données via **PyMongo** (sans ORM), afin de manipuler
  directement les documents, requêtes et pipelines d'agrégation MongoDB.

## 5. Livrables attendus

Cahier des charges, diagramme des cas d'utilisation, modèle de données
MongoDB, code source, script de peuplement, README, comptes de démonstration,
rapport technique, dépôt Git.
