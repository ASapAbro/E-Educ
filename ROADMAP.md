# Feuille de route — Reconstruction pas à pas

Ce document est notre plan de cours. Chaque sprint = une fonctionnalité
complète, testée, comprise avant de passer à la suivante. On ne code jamais
"pour que ça marche" — on code pour que **tu** comprennes chaque ligne.

Référence : `complet/` contient l'ancienne version terminée du projet
(cahier des charges dans `complet/docs/cahier_des_charges.md`). On garde le
même stack imposé : **Python + Flask + MongoDB (PyMongo, sans ORM)**.
Essaie de ne pas aller copier dedans avant d'avoir cherché toi-même — sinon
l'exercice perd tout son intérêt. Il servira surtout si on est bloqués ou
pour comparer une fois qu'un sprint est fini.

## Règle du jeu

Pour chaque étape je te donne, dans cet ordre :
1. **Quoi** écrire (le concept, pas juste "recopie ça")
2. **Où** l'écrire (quel fichier, quel dossier, et pourquoi cet endroit)
3. **Pourquoi** on l'écrit (le rôle de ce bout de code dans l'appli)
4. **Comment** l'écrire (la syntaxe, avec un exemple minimal si besoin)

Ensuite **tu écris le code toi-même**. Je ne te donne pas la solution
copiable directement, je te guide jusqu'à ce que tu l'écrives. Une fois que
c'est fait, tu me montres, je relis, on corrige ensemble, et seulement là on
avance.

## Sprint 0 — Outils et bases (avant même Flask)
- Vérifier Python installé, comprendre le terminal (`cd`, `ls`, `pwd`)
- Éditeur de code (VS Code), extensions utiles
- Environnement virtuel (`venv`) : pourquoi on isole les dépendances
- Rappels Python minimum : variables, fonctions, `if`, boucles, listes, dict
- Git de base : `status`, `add`, `commit` (le `push` viendra plus tard)

## Sprint 1 — Premier serveur Flask
- Structure minimale d'un projet Flask
- Une route, une page HTML servie via Jinja2
- Lancer le serveur, comprendre `debug=True`, le rechargement automatique

## Sprint 2 — Connexion à MongoDB
- Installer/lancer MongoDB en local
- PyMongo : se connecter, insérer un document, le relire
- Notion de collection vs table SQL, document vs ligne

## Sprint 3 — CRUD Étudiants (première entité complète)
- Modèle de données pour un étudiant
- Formulaire (Flask-WTF), validation, protection CSRF
- Créer / lister / modifier / supprimer un étudiant

## Sprint 4 — Authentification et rôles
- Hachage des mots de passe (Werkzeug)
- Flask-Login : connexion, session, déconnexion
- Décorateur `@roles_required` pour protéger les routes (admin/formateur/étudiant)

## Sprint 5 — Formateurs et Formations (CRUD)
- Même logique que le Sprint 3, appliquée à deux nouvelles entités
- Relations simples par référence (`_id`) plutôt que documents imbriqués

## Sprint 6 — Inscriptions (la première vraie relation)
- Modèle d'inscription reliant étudiant + formation
- Règles de gestion : unicité d'inscription active, capacité max de la formation
- Index unique partiel MongoDB pour garantir la règle en base

## Sprint 7 — Notation
- Le formateur attribue une note (0–20) à un étudiant inscrit à sa formation
- Vérification serveur : le formateur ne note que ses propres formations
- Calcul de moyenne (par formation, par étudiant)

## Sprint 8 — Tableau de bord et statistiques
- Agrégations MongoDB (`$group`, `$match`, `$lookup`)
- Affichage de graphiques (Chart.js) à partir de ces agrégations

## Sprint 9 — Sécurité et finitions
- Revue CSRF/XSS/injection, gestion des erreurs (403/404)
- Messages de confirmation, UX des formulaires

## Sprint 10 — Index et performances
- Créer les index (email unique, index composés)
- Comparer un `explain()` avec et sans index (COLLSCAN vs IXSCAN)

## Sprint 11 — Documentation et rapport
- README, script de peuplement (Faker), rapport technique

---

**Où on en est :** Sprint 0 terminé ✅ (variables, fonctions, conditions,
boucles/listes, import et `if __name__ == "__main__"`, dictionnaires —
exercices dans `sprint0/`). Prochaine étape : Sprint 1, premier serveur
Flask.
