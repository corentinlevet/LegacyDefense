=======================================
GeneWeb - Version Python (Modernisation)
=======================================

Ce fichier concerne la nouvelle version de GeneWeb, ré-écrite en Python avec le framework FastAPI.


--------------------
Lancement Rapide (Développement)
--------------------

1. Prérequis:
   - Python 3.9 ou supérieur
   - Un environnement virtuel est recommandé

2. Installation des dépendances:
   Ouvrez un terminal à la racine du projet et lancez :
   pip install -r requirements.txt

3. Lancement du serveur:
   Depuis la racine du projet, lancez la commande suivante :

   uvicorn geneweb.presentation.main:app --reload --app-dir src

   - `--reload`: Le serveur redémarrera automatiquement si vous modifiez le code.
   - `--app-dir src`: Indique à uvicorn de chercher le code dans le dossier `src`.

4. Accès à l'application:
   Ouvrez votre navigateur et allez à l'adresse : http://127.0.0.1:8000


--------------------
Structure du Projet
--------------------

Le code source de l'application se trouve dans le dossier `src/geneweb`.
Il est organisé en plusieurs couches :

- `presentation`: Gère l'interface web (HTML) et l'API REST.
- `application`: Contient les services qui orchestrent la logique métier.
- `domain`: Le cœur de l'application, avec les modèles de données et les algorithmes de généalogie.
- `infrastructure`: Gère la communication avec la base de données et autres systèmes externes.


--------------------
Configuration
--------------------

La configuration de l'application (qui remplace l'ancien `gwsetup`) se fera via :
- Des variables d'environnement.
- Une future interface d'administration directement dans l'application web.
