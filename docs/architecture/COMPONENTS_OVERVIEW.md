# Vue d'Ensemble des Composants GeneWeb

## Introduction

Ce document fournit une explication détaillée de tous les composants du projet GeneWeb, tant pour la version originale en OCaml que pour la version modernisée en Python. Il s'adresse aux développeurs qui souhaitent comprendre l'architecture globale et le rôle de chaque composant.

---

## Table des Matières

1. [Architecture Globale](#architecture-globale)
2. [GeneWeb Original (OCaml)](#geneweb-original-ocaml)
3. [GeneWeb Python (Modernisation)](#geneweb-python-modernisation)
4. [Correspondance entre les Composants](#correspondance-entre-les-composants)
5. [Flux de Données](#flux-de-données)

---

## Architecture Globale

GeneWeb est un logiciel de généalogie qui se compose de plusieurs parties :

```
┌─────────────────────────────────────────────────────────────┐
│                     INTERFACE UTILISATEUR                    │
│          (Interface Web, API REST, Ligne de commande)       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SERVEUR D'APPLICATION                     │
│         (gwd - GeneWeb Daemon ou FastAPI en Python)         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      LOGIQUE MÉTIER                          │
│    (Algorithmes, Calculs généalogiques, Validations)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   COUCHE DE DONNÉES                          │
│         (Base de données, Import/Export GEDCOM)              │
└─────────────────────────────────────────────────────────────┘
```

---

## GeneWeb Original (OCaml)

### Structure des Répertoires

```
geneweb/
├── bin/          # Exécutables et programmes principaux
├── lib/          # Bibliothèques et logique métier
├── hd/           # Fichiers d'interface (HTML, CSS, JS, images)
├── etc/          # Configuration et scripts de démarrage
├── plugins/      # Extensions et plugins
├── rpc/          # API RPC (Remote Procedure Call)
└── test/         # Tests unitaires et d'intégration
```

---

### 1. Répertoire `bin/` - Exécutables

Ce répertoire contient tous les programmes exécutables de GeneWeb. Chaque sous-dossier est un programme distinct.

#### **`gwd/`** - GeneWeb Daemon (Serveur Web)
**Rôle :** Serveur web principal qui expose l'interface utilisateur.

**Fonctionnalités :**
- Écoute les requêtes HTTP des utilisateurs
- Gère les sessions et l'authentification
- Génère les pages HTML dynamiques
- Sert les fichiers statiques (CSS, JS, images)

**Fichiers clés :**
- `gwd.ml` : Point d'entrée du serveur
- `request.ml` : Traitement des requêtes HTTP

**Utilisation :**
```bash
./gwd -hd <chemin_templates> -bd <chemin_bases> -p <port>
```

#### **`gwsetup/`** - Setup (Configuration et Administration)
**Rôle :** Interface d'administration pour configurer et gérer les bases de données.

**Fonctionnalités :**
- Création de nouvelles bases
- Configuration des paramètres
- Gestion des utilisateurs et permissions
- Nettoyage et maintenance

**Utilisation :**
```bash
./gwsetup -p <port>
```

#### **`gwc/`** - GeneWeb Compiler
**Rôle :** Compile les fichiers source (.gw) en base de données binaire.

**Fonctionnalités :**
- Lit les fichiers texte .gw
- Crée les index et structures de données
- Optimise le stockage

**Utilisation :**
```bash
./gwc <fichier.gw> -o <nom_base>
```

#### **`ged2gwb/`** - GEDCOM to GeneWeb
**Rôle :** Convertit les fichiers GEDCOM en base GeneWeb.

**Fonctionnalités :**
- Parse les fichiers GEDCOM (format standard de généalogie)
- Mappe les données vers le modèle GeneWeb
- Gère les encodages (ANSEL, UTF-8, etc.)

**Utilisation :**
```bash
./ged2gwb <fichier.ged> -o <nom_base>
```

#### **`gwb2ged/`** - GeneWeb to GEDCOM
**Rôle :** Exporte une base GeneWeb en fichier GEDCOM.

**Fonctionnalités :**
- Inverse de ged2gwb
- Permet l'interopérabilité avec d'autres logiciels

**Utilisation :**
```bash
./gwb2ged <nom_base> -o <fichier.ged>
```

#### **`gwu/`** - GeneWeb Uncompile
**Rôle :** Décompile une base binaire en fichier texte .gw.

**Fonctionnalités :**
- Extraction des données en format lisible
- Utile pour les sauvegardes et migrations

**Utilisation :**
```bash
./gwu <nom_base> > sauvegarde.gw
```

#### **`consang/`** - Consanguinity Calculator
**Rôle :** Calcule les coefficients de consanguinité.

**Fonctionnalités :**
- Parcourt l'arbre généalogique
- Identifie les ancêtres communs
- Calcule les coefficients de consanguinité

**Utilisation :**
```bash
./consang <nom_base>
```

#### **`connex/`** - Connexity Checker
**Rôle :** Vérifie la connexité de la base (liens entre personnes).

**Fonctionnalités :**
- Identifie les groupes de personnes connectées
- Détecte les individus isolés

#### **`gwdiff/`** - GeneWeb Diff
**Rôle :** Compare deux versions d'une base.

**Fonctionnalités :**
- Détecte les modifications
- Génère un rapport de différences

#### **`fixbase/`** - Database Repair
**Rôle :** Répare et corrige les incohérences dans une base.

**Fonctionnalités :**
- Vérifie l'intégrité des données
- Corrige les références cassées
- Nettoie les doublons

#### **`gwgc/`** - GeneWeb Garbage Collector
**Rôle :** Nettoie les données inutilisées.

#### **`gwexport/`** - GeneWeb Export
**Rôle :** Exporte des données dans différents formats.

#### **`update_nldb/`** - Update Name Database
**Rôle :** Met à jour la base de données de noms pour la recherche.

---

### 2. Répertoire `lib/` - Bibliothèques et Logique Métier

C'est le cœur de GeneWeb. Tous les algorithmes et la logique métier sont ici.

#### **Sous-répertoire `lib/core/`** - Structures de Données Fondamentales

##### **`def/`** - Définitions
**Rôle :** Définit les types de données de base.

**Fichiers principaux :**
- `def.ml` : Définitions des types Person, Family, etc.

**Structures clés :**
```ocaml
type person = {
  first_name : string;
  surname : string;
  occ : int;
  birth : date option;
  death : death option;
  (* ... *)
}

type family = {
  marriage : date option;
  father : person_id;
  mother : person_id;
  children : person_id array;
  (* ... *)
}
```

##### **`db/`** - Database Access Layer
**Rôle :** Gestion de l'accès à la base de données.

**Fichiers principaux :**
- `gwdb.ml` : Interface générique de base de données
- `dbdisk.ml` : Implémentation sur disque

**Fonctionnalités :**
- CRUD (Create, Read, Update, Delete) pour personnes et familles
- Indexation pour recherche rapide
- Gestion de la cohérence des données

#### **Algorithmes Généalogiques**

##### **`relation.ml`** - Calcul de Relations
**Rôle :** Calcule les relations de parenté entre deux personnes.

**Fonctionnalités :**
- Détecte : frères/sœurs, cousins, oncles/tantes, etc.
- Calcule le degré de parenté
- Gère les relations multiples

**Algorithme :**
1. Trouve tous les chemins entre deux personnes
2. Analyse les chemins pour déterminer la relation
3. Retourne la relation la plus proche

##### **`consang.ml`** - Consanguinité
**Rôle :** Calcule les coefficients de consanguinité.

**Algorithme de Jacquard :**
- Identifie les ancêtres communs
- Calcule la probabilité qu'un individu hérite du même allèle de ses deux parents
- Formule : F = Σ (1/2)^(n+m+1) × (1 + F_a)
  - n, m : nombre de générations entre l'individu et l'ancêtre commun
  - F_a : coefficient de consanguinité de l'ancêtre commun

##### **`sosa/`** - Numérotation Sosa-Stradonitz
**Rôle :** Attribue un numéro unique à chaque ancêtre.

**Système de numérotation :**
- Personne de référence (de cujus) : numéro 1
- Père : 2n (le double)
- Mère : 2n + 1
- Exemple : Le père (2), la mère (3), le grand-père paternel (4), etc.

**Utilité :**
- Navigation rapide dans l'arbre
- Identification unique des ancêtres

#### **Affichage et Génération de Vues**

Tous les fichiers `*Display.ml` génèrent du HTML pour l'interface web.

##### **`ascendDisplay.ml`** - Affichage des Ascendants
**Rôle :** Génère l'arbre d'ascendance.

##### **`descendDisplay.ml`** - Affichage des Descendants
**Rôle :** Génère l'arbre de descendance.

##### **`dag.ml` / `dag2html.ml`** - Directed Acyclic Graph
**Rôle :** Génère des graphes de relations complexes.

**Utilité :**
- Visualisation d'arbres avec mariages entre cousins
- Gestion des boucles généalogiques

##### **`perso.ml`** - Page Personnelle
**Rôle :** Génère la page de détails d'une personne.

**Contenu affiché :**
- Informations biographiques
- Parents, conjoint(s), enfants
- Événements de vie
- Notes et sources

#### **Édition et Mise à Jour**

##### **`update.ml` / `updateData.ml`**
**Rôle :** Gestion des modifications de la base.

**Fonctionnalités :**
- Validation des données
- Mise à jour atomique
- Historique des modifications

##### **`updateInd.ml` / `updateIndOk.ml`**
**Rôle :** Mise à jour des individus.

##### **`updateFam.ml` / `updateFamOk.ml`**
**Rôle :** Mise à jour des familles.

##### **`merge*.ml`** - Fusion
**Rôle :** Fusion de personnes ou familles en doublon.

**Process :**
1. Identification des doublons
2. Comparaison des données
3. Fusion intelligente (conservation des données les plus complètes)

#### **Recherche**

##### **`searchName.ml`**
**Rôle :** Recherche de personnes par nom.

**Algorithmes :**
- Recherche exacte
- Recherche phonétique (Soundex, Metaphone)
- Recherche approximative (Levenshtein)

##### **`advSearchOk.ml`** - Recherche Avancée
**Rôle :** Recherche multicritères.

**Critères disponibles :**
- Nom, prénom, date de naissance/décès
- Lieu, profession
- Combinaisons booléennes

#### **Validation et Vérification**

##### **`check.ml` / `checkData.ml`**
**Rôle :** Vérifie la cohérence des données.

**Vérifications :**
- Dates incohérentes (naissance après décès, etc.)
- Âges improbables pour avoir des enfants
- Références manquantes

#### **Utilitaires**

##### **`util.ml`**
**Rôle :** Fonctions utilitaires générales.

##### **`translate.ml`**
**Rôle :** Gestion de l'internationalisation.

**Langues supportées :**
- Français, anglais, allemand, néerlandais, suédois, etc.

##### **`templ/`** - Moteur de Templates
**Rôle :** Génération de pages HTML à partir de templates.

**Format :**
- Templates avec variables : `%first_name;`
- Conditions : `%if;...%end;`
- Boucles : `%foreach;...%end;`

##### **`wserver/`** - Web Server Components
**Rôle :** Composants de bas niveau du serveur web.

---

### 3. Répertoire `hd/` - Interface Utilisateur

```
hd/
├── etc/          # Templates HTML
├── lang/         # Fichiers de traduction
└── images/       # Images et ressources statiques
```

#### **`etc/`** - Templates
**Contenu :** Fichiers .txt avec le format de template GeneWeb.

**Exemples :**
- `perso.txt` : Template de la page personnelle
- `family.txt` : Template de la page famille
- `welcome.txt` : Page d'accueil

#### **`lang/`** - Traductions
**Fichiers :** `lexicon_xx.txt` (xx = code langue)

**Format :**
```
first_name: prénom
surname: nom de famille
birth: naissance
```

---

### 4. Répertoire `plugins/` - Extensions

**Rôle :** Extensions modulaires pour ajouter des fonctionnalités.

**Exemples de plugins :**
- Export vers des formats spécifiques
- Intégrations avec d'autres services
- Visualisations personnalisées

---

### 5. Répertoire `rpc/` - API RPC

**Rôle :** API pour accès programmatique aux données.

**Fonctionnalités :**
- Requêtes structurées en Protobuf
- Accès sans interface web
- Intégration avec d'autres applications

---

## GeneWeb Python (Modernisation)

### Structure des Répertoires

```
geneweb-python/
├── src/geneweb/          # Code source principal
│   ├── presentation/     # Interface (API, Web)
│   ├── application/      # Services et cas d'usage
│   ├── domain/           # Logique métier et algorithmes
│   └── infrastructure/   # BDD, persistence, I/O
├── tests/                # Tests unitaires et d'intégration
├── docs/                 # Documentation
├── alembic/              # Migrations de base de données
└── scripts/              # Scripts utilitaires
```

---

### 1. `src/geneweb/presentation/` - Couche Présentation

#### **`presentation/api/`** - API REST

**Rôle :** Expose les fonctionnalités via une API RESTful moderne.

**Technologie :** FastAPI

**Structure :**
```python
presentation/api/
├── routers/
│   ├── persons.py       # Routes pour les personnes
│   ├── families.py      # Routes pour les familles
│   ├── search.py        # Routes de recherche
│   └── relationships.py # Routes de calcul de relations
├── dependencies.py      # Dépendances (auth, DB session)
└── schemas.py           # Schémas Pydantic (validation)
```

**Exemples d'endpoints :**
```
GET    /api/v1/persons           # Liste des personnes
GET    /api/v1/persons/{id}      # Détails d'une personne
POST   /api/v1/persons           # Créer une personne
PUT    /api/v1/persons/{id}      # Modifier une personne
DELETE /api/v1/persons/{id}      # Supprimer une personne

GET    /api/v1/persons/{id}/ancestors    # Ancêtres
GET    /api/v1/persons/{id}/descendants  # Descendants

GET    /api/v1/relationship?p1={id1}&p2={id2}  # Relation entre deux personnes

POST   /api/v1/gedcom/import     # Importer un GEDCOM
GET    /api/v1/gedcom/export     # Exporter en GEDCOM
```

#### **`presentation/web/`** - Interface Web

**Rôle :** Interface utilisateur HTML.

**Technologie :** Jinja2 templates

**Structure :**
```python
presentation/web/
├── routers.py           # Routes web
├── templates/           # Templates HTML
│   ├── base.html
│   ├── person_detail.html
│   ├── family_tree.html
│   └── search.html
└── static/              # CSS, JavaScript, images
    ├── css/
    ├── js/
    └── images/
```

---

### 2. `src/geneweb/application/` - Couche Application

**Rôle :** Orchestration de la logique métier. Services qui coordonnent les opérations.

**Structure :**
```python
application/
├── services/
│   ├── person_service.py        # Gestion des personnes
│   ├── family_service.py        # Gestion des familles
│   ├── genealogy_service.py     # Calculs généalogiques
│   ├── search_service.py        # Recherche
│   └── import_export_service.py # Import/Export GEDCOM
└── dto/                         # Data Transfer Objects
    ├── person_dto.py
    └── family_dto.py
```

**Exemple de service :**
```python
class GenealogyService:
    def __init__(self, person_repo: PersonRepository):
        self.person_repo = person_repo
    
    def calculate_relationship(self, person1_id: int, person2_id: int) -> Relationship:
        """Calcule la relation entre deux personnes."""
        person1 = self.person_repo.get_by_id(person1_id)
        person2 = self.person_repo.get_by_id(person2_id)
        
        # Utilise l'algorithme du domaine
        return relationship_algorithm(person1, person2)
```

---

### 3. `src/geneweb/domain/` - Couche Domaine

**Rôle :** Logique métier pure, indépendante de la technologie.

#### **`domain/models.py`** - Modèles du Domaine

**Définitions avec Pydantic :**
```python
from pydantic import BaseModel
from datetime import date
from typing import Optional, List

class Person(BaseModel):
    id: Optional[int] = None
    first_name: str
    surname: str
    birth_date: Optional[date] = None
    death_date: Optional[date] = None
    sex: str  # 'M' ou 'F'
    
    # Relations
    father_id: Optional[int] = None
    mother_id: Optional[int] = None
    families_as_spouse: List[int] = []
    families_as_child: List[int] = []

class Family(BaseModel):
    id: Optional[int] = None
    father_id: int
    mother_id: int
    marriage_date: Optional[date] = None
    divorce_date: Optional[date] = None
    children_ids: List[int] = []
```

#### **`domain/algorithms.py`** - Algorithmes Généalogiques

**Contenu :** Portage Python des algorithmes OCaml.

**Exemples :**
```python
def calculate_consanguinity(person: Person, ancestors_cache: dict) -> float:
    """
    Calcule le coefficient de consanguinité selon l'algorithme de Jacquard.
    """
    # Implémentation de l'algorithme
    pass

def find_relationship(person1: Person, person2: Person) -> Relationship:
    """
    Trouve la relation de parenté entre deux personnes.
    """
    # BFS ou DFS pour trouver les chemins
    pass

def calculate_sosa_number(person: Person, root_person: Person) -> Optional[int]:
    """
    Calcule le numéro Sosa d'une personne par rapport à la racine.
    """
    # Algorithme de numérotation Sosa
    pass
```

#### **`domain/repositories.py`** - Interfaces des Repositories

**Rôle :** Définit les contrats (Protocols) pour l'accès aux données.

```python
from typing import Protocol, List, Optional

class PersonRepository(Protocol):
    def get_by_id(self, person_id: int) -> Optional[Person]:
        """Récupère une personne par son ID."""
        ...
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Person]:
        """Récupère toutes les personnes avec pagination."""
        ...
    
    def create(self, person: Person) -> Person:
        """Crée une nouvelle personne."""
        ...
    
    def update(self, person: Person) -> Person:
        """Met à jour une personne."""
        ...
    
    def delete(self, person_id: int) -> bool:
        """Supprime une personne."""
        ...
```

---

### 4. `src/geneweb/infrastructure/` - Couche Infrastructure

**Rôle :** Implémentations techniques (BDD, fichiers, etc.).

#### **`infrastructure/database.py`** - Configuration BDD

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:pass@localhost/geneweb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

#### **`infrastructure/models_db.py`** - Modèles SQLAlchemy

```python
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PersonDB(Base):
    __tablename__ = "persons"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    birth_date = Column(Date)
    death_date = Column(Date)
    sex = Column(String(1))
    
    father_id = Column(Integer, ForeignKey("persons.id"))
    mother_id = Column(Integer, ForeignKey("persons.id"))
    
    # Relations ORM
    father = relationship("PersonDB", foreign_keys=[father_id])
    mother = relationship("PersonDB", foreign_keys=[mother_id])
```

#### **`infrastructure/repositories/`** - Implémentations

```python
# infrastructure/repositories/sql_person_repository.py
from sqlalchemy.orm import Session
from typing import List, Optional

class SQLPersonRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, person_id: int) -> Optional[Person]:
        db_person = self.db.query(PersonDB).filter(PersonDB.id == person_id).first()
        if db_person:
            return self._to_domain(db_person)
        return None
    
    def create(self, person: Person) -> Person:
        db_person = PersonDB(**person.dict(exclude={'id'}))
        self.db.add(db_person)
        self.db.commit()
        self.db.refresh(db_person)
        return self._to_domain(db_person)
    
    def _to_domain(self, db_person: PersonDB) -> Person:
        """Convertit un modèle DB en modèle du domaine."""
        return Person(**db_person.__dict__)
```

#### **`infrastructure/gedcom/`** - Import/Export GEDCOM

```python
# infrastructure/gedcom/parser.py
class GedcomParser:
    def parse_file(self, filepath: str) -> List[Person]:
        """Parse un fichier GEDCOM et retourne une liste de personnes."""
        # Logique de parsing
        pass

# infrastructure/gedcom/exporter.py
class GedcomExporter:
    def export(self, persons: List[Person], filepath: str):
        """Exporte des personnes en fichier GEDCOM."""
        # Logique d'export
        pass
```

---

### 5. `tests/` - Tests

**Structure :**
```
tests/
├── domain/
│   ├── test_algorithms.py       # Tests des algorithmes
│   └── test_models.py           # Tests des modèles
├── application/
│   └── test_services.py         # Tests des services
├── infrastructure/
│   └── test_repositories.py     # Tests des repositories
└── presentation/
    ├── test_api.py              # Tests de l'API
    └── test_web.py              # Tests de l'interface web
```

**Exemple de test TDD :**
```python
# tests/domain/test_algorithms.py
import pytest
from geneweb.domain.algorithms import calculate_consanguinity
from geneweb.domain.models import Person

def test_consanguinity_between_siblings_with_non_consanguineous_parents():
    """
    Le coefficient de consanguinité entre frères/sœurs 
    avec parents non consanguins doit être 0.
    """
    father = Person(id=1, first_name="John", surname="Doe", sex="M")
    mother = Person(id=2, first_name="Jane", surname="Smith", sex="F")
    
    child1 = Person(id=3, first_name="Alice", surname="Doe", sex="F",
                    father_id=1, mother_id=2)
    
    assert calculate_consanguinity(child1, {}) == 0.0

def test_consanguinity_with_cousin_marriage():
    """
    Test avec mariage entre cousins germains.
    """
    # Création d'un arbre généalogique complexe
    # ...
    result = calculate_consanguinity(person, ancestors)
    assert result == pytest.approx(0.0625)  # 1/16
```

---

### 6. `alembic/` - Migrations de Base de Données

**Rôle :** Gestion des versions du schéma de base de données.

**Utilisation :**
```bash
# Créer une nouvelle migration
alembic revision -m "add persons table"

# Appliquer les migrations
alembic upgrade head

# Revenir en arrière
alembic downgrade -1
```

---

## Correspondance entre les Composants

| Composant OCaml | Composant Python | Description |
|-----------------|------------------|-------------|
| `bin/gwd/` | `presentation/web/` + `presentation/api/` | Serveur web et API |
| `bin/gwsetup/` | Interface admin dans `presentation/web/` | Configuration |
| `bin/ged2gwb/` | `infrastructure/gedcom/parser.py` | Import GEDCOM |
| `bin/gwb2ged/` | `infrastructure/gedcom/exporter.py` | Export GEDCOM |
| `bin/consang/` | `domain/algorithms.py::calculate_consanguinity()` | Calcul de consanguinité |
| `lib/def/` | `domain/models.py` | Modèles de données |
| `lib/db/` | `infrastructure/repositories/` | Accès aux données |
| `lib/relation.ml` | `domain/algorithms.py::find_relationship()` | Calcul de relations |
| `lib/sosa/` | `domain/algorithms.py::calculate_sosa_number()` | Numérotation Sosa |
| `lib/update.ml` | `application/services/person_service.py` | Mise à jour des données |
| `lib/searchName.ml` | `application/services/search_service.py` | Recherche |
| `lib/*Display.ml` | `presentation/web/templates/` | Génération de vues |
| `lib/templ/` | Jinja2 (intégré à FastAPI) | Moteur de templates |
| `lib/wserver/` | FastAPI + Uvicorn | Serveur web |

---

## Flux de Données

### Exemple : Affichage de la page d'une personne

#### Version OCaml :
```
1. Requête HTTP → gwd
2. gwd → perso.ml (logique de la page)
3. perso.ml → gwdb (récupération des données)
4. perso.ml → templ (génération HTML)
5. gwd → Réponse HTTP
```

#### Version Python :
```
1. Requête HTTP → FastAPI (presentation/api/routers/persons.py)
2. Router → PersonService (application/services/person_service.py)
3. PersonService → PersonRepository (domain/repositories.py)
4. PersonRepository → SQLPersonRepository (infrastructure/repositories/)
5. SQLAlchemy → PostgreSQL
6. Données remontent via les mêmes couches
7. FastAPI → Réponse JSON ou HTML (via Jinja2)
```

### Diagramme de Séquence (Python) :

```
┌─────────┐    ┌─────────┐    ┌──────────────┐    ┌────────────┐    ┌──────────┐
│ Client  │    │  API    │    │PersonService │    │ Repository │    │PostgreSQL│
└────┬────┘    └────┬────┘    └──────┬───────┘    └─────┬──────┘    └────┬─────┘
     │              │                 │                  │                 │
     │─GET /persons/123              │                  │                 │
     │──────────────>│                │                  │                 │
     │              │─get_person(123)│                  │                 │
     │              │───────────────>│                  │                 │
     │              │                │─get_by_id(123)   │                 │
     │              │                │─────────────────>│                 │
     │              │                │                  │─SELECT * FROM...│
     │              │                │                  │────────────────>│
     │              │                │                  │<────────────────│
     │              │                │<─────────────────│                 │
     │              │<───────────────│                  │                 │
     │<──────────────│                │                  │                 │
     │  JSON/HTML   │                │                  │                 │
```

---

## Conclusion

Cette documentation fournit une vue complète de l'architecture de GeneWeb, tant dans sa version originale OCaml que dans sa modernisation Python. 

**Points clés à retenir :**

1. **Séparation des responsabilités** : Chaque composant a un rôle précis
2. **Architecture en couches** : Domain, Application, Infrastructure, Presentation
3. **Testabilité** : L'architecture Python facilite le TDD
4. **Portabilité** : Les algorithmes du domaine sont indépendants de la technologie
5. **Interopérabilité** : Support du format GEDCOM standard

Pour plus de détails sur un composant spécifique, consultez :
- [Guide de développement](DEVELOPER_SETUP.md)
- [Architecture détaillée](ARCHITECTURE_DIAGRAMS.md)
- [Principes SOLID](SOLID_PRINCIPLES.md)

---

**Dernière mise à jour :** Octobre 2025
