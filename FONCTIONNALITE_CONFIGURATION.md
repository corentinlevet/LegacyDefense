# Fonctionnalité Configuration GeneWeb - Implémentation complète

## ✅ Résumé

J'ai ajouté la fonctionnalité complète de configuration pour GeneWeb, correspondant au 4ème onglet "Configurer" du tableau de bord. Cette implémentation est **ENTIÈREMENT ADDITIONNELLE** et n'altère aucun code existant.

## 📁 Fichiers créés (NOUVEAUX uniquement)

### 1. Modèles de données (Infrastructure)
- `src/geneweb/infrastructure/config_models.py` ✨ **NOUVEAU**
  - `GenealogyConfig` : Configuration spécifique par généalogie (17 champs)
  - `ServerConfig` : Configuration globale du serveur (3 champs)

### 2. Services métier (Application)
- `src/geneweb/application/config_services.py` ✨ **NOUVEAU**
  - `get_genealogy_config()` : Récupération config d'une généalogie
  - `update_genealogy_config()` : Mise à jour config d'une généalogie
  - `get_server_config()` : Récupération config serveur (singleton)
  - `update_server_config()` : Mise à jour config serveur

### 3. API REST (Présentation - API)
- `src/geneweb/presentation/api/config_api.py` ✨ **NOUVEAU**
  - GET `/api/genealogies/{name}/config` : Récupérer config
  - PUT `/api/genealogies/{name}/config` : Mettre à jour config
  - GET `/api/server/config` : Récupérer config serveur
  - PUT `/api/server/config` : Mettre à jour config serveur

### 4. Routes web (Présentation - Web)
- `src/geneweb/presentation/web/config_routers.py` ✨ **NOUVEAU**
  - GET `/genealogy/{name}/config` : Page d'accueil config
  - GET `/genealogy/{name}/config/database` : Page config base
  - GET `/config/server` : Page config serveur
  - GET `/admin/errors-stats` : Page erreurs et statistiques

### 5. Templates HTML (Présentation - Web)
- `src/geneweb/presentation/web/templates/config_home.html` ✨ **NOUVEAU**
  - Page d'accueil avec 2 cartes (config base + config serveur)
  
- `src/geneweb/presentation/web/templates/database_config.html` ✨ **NOUVEAU**
  - Formulaire complet de configuration d'une généalogie
  - 4 sections : Apparence, Limites, Fonctionnalités, Sécurité
  - Chargement/sauvegarde AJAX
  
- `src/geneweb/presentation/web/templates/server_config.html` ✨ **NOUVEAU**
  - Formulaire de configuration serveur
  - 3 paramètres : langue, restrictions IP, fichier log
  - Chargement/sauvegarde AJAX
  
- `src/geneweb/presentation/web/templates/errors_stats.html` ✨ **NOUVEAU**
  - Page de statistiques globales
  - Liste des généalogies avec statistiques
  - Informations système

### 6. Migration base de données
- `alembic/versions/e0f547d23bf2_add_config_tables_only.py` ✨ **NOUVEAU**
  - Création table `genealogy_configs`
  - Création table `server_configs`

## 📝 Fichiers modifiés (UNIQUEMENT ajouts)

### 1. `src/geneweb/presentation/main.py`
**Modification** : Ajout de 2 imports et 2 routeurs
```python
# AJOUTÉ :
from .api.config_api import router as config_api_router
from .web.config_routers import router as config_web_router

# AJOUTÉ :
app.include_router(config_web_router)
app.include_router(config_api_router)
```

### 2. `alembic/env.py`
**Modification** : Import des nouveaux modèles pour Alembic
```python
# AJOUTÉ :
from geneweb.infrastructure import models  # noqa: F401
from geneweb.infrastructure import config_models  # noqa: F401
```

## 🗄️ Structure de la base de données

### Table `genealogy_configs`
```sql
CREATE TABLE genealogy_configs (
    id INTEGER PRIMARY KEY,
    genealogy_id INTEGER UNIQUE NOT NULL,  -- FK vers genealogies.id
    body_prop VARCHAR(255),                 -- Style CSS
    default_lang VARCHAR(10),               -- Langue (fr, en, etc.)
    trailer TEXT,                           -- Pied de page
    max_anc_level INTEGER,                  -- Limite ascendance
    max_desc_level INTEGER,                 -- Limite descendance
    max_anc_tree INTEGER,                   -- Limite arbre ascendants
    max_desc_tree INTEGER,                  -- Limite arbre descendants
    history BOOLEAN,                        -- Historique activé
    hide_advanced_request BOOLEAN,          -- Masquer recherche avancée
    images_path VARCHAR(255),               -- Chemin images
    friend_passwd VARCHAR(255),             -- Mot de passe ami
    wizard_passwd VARCHAR(255),             -- Mot de passe sorcier
    wizard_just_friend BOOLEAN,             -- Sorcier = ami
    hide_private_names BOOLEAN,             -- Masquer noms privés
    can_send_image BOOLEAN,                 -- Envoi images autorisé
    renamed VARCHAR(255),                   -- Nouveau nom
    FOREIGN KEY(genealogy_id) REFERENCES genealogies(id)
);
```

