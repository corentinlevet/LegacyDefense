# Déploiement et Hébergement — Legacy (GeneWeb Python)

> **Version :** 1.0  
> **Date :** Février 2026  
> **Statut :** Documentation officielle

---

## Avertissement préalable — Données personnelles et RGPD

> **⚠️ Ce projet doit impérativement être utilisé en local.**

L'application Legacy gère des données généalogiques qui constituent, au sens du Règlement Général sur la Protection des Données (RGPD — Règlement UE 2016/679), des **données à caractère personnel** :

- Noms, prénoms, dates et lieux de naissance, de mariage et de décès
- Liens de filiation et de parenté entre individus
- Informations potentiellement sensibles sur des **personnes encore en vie**

Le déploiement sur une infrastructure cloud ou un serveur distant accessible depuis Internet **est formellement déconseillé**, car il entraînerait :

- Une obligation de désignation d'un **DPO** (Délégué à la Protection des Données)
- L'obligation de tenir un **registre des traitements**
- Des risques d'exposition non consentie de données de tiers
- Des obligations contractuelles vis-à-vis des hébergeurs (clauses de sous-traitance RGPD)
- Une exposition potentielle à des sanctions de la CNIL (jusqu'à 20 M€ ou 4 % du CA mondial)

**L'utilisation locale sur la machine personnelle de l'utilisateur élimine ces risques** en maintenant les données dans un périmètre entièrement maîtrisé, sans transit réseau externe.

---

## 1. Solution d'hébergement retenue : déploiement local via Docker

### 1.1 Justification du choix

La solution retenue est un **déploiement local conteneurisé** via **Docker** sur la machine de l'utilisateur final. Ce choix répond à plusieurs exigences simultanées :

| Critère | Justification |
|---|---|
| **Confidentialité des données** | Les données restent sur la machine locale, aucun transit réseau externe |
| **Conformité RGPD** | Traitement local = responsable de traitement unique et identifié |
| **Reproductibilité** | L'environnement Docker est identique sur Windows, macOS et Linux |
| **Isolation** | Le conteneur n'interfère pas avec le système hôte |
| **Simplicité** | Un seul fichier `docker-compose.yml` suffit à démarrer l'application |
| **Portabilité** | L'image embarque toutes les dépendances, sans configuration système |

### 1.2 Architecture du déploiement local

```
Machine de l'utilisateur
│
├── Docker Engine (daemon local)
│   └── Conteneur geneweb-app
│       ├── Python 3.13-slim (image de base)
│       ├── FastAPI + Uvicorn (serveur ASGI)
│       ├── SQLAlchemy + SQLite (base de données locale)
│       └── Écoute sur 127.0.0.1:8000
│
├── Navigateur web (http://localhost:8000)
│
└── Données (montage volume local → ./src)
    └── Fichiers GEDCOM, base SQLite → restent sur disque local
```

Le serveur Uvicorn est configuré pour écouter sur `0.0.0.0:8000` **à l'intérieur du conteneur**, ce qui est mappé sur `localhost:8000` de la machine hôte. Aucun port n'est exposé vers l'extérieur du réseau local par défaut.

---

## 2. Prérequis

| Logiciel | Version minimale | Liens |
|---|---|---|
| Docker Desktop (Windows / macOS) | 4.x | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop) |
| Docker Engine (Linux) | 24.x | [docs.docker.com/engine/install](https://docs.docker.com/engine/install/) |
| Docker Compose plugin | v2 | Inclus dans Docker Desktop |
| Git | 2.x | Pour récupérer le dépôt |

> **Note Windows :** Docker Desktop nécessite WSL 2 activé. Consultez la [documentation officielle](https://docs.docker.com/desktop/windows/wsl/).

---

## 3. Déploiement avec Docker (solution recommandée)

### 3.1 Récupérer le projet

```bash
git clone https://github.com/EpitechPGE45-2025/G-ING-900-PAR-9-1-legacy-1.git
cd G-ING-900-PAR-9-1-legacy-1
```

### 3.2 Construire l'image

```bash
docker compose build
```

Le Dockerfile utilise une construction **multi-stage** pour minimiser la taille de l'image finale :

- **Stage `builder`** : installe les outils de compilation et les dépendances Python dans `/install`
- **Stage `container`** : image minimale `python:3.13-slim` qui ne copie que les packages compilés et le code source

```
python:3.13-slim (builder)   →   python:3.13-slim (container)
~350 MB avec build tools         ~180 MB image finale
```

### 3.3 Démarrer l'application

```bash
docker compose up
```

L'application est accessible sur : **http://localhost:8000**

Pour démarrer en arrière-plan :

```bash
docker compose up -d
```

Pour arrêter :

```bash
docker compose down
```

### 3.4 Vérification

```bash
# Vérifier que le conteneur tourne
docker compose ps

# Consulter les logs
docker compose logs -f
```

Réponse attendue à `http://localhost:8000/docs` : interface Swagger UI listant tous les endpoints de l'API.

### 3.5 Détail du `docker-compose.yml`

```yaml
services:
  app:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: geneweb-app
    ports:
      - "8000:8000"       # exposé uniquement en local
    volumes:
      - ./src:/app/src    # le code source est monté en live-reload
    environment:
      - PYTHONUNBUFFERED=1
    command: uvicorn src.geneweb.main:app --reload --host 0.0.0.0 --port 8000
```

Le volume `./src:/app/src` permet de modifier le code source sans reconstruire l'image.

---

## 4. Alternative : déploiement sans Docker (venv Python)

Pour les utilisateurs ne souhaitant pas installer Docker :

### 4.1 Créer l'environnement virtuel

**Linux / macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 4.2 Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4.3 Lancer l'application

```bash
uvicorn src.geneweb.main:app --reload --host 127.0.0.1 --port 8000
```

> **Important :** utiliser `--host 127.0.0.1` (et non `0.0.0.0`) pour s'assurer que le serveur n'écoute que sur l'interface de loopback locale, sans exposer de port sur le réseau.

L'application est alors accessible sur : **http://localhost:8000**

---

## 5. Données et persistance

### 5.1 Base de données

L'application utilise **SQLite** comme base de données. Le fichier `test.db` est créé à la racine du projet dès le premier démarrage. Ce fichier contient toutes les données genealogiques saisies.

```
G-ING-900-PAR-9-1-legacy-1/
└── test.db    ← base SQLite locale, ne jamais versionner ni partager
```

> **⚠️ Ce fichier contient des données personnelles. Il ne doit jamais être commité dans le dépôt Git** (il est listé dans `.gitignore`), **ni transmis à un tiers sans consentement explicite des personnes concernées.**

### 5.2 Fichiers GEDCOM

Les fichiers GEDCOM importés ou exportés par l'application doivent rester dans un répertoire local sous contrôle de l'utilisateur. Ils ne doivent pas être stockés sur des services de partage cloud (Google Drive, Dropbox, OneDrive, etc.) sans chiffrement préalable.

### 5.3 Sauvegardes

Pour sauvegarder les données :

```bash
# Copier la base SQLite
cp test.db test.db.backup-$(date +%Y%m%d)
```

Les sauvegardes doivent être conservées sur un support local chiffré (ex. : volume VeraCrypt, BitLocker, FileVault).

---

## 6. Ce qu'il ne faut pas faire

Les configurations suivantes sont **incompatibles avec les exigences RGPD** de ce projet et ne doivent pas être mises en place :

| Configuration interdite | Raison |
|---|---|
| Déploiement sur un VPS / cloud public (AWS, GCP, Azure, OVH…) | Les données transitent hors du périmètre de contrôle de l'utilisateur |
| Exposition du port `8000` sur une interface réseau publique | Accès possible par des tiers non autorisés |
| Utilisation d'une base de données distante (PostgreSQL distant, RDS…) | Les données personnelles quittent la machine locale |
| Hébergement de l'image Docker sur un registry public | Risque d'exposition du code et des secrets |
| Partage du fichier `test.db` par email ou messagerie | Transmission de données personnelles non chiffrées |

---

## 7. Tableau de conformité RGPD

| Principe RGPD | Mise en œuvre dans ce projet |
|---|---|
| **Minimisation des données** | Seules les données saisies par l'utilisateur sont stockées |
| **Intégrité et confidentialité** | Données stockées localement, pas de transit réseau |
| **Limitation de la finalité** | Usage généalogique personnel uniquement |
| **Responsabilité** | L'utilisateur local est l'unique responsable de traitement |
| **Droit d'accès / rectification / effacement** | Contrôle total via l'interface ou suppression du fichier `test.db` |

---

## 8. Références

- [RGPD — Règlement (UE) 2016/679](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX%3A32016R0679)
- [CNIL — Guide RGPD pour les développeurs](https://www.cnil.fr/fr/guide-rgpd-du-developpeur)
- [docs/architecture/SECURITY_PRIVACY.md](architecture/SECURITY_PRIVACY.md) — mesures de sécurité applicatives
- [INSTALL.md](../INSTALL.md) — guide d'installation complet
- [docker/Dockerfile](../docker/Dockerfile) — définition de l'image Docker
- [docker-compose.yml](../docker-compose.yml) — configuration du déploiement local