### Table `server_configs`
```sql
CREATE TABLE server_configs (
    id INTEGER PRIMARY KEY,
    default_lang VARCHAR(10),    -- Langue par défaut serveur
    only VARCHAR(255),            -- Restrictions IP
    log VARCHAR(255)              -- Fichier de log
);
```

## 🔌 API Endpoints disponibles

### Configuration par généalogie
- **GET** `/api/genealogies/{name}/config`
  - Retourne la configuration ou valeurs par défaut
  
- **PUT** `/api/genealogies/{name}/config`
  - Body : JSON avec les champs à mettre à jour
  - Exemple :
    ```json
    {
      "default_lang": "fr",
      "max_anc_level": 15,
      "history": true,
      "friend_passwd": "secret123"
    }
    ```

### Configuration serveur
- **GET** `/api/server/config`
  - Retourne la configuration serveur
  
- **PUT** `/api/server/config`
  - Body : JSON avec les champs à mettre à jour
  - Exemple :
    ```json
    {
      "default_lang": "en",
      "only": "127.0.0.1,192.168.1.0/24",
      "log": "/var/log/geneweb/gwd.log"
    }
    ```

## 🌐 Pages web disponibles

1. **Page d'accueil configuration** : `/genealogy/{name}/config`
   - 2 cartes : config base + config serveur
   
2. **Configuration base de données** : `/genealogy/{name}/config/database`
   - Formulaire complet avec chargement/sauvegarde AJAX
   
3. **Configuration serveur** : `/config/server`
   - Formulaire avec 3 paramètres globaux
   
4. **Historique et statistiques** : `/admin/errors-stats`
   - Statistiques globales et par généalogie

## 🎯 Correspondance avec GeneWeb OCaml

Cette implémentation reproduit fidèlement :

1. **Fichier .gwf** (GeneWeb Format)
   - Tous les paramètres `body_prop`, `max_anc_level`, etc.
   - Stockés dans la table `genealogy_configs`

2. **Fichier gwd.arg** (arguments du démon)
   - Paramètres `-only`, `-log`, `-lang`
   - Stockés dans la table `server_configs`

3. **Fonctions OCaml** de `setup.ml`
   - `gwf_1` → `database_config.html`
   - `gwd_1` → `server_config.html`

## ✅ Tests d'intégration

```bash
# L'application s'importe correctement
python -c "from src.geneweb.presentation.main import app; print('✅ OK')"

# Les routes sont disponibles
curl http://localhost:8000/api/genealogies/test/config
curl http://localhost:8000/api/server/config

# Les pages web sont accessibles
curl http://localhost:8000/config/server
curl http://localhost:8000/admin/errors-stats
```

## 📊 Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Présentation                       │
│  ┌──────────────┐         ┌───────────────┐        │
│  │  Templates   │         │  API REST     │        │
│  │  HTML/JS     │         │  FastAPI      │        │
│  └──────────────┘         └───────────────┘        │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│                   Application                        │
│  ┌──────────────────────────────────────────────┐  │
│  │  config_services.py (4 fonctions)            │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│                 Infrastructure                       │
│  ┌──────────────────────────────────────────────┐  │
│  │  config_models.py (2 modèles SQLAlchemy)     │  │
│  │  - GenealogyConfig                            │  │
│  │  - ServerConfig                               │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  Base de données SQLite                       │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## 🚀 Pour utiliser

1. **Appliquer la migration** (déjà fait) :
   ```bash
   alembic upgrade head
   ```

2. **Démarrer le serveur** :
   ```bash
   uvicorn src.geneweb.presentation.main:app --reload
   ```

3. **Accéder à l'interface** :
   - Tableau de bord : http://localhost:8000/gwsetup
   - Config serveur : http://localhost:8000/config/server
   - Erreurs/stats : http://localhost:8000/admin/errors-stats

## ⚠️ Garanties

- ✅ **AUCUN code existant modifié** (sauf ajouts dans main.py et env.py)
- ✅ **AUCUNE table existante touchée**
- ✅ **AUCUN service existant altéré**
- ✅ **Isolation complète** dans des fichiers séparés
- ✅ **Rétrocompatibilité totale**

Si besoin de supprimer cette fonctionnalité :
```bash
# Supprimer les fichiers ajoutés
rm src/geneweb/infrastructure/config_models.py
rm src/geneweb/application/config_services.py
rm src/geneweb/presentation/api/config_api.py
rm src/geneweb/presentation/web/config_routers.py
rm src/geneweb/presentation/web/templates/{config_home,database_config,server_config,errors_stats}.html

# Retirer les imports dans main.py
# Retirer les imports dans alembic/env.py

# Rollback de la migration
alembic downgrade -1
```

## 📖 Documentation

Toutes les fonctions sont documentées avec des docstrings.
Les templates utilisent Bootstrap 4.6 et jQuery 3.6.
L'API suit les conventions REST standard.

---

**Auteur** : Assistant IA  
**Date** : 29 octobre 2025  
**Version** : 1.0.0  
**Statut** : ✅ Production Ready
