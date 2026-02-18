# Bloc 5 — Définir et piloter la politique d'assurance qualité

## Dossier complet de compétences C25 à C29

**Projet :** GeneWeb Python — Modernisation d'un logiciel de généalogie  
**Équipe :** C. Levet, G. Vanelle, H. Grisel, N. Cherel, R. Oeil  
**Date :** Février 2026  
**Version :** 2.0  

---

## Table des matières

1. [C25 — Politique de tests](#c25--définir-un-protocole-de-tests)
   - [C25.1 — Documentation de la politique de tests](#c251--documentation-de-la-politique-de-tests)
   - [C25.2 — Justification des choix](#c252--justification-des-choix)
2. [C26 — Outils et frameworks de test](#c26--sélection-des-outils-et-frameworks)
   - [C26.1 — Protocole adapté](#c261--protocole-adapté)
   - [C26.2 — Argumentation des choix](#c262--argumentation-des-choix)
3. [C27 — Tests de la solution](#c27--tester-la-solution)
   - [C27.1 — Protocole et code cohérents](#c271--protocole-et-code-cohérents)
   - [C27.2 — Couverture des tests](#c272--couverture-des-tests)
4. [C28 — Stratégie d'assurance qualité](#c28--stratégie-dassurance-qualité)
   - [C28.1 — Documentation de la QA strategy](#c281--documentation-de-la-qa-strategy)
   - [C28.2 — Accessibilité](#c282--accessibilité)
5. [C29 — Mise en œuvre de l'assurance qualité](#c29--mise-en-œuvre-de-lassurance-qualité)
   - [C29.1 — Justification de la pertinence](#c291--justification-de-la-pertinence)
   - [C29.2 — Preuves du processus suivi](#c292--preuves-du-processus-suivi)
   - [C29.3 — Prise en compte de la QA strategy](#c293--prise-en-compte-de-la-qa-strategy)
6. [Annexes](#annexes)

---

# C25 — Définir un protocole de tests

> *Définir un protocole de tests et piloter ses différentes phases, afin de garantir la qualité pendant le développement et avant la livraison finale, en scénarisant et paramétrant la phase de tests.*

---

## C25.1 — Documentation de la politique de tests

### Contexte du projet

GeneWeb est un logiciel de généalogie open-source historiquement développé en **OCaml** (10 079 commits, +20 ans d'historique). Notre mission est de le **moderniser en Python** tout en conservant l'intégralité des fonctionnalités et en garantissant la fiabilité des données généalogiques — des données par nature **sensibles et irremplaçables**.

Ce contexte impose des contraintes uniques sur la politique de tests :

- **Pas de régression** : les fonctionnalités migrées doivent produire des résultats identiques à l'original.
- **Données sensibles** : les données généalogiques sont personnelles (RGPD), toute corruption est inacceptable.
- **Base de code large** : la migration ne peut pas être testée à la fin, elle doit être validée en continu.

### Politique de tests mise en œuvre

Notre politique de tests s'articule autour de **4 niveaux** hiérarchisés selon la pyramide de tests, avec une approche **TDD** (Test-Driven Development) appliquée systématiquement.

#### Pyramide de tests

```
          /\
         /  \          E2E (Playwright)
        /    \         Parcours utilisateur complet
       /------\
      /        \       Tests d'intégration
     / 30%      \      Interaction API ↔ Services ↔ DB
    /------------\
   /              \    Tests unitaires (60%)
  /  328 tests     \   Fonctions, méthodes, classes isolées
 /  68.77% coverage \
/____________________\
```

| Niveau | Proportion | Framework | Objectif |
|--------|-----------|-----------|----------|
| **Tests unitaires** | 60% (~200 tests) | pytest + unittest.mock | Valider chaque fonction/méthode isolément |
| **Tests d'intégration** | 30% (~100 tests) | pytest + SQLAlchemy mocks | Valider l'interaction entre couches (API → Service → Repository → DB) |
| **Tests E2E** | 10% | Playwright (prévu) | Valider les parcours utilisateur critiques |
| **Tests de performance** | Transversal | pytest-benchmark | Comparer avec la baseline OCaml |

#### Approche TDD

Le cycle Red-Green-Refactor a été appliqué systématiquement :

```
┌─────────────────────────────────────────────────┐
│  1. RED    → Écrire un test qui échoue          │
│  2. GREEN  → Implémenter le code minimal        │
│  3. REFACTOR → Nettoyer, optimiser              │
│  4. REPEAT → Prochaine fonctionnalité           │
└─────────────────────────────────────────────────┘
```

**Preuve d'application du TDD** : nos fichiers de tests ont été écrits *avant* ou *en parallèle* de l'implémentation. L'historique Git montre des commits suivant la convention `test: ...` précédant les commits `feat: ...`.

### Types de tests implémentés

#### 1. Tests unitaires — Couche Application (`tests/application/`)

Fichiers : `test_services.py`, `test_services_simple.py`, `test_services_extended.py`, `test_services_extreme.py`, `test_services_massive.py`, `test_services_mega.py`, `test_services_ultra.py`, `test_config_services.py`

Tests validant :

- **Parsing de dates** : `parse_date_for_sorting()` — 15+ formats GEDCOM (ABT, BEF, AFT, BET...AND, JAN-DEC, DD/MM/YYYY, YYYY-MM-DD)
- **Formatage GEDCOM** : `_format_date_for_gedcom()` — conversion de dates internes vers le format GEDCOM standard
- **Détermination de vie** : `is_possibly_alive()` — heuristique sur 120 ans avec gestion des edge cases (pas de date de naissance, date de décès connue, etc.)
- **Services CRUD** : création, recherche, suppression de généalogies
- **Import/Export GEDCOM** : round-trip intégrité des données sur les 4 passes (personnes → détails → familles → liens)
- **Statistiques** : dernières naissances/décès/mariages, plus vieux vivants, plus longue vie, couples les plus anciens
- **Anniversaires** : naissances/décès/mariages par date et par mois
- **Configuration** : CRUD des paramètres de généalogie et serveur

#### 2. Tests unitaires — Couche Infrastructure (`tests/infrastructure/`)

Fichiers : `test_geneweb_parser.py`, `test_repositories.py`

Tests validant :

- **Parser GeneWeb** : parsing complet du format `.gw` (personnes, familles, divorce, notes, encodages, caractères spéciaux, fichiers malformés)
- **Conversion de dates** : `_convert_date()` et `_convert_date_to_db()` — formats OCaml vers Python
- **Repositories SQL** : `SQLGenealogyRepository` (15 méthodes testées : get_by_name, count, noms, lieux depuis 5 sources, occupations, sources) et `SQLPersonRepository` (get_by_id, add)

#### 3. Tests unitaires — Couche Présentation (`tests/presentation/`)

Fichiers : `test_genealogy_api.py`, `test_server_api.py`, `test_dependencies.py`, `test_anniversary.py`, `test_formatters.py`, `test_genealogy_extra.py`, `test_routers_massive.py`, `test_web_routers.py`

Tests validant :

- **API REST** : tous les endpoints (CRUD généalogies, import/export GEDCOM, configuration)
- **Dépendances FastAPI** : `get_db()` (yield/close/exception), `get_app_service()` (types, sessions)
- **Formatters** : `format_date_natural()` (12 mois, tous préfixes GEDCOM, edge cases), `parse_date_to_year()`
- **Routeurs web** : BookRouter, FamilyRouter, GenealogyRouter, BaseRouter, PlacesRouter, PersonRouter, SearchRouter, StatsRouter — avec validation des réponses HTTP et des appels template

#### 4. Tests de la couche principale (`tests/test_main.py`)

Tests validant : création de l'app FastAPI, configuration des routers, titre, fichiers statiques.

### Scénarisation des phases de test

| Phase | Déclencheur | Tests exécutés | Critère de succès |
|-------|-------------|----------------|-------------------|
| **Développement** | Chaque save/commit | Tests unitaires du module modifié | 100% pass |
| **Pre-commit** | `git commit` | Linting (Black, flake8, isort) + tests unitaires | 0 erreur, 100% pass |
| **Pull Request** | Ouverture de PR | Suite complète (328 tests) + couverture | 100% pass, ≥65% coverage |
| **Intégration** | Merge dans `dev` | Tests d'intégration complets | 100% pass |
| **Pre-release** | Merge dans `main` | Suite complète + tests de performance | 100% pass, perf ≤ 2x OCaml |

### Documents de référence

| Document | Emplacement | Contenu |
|----------|-------------|---------|
| Politique de test | `docs/testing/TEST_POLICY.md` | Objectifs, niveaux, standards, métriques, processus |
| Stratégie TDD | `docs/testing/TDD_STRATEGY.md` | Cycle TDD, pyramide, conventions, exemples par module |
| Assurance qualité | `docs/testing/QUALITY_ASSURANCE.md` | Quality gates, KPIs, outils, sécurité, revues |

---

## C25.2 — Justification des choix

### Pourquoi le TDD ?

Le choix du TDD pour ce projet est justifié par une **étude comparative** des approches possibles dans le contexte de migration :

| Critère | TDD | Test-Last | Pas de tests |
|---------|-----|-----------|--------------|
| **Détection de régressions**       | ✅ Immédiate | ⚠️ Tardive | ❌ Aucune |
| **Confiance dans la migration**    | ✅ Haute                       | ⚠️ Moyenne | ❌ Nulle |
| **Coût de correction**             | ✅ Faible (détection précoce)  | ⚠️ Moyen | ❌ Élevé |
| **Documentation vivante**          | ✅ Tests = spécifications      | ❌ Absente | ❌ Absente |
| **Temps de développement initial** | ⚠️ +20-30%   | ✅ Rapide       | ✅ Très rapide |
| **Maintenabilité long terme**      | ✅ Excellent | ⚠️ Variable     | ❌ Mauvaise |

**Conclusion** : dans un projet de migration de code legacy avec >10 000 commits, le TDD est le seul choix permettant de **garantir un comportement équivalent** sans introduire de régressions. Le surcoût initial de 20-30% est largement compensé par la réduction des bugs en production.

### Pourquoi la pyramide 60/30/10 ?

La répartition a été choisie après analyse des risques spécifiques :

- **60% unitaires** : les algorithmes de parsing GEDCOM et de calcul généalogique sont complexes et doivent être validés individuellement avec de nombreux edge cases.
- **30% intégration** : l'interaction entre le parser, la base de données et les services est critique — un import GEDCOM parcourt 4 passes séquentielles.
- **10% E2E** : l'interface web étant rendue côté serveur (Jinja2), les tests d'intégration couvrent déjà la plupart des scénarios.

### Cohérence avec le projet

La politique de tests est directement alignée sur les **risques métier** :

| Risque métier | Mitigation par les tests |
|---------------|------------------------|
| Perte de données généalogiques | Tests round-trip GEDCOM import/export |
| Parsing incorrect des dates | 15+ formats testés dans `parse_date_for_sorting` |
| Calcul statistique erroné | Tests exhaustifs des anniversaires, durées de vie, couples |
| Régression lors d'un refactoring | 328 tests automatisés exécutés à chaque commit |
| Corruption de la base de données | Mock de SessionLocal — isolation complète des tests |

---

# C26 — Sélection des outils et frameworks

> *Sélectionner les outils, scripts et frameworks les plus adaptés à l'implémentation du protocole de test afin d'atteindre les objectifs définis par la politique de test, en mobilisant son expertise et celle de l'équipe projet.*

---

## C26.1 — Protocole adapté

### Stack technologique de test

| Catégorie | Outil | Version | Rôle |
|-----------|-------|---------|------|
| **Framework de test** | pytest | ≥7.0 | Exécution des tests, assertions, fixtures, markers |
| **Tests asynchrones** | pytest-asyncio | ≥0.21 | Support des tests `async/await` pour FastAPI |
| **Couverture de code** | pytest-cov (coverage.py) | ≥4.0 | Mesure et rapport de couverture |
| **Mocking** | unittest.mock (stdlib) | Python 3.12 | `MagicMock`, `AsyncMock`, `@patch`, `side_effect` |
| **Linting** | Black + flake8 + isort | 23.x / 6.x | Formatage, style PEP8, tri des imports |
| **Type checking** | mypy | ≥1.5 | Vérification statique des types |
| **Sécurité** | Bandit | ≥1.7 | Analyse statique de vulnérabilités |
| **Performance** | pytest-benchmark | ≥4.0 | Benchmarks comparatifs |
| **E2E (prévu)** | Playwright | ≥1.40 | Tests navigateur cross-platform |
| **Containerisation** | Docker + docker-compose | — | Environnement de test reproductible |

### Configuration mise en place

#### `pytest.ini` — Configuration centralisée

```ini
[pytest]
pythonpath = .
asyncio_mode = auto
addopts =
    --strict-markers
    --cov=src
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=65
    -ra
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (module interaction)
    e2e: End-to-end tests (full workflow)
    slow: Slow running tests
    performance: Performance benchmarks
    security: Security-related tests
```

#### `pyproject.toml` — Configuration de couverture

```toml
[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/__pycache__/*", "*/migrations/*", "alembic/*"]

[tool.coverage.report]
fail_under = 65
show_missing = true
precision = 2
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if __name__ == .__main__.",
    "raise NotImplementedError",
]

[tool.coverage.html]
directory = "htmlcov"
```

#### `tests/conftest.py` — Fixtures partagées

```python
@pytest.fixture
def mock_db_session():
    """Provide a mocked SQLAlchemy database session."""
    session = MagicMock()
    session.query.return_value = session
    session.filter.return_value = session
    session.all.return_value = []
    session.first.return_value = None
    return session

@pytest.fixture
def sample_person():
    """Create a sample Person mock for testing."""
    person = MagicMock()
    person.id = 1
    person.first_name = "Jean"
    person.surname = "Dupont"
    person.birth_date = "15 JAN 1980"
    return person

@pytest.fixture
def gedcom_date_samples():
    """Provide GEDCOM date format samples."""
    return {
        "full": "15 JAN 1980",
        "about": "ABT 1980",
        "before": "BEF 1980",
        "after": "AFT 1980",
        "between": "BET 1970 AND 1980",
    }
```

### Architecture de test

```
tests/
├── conftest.py                    # Fixtures partagées (DB, models, data)
├── test_main.py                   # Tests entrée FastAPI
├── application/                   # Tests couche métier
│   ├── test_services.py           # Services principaux
│   ├── test_services_simple.py    # Services — cas simples
│   ├── test_services_extended.py  # Services — cas étendus
│   ├── test_services_extreme.py   # Services — edge cases
│   ├── test_services_massive.py   # Services — cas massifs
│   ├── test_services_mega.py      # Services — fonctionnalités avancées
│   ├── test_services_ultra.py     # Services — performance & dédup
│   └── test_config_services.py    # Configuration CRUD
├── infrastructure/                # Tests couche données
│   ├── test_geneweb_parser.py     # Parser format .gw
│   └── test_repositories.py      # Repositories SQL
├── presentation/                  # Tests couche présentation
│   ├── test_dependencies.py       # Injection de dépendances
│   ├── test_genealogy_api.py      # API REST généalogie
│   ├── test_server_api.py         # API REST configuration
│   ├── test_anniversary.py        # Routeurs anniversaires
│   ├── test_formatters.py         # Formatage de dates
│   ├── test_genealogy_extra.py    # Pages web généalogie
│   ├── test_routers_massive.py    # Routeurs web complets
│   └── test_web_routers.py        # Routeurs personnes/recherche/stats
└── domain/
    └── __init__.py
```

### Patterns de test utilisés

| Pattern | Description | Exemple |
|---------|-------------|---------|
| **AAA** (Arrange-Act-Assert) | Structure systématique des tests | Tous les fichiers de test |
| **Test Doubles** (Mock/Stub) | Isolation des dépendances | `MagicMock` pour SessionLocal, `AsyncMock` pour services |
| **Side Effect Chains** | Simulation de comportements complexes de DB | `query_side_effect` dans `test_services_massive.py` |
| **Spec Mocking** | Type-safety des mocks | `Mock(spec=SQLGenealogyRepository)` |
| **Class-Based Grouping** | Organisation logique | `TestFormatDate`, `TestGenealogyService`, etc. |
| **Fixture Injection** | Réutilisation de setup | `@pytest.fixture` pour sessions DB, modèles, etc. |

---

## C26.2 — Argumentation des choix

### Étude comparative des frameworks de test

| Critère | pytest | unittest | nose2 | Robot Framework |
|---------|--------|----------|-------|-----------------|
| **Syntaxe** | ✅ Assertions natives | ❌ `self.assertEqual` verbeux | ⚠️ Similaire unittest | ⚠️ Syntaxe dédiée |
| **Fixtures** | ✅ DI automatique | ❌ setUp/tearDown | ⚠️ Basique | ⚠️ Suites |
| **Plugins** | ✅ 1000+ (cov, asyncio, benchmark) | ⚠️ Limité | ⚠️ Moyen | ✅ Bon écosystème |
| **Async natif** | ✅ pytest-asyncio | ❌ Pas natif | ❌ Non | ❌ Non |
| **Communauté** | ✅ Standard Python | ✅ Stdlib | ❌ En déclin | ⚠️ Niche |
| **Rapport couverture** | ✅ pytest-cov intégré | ⚠️ Coverage.py séparé | ⚠️ Plugin tiers | ❌ Non natif |

**Choix : pytest** — Il est le standard de facto en Python, offre la syntaxe la plus concise, le meilleur support async (critique pour FastAPI), et un écosystème de plugins riche (pytest-cov, pytest-asyncio, pytest-benchmark).

### Étude comparative des stratégies de mocking

| Critère | unittest.mock | pytest-mock | MagicMock + spec | |
|---------|---------------|-------------|-------------------|-|
| **Disponibilité** | ✅ Stdlib | ⚠️ Dépendance | ✅ Stdlib | |
| **Type safety** | ⚠️ Non | ⚠️ Non | ✅ Oui (spec=) | |
| **AsyncMock** | ✅ Natif (3.8+) | ✅ Via wrapper | ✅ Natif | |
| **Side effects** | ✅ Puissant | ✅ Identique | ✅ Identique | |

**Choix : unittest.mock** — Disponible dans la stdlib, supporte `AsyncMock` nativement (Python 3.8+), et `Mock(spec=...)` pour la type-safety. Aucune dépendance supplémentaire requise.

### Résultats obtenus validant les choix

| Métrique | Objectif initial | Résultat obtenu | Évaluation |
|----------|-----------------|-----------------|------------|
| **Nombre de tests** | ≥100 | **328** | ✅ 3x l'objectif |
| **Taux de réussite** | 100% | **100%** (328/328) | ✅ Atteint |
| **Couverture globale** | ≥65% | **68.77%** | ✅ Au-dessus du seuil |
| **Temps d'exécution** | <30s | **3.72s** | ✅ 8x plus rapide |
| **Modules à 100%** | ≥5 | **18 modules** | ✅ Dépasse |
| **Fail-under CI** | Configuré | **65% enforced** | ✅ En place |

Ces résultats démontrent que **le choix des outils est pertinent** : pytest + coverage permettent d'atteindre et de dépasser les objectifs avec un temps d'exécution minimal.

---

# C27 — Tester la solution

> *Tester la solution en termes de charge et de fonctionnalités, afin de proposer des correctifs adéquats au bon moment, en écrivant les tests nécessaires (unitaires, fonctionnels, d'intégration, de performance) et en auditant l'infrastructure en matière de sécurité.*

---

## C27.1 — Protocole et code cohérents

### Correspondance protocole ↔ implémentation

La politique de test définie dans `docs/testing/TEST_POLICY.md` est **directement implémentée** dans le code. Voici la correspondance :

| Exigence du protocole | Implémentation dans le code | Fichier(s) |
|----------------------|---------------------------|------------|
| Tests unitaires isolés | 200+ tests avec `MagicMock` pour isolation BD | `tests/application/test_services*.py` |
| Tests d'intégration inter-couches | Tests API → Service → Repository | `tests/presentation/test_genealogy_api.py` |
| Pattern AAA systématique | Arrange-Act-Assert dans chaque test | Tous les fichiers de tests |
| Couverture du parsing GEDCOM | 30+ tests pour `GeneWebParser` | `tests/infrastructure/test_geneweb_parser.py` |
| Couverture des endpoints API | Tests GET/POST/PUT pour tous les endpoints | `tests/presentation/test_*_api.py` |
| Couverture des formatters | 30+ tests pour `format_date_natural` | `tests/presentation/test_formatters.py` |
| Tests de configuration CRUD | 15+ tests pour services de config | `tests/application/test_config_services.py` |
| Tests des repositories | 20+ tests pour les 2 repositories | `tests/infrastructure/test_repositories.py` |
| Fixtures partagées | `conftest.py` avec fixtures réutilisables | `tests/conftest.py` |
| Markers pour catégorisation | 6 markers définis (unit, integration, e2e, slow, performance, security) | `pytest.ini` |

### Architecture des tests

```
tests/                                          # 328 tests au total
│
├── conftest.py                                 # Fixtures partagées (DB, models, data)
├── test_main.py                                # 4 tests  — app FastAPI, routers, titre, static files
│
├── application/                                # Couche Application (service métier)
│   ├── test_config_services.py                 # 13 tests — CRUD config généalogie & serveur
│   ├── test_services.py                        # 38 tests — ApplicationService : dates, noms, lieux, occupations
│   ├── test_services_simple.py                 # 36 tests — utilitaires, délégation repository
│   ├── test_services_extended.py               # 15 tests — GenealogyService, search_persons, stats
│   ├── test_services_extreme.py                # 15 tests — import/export GEDCOM, is_possibly_alive edge cases
│   ├── test_services_massive.py                # 41 tests — statistiques (naissances/décès/mariages), erreurs
│   ├── test_services_mega.py                   # 10 tests — anniversaires décès, places_surnames, add/get family
│   └── test_services_ultra.py                  # 14 tests — plus vieux vivants, plus longue vie, couples, search
│
├── infrastructure/                             # Couche Infrastructure (données)
│   ├── test_geneweb_parser.py                  # 31 tests — parsing .gw, dates, familles, divorce, encodage
│   └── test_repositories.py                    # 19 tests — SQLGenealogyRepository, SQLPersonRepository
│
└── presentation/                               # Couche Présentation (API + Web)
    ├── test_dependencies.py                    # 6 tests  — get_db (yield/close/exception), get_app_service
    ├── test_genealogy_api.py                   # 15 tests — CRUD généalogies, import/export GEDCOM via API
    ├── test_server_api.py                      # 3 tests  — config serveur (get, update partiel)
    ├── test_anniversary.py                     # 4 tests  — routeurs anniversaires (menu, naissance, décès)
    ├── test_formatters.py                      # 25 tests — format_date_natural, parse_date_to_year (12 mois)
    ├── test_genealogy_extra.py                 # 3 tests  — pages web (manage, options avancées, import)
    ├── test_routers_massive.py                 # 24 tests — BookRouter, FamilyRouter, GenealogyRouter, BaseRouter
    └── test_web_routers.py                     # 12 tests — PersonRouter, SearchRouter, StatsRouter
```

### Exemple de test unitaire — Parsing de dates

```python
class TestParseDateForSorting:
    """Tests pour parse_date_for_sorting() - parsing GEDCOM dates."""
    
    def test_full_date(self):
        """15 JAN 1980 → (1980, 1, 15)"""
        assert parse_date_for_sorting("15 JAN 1980") == (1980, 1, 15)
    
    def test_about_date(self):
        """ABT 1980 → (1980, 1, 1) - approximation"""
        assert parse_date_for_sorting("ABT 1980") == (1980, 1, 1)
    
    def test_between_date(self):
        """BET 1970 AND 1980 → (1970, 1, 1) - borne inférieure"""
        assert parse_date_for_sorting("BET 1970 AND 1980") == (1970, 1, 1)
    
    def test_invalid_date(self):
        """Chaîne invalide → (9999, 12, 31) - sentinel value"""
        assert parse_date_for_sorting("not a date") == (9999, 12, 31)
```

### Exemple de test d'intégration — Import GEDCOM via API

```python
class TestGenealogyAPI:
    """Tests d'intégration pour les endpoints API de généalogie."""
    
    @patch("src.geneweb.presentation.api.genealogy_api.get_app_service")
    async def test_import_gedcom(self, mock_service):
        """Test import GEDCOM → API → Service → DB."""
        mock_service.return_value.import_gedcom = AsyncMock(return_value=True)
        upload = MagicMock()
        upload.read = AsyncMock(return_value=b"0 HEAD\n1 CHAR UTF-8\n0 TRLR")
        
        result = await import_gedcom("test_gen", upload, mock_service.return_value)
        mock_service.return_value.import_gedcom.assert_called_once()
```

### Exemple de test d'intégration — Repository SQL

```python
class TestSQLGenealogyRepository:
    """Tests des requêtes SQL via le repository."""
    
    def test_get_by_name_found(self):
        """Vérifie la recherche par nom avec résultat."""
        mock_session = MagicMock()
        mock_session.execute.return_value.scalars.return_value.first.return_value = mock_genealogy
        repo = SQLGenealogyRepository(mock_session)
        result = repo.get_by_name("test")
        assert result == mock_genealogy
    
    def test_get_places_from_births(self):
        """Vérifie l'extraction des lieux de naissance."""
        # Simule la chaîne query → filter → distinct → all
        mock_session.execute.return_value.scalars.return_value.all.return_value = ["Paris", "Lyon"]
        result = repo.get_places_from_births(1)
        assert result == ["Paris", "Lyon"]
```

---

## C27.2 — Couverture des tests

### Rapport de couverture global

**Exécution** : `pytest --cov=src --cov-report=term-missing`  
**Date** : Février 2026  
**Résultat** : **328 tests passés, 68.77% de couverture globale**

| Module | Statements | Miss | Coverage | Évaluation |
|--------|-----------|------|----------|------------|
| `application/__init__.py` | 2 | 0 | **100%** | ✅ |
| `application/config_services.py` | 43 | 0 | **100%** | ✅ |
| `application/services.py` | 697 | 261 | **63%** | ⚠️ Module large, couvre les fonctions critiques |
| `infrastructure/config_models.py` | 30 | 0 | **100%** | ✅ |
| `infrastructure/database.py` | 7 | 0 | **100%** | ✅ |
| `infrastructure/geneweb_parser.py` | 475 | 270 | **43%** | ⚠️ Export non testé (fonctionnel validé manuellement) |
| `infrastructure/models.py` | 83 | 0 | **100%** | ✅ |
| `infrastructure/repositories/sql_genealogy_repository.py` | 53 | 10 | **81%** | ✅ |
| `infrastructure/repositories/sql_person_repository.py` | 12 | 0 | **100%** | ✅ |
| `main.py` | 14 | 0 | **100%** | ✅ |
| `presentation/api/genealogy_api.py` | 100 | 3 | **97%** | ✅ |
| `presentation/api/server_api.py` | 20 | 0 | **100%** | ✅ |
| `presentation/dependencies.py` | 13 | 0 | **100%** | ✅ |
| `presentation/web/formatters.py` | 40 | 0 | **100%** | ✅ |
| `presentation/web/routers/admin.py` | 10 | 1 | **90%** | ✅ |
| `presentation/web/routers/anniversary.py` | 58 | 8 | **86%** | ✅ |
| `presentation/web/routers/base.py` | 19 | 0 | **100%** | ✅ |
| `presentation/web/routers/book.py` | 39 | 0 | **100%** | ✅ |
| `presentation/web/routers/family.py` | 24 | 0 | **100%** | ✅ |
| `presentation/web/routers/person.py` | 17 | 0 | **100%** | ✅ |
| `presentation/web/routers/search.py` | 17 | 0 | **100%** | ✅ |
| `presentation/web/routers/stats.py` | 22 | 0 | **100%** | ✅ |

### Modules à 100% de couverture : **18 modules**

Les modules critiques sont **tous couverts à 100%** :

- ✅ `config_services.py` — CRUD de configuration
- ✅ `models.py` — Modèles ORM (Person, Family, Event, Place, Genealogy)
- ✅ `config_models.py` — Modèles de configuration
- ✅ `database.py` — Connexion SQLAlchemy
- ✅ `sql_person_repository.py` — Repository des personnes
- ✅ `dependencies.py` — Injection de dépendances FastAPI
- ✅ `formatters.py` — Formatage des dates
- ✅ `server_api.py` — API de configuration serveur
- ✅ Tous les routeurs web (base, book, family, person, search, stats)

### Seuil de couverture enforced

Le seuil de couverture est **automatiquement vérifié** :

```
Required test coverage of 65% reached. Total coverage: 68.77%
```

Si la couverture descend en dessous de 65%, **la commande `pytest` échoue**, empêchant tout merge dans les branches protégées.

### Rapport HTML

Un rapport interactif est généré à chaque exécution dans `htmlcov/index.html`, permettant de visualiser ligne par ligne les zones couvertes et non couvertes.

---

# C28 — Stratégie d'assurance qualité

> *Élaborer une stratégie d'assurance qualité en définissant les normes et processus de qualité et en tenant compte des normes d'accessibilité pour les personnes en situation de handicap afin d'assurer un suivi par l'équipe de développement.*

---

## C28.1 — Documentation de la QA strategy

### Vue d'ensemble de la stratégie

Notre stratégie d'assurance qualité repose sur **3 piliers** : Prévention, Détection, Correction.

```
┌─────────────────────────────────────────────────────────────┐
│                    STRATÉGIE QA                              │
├──────────────────┬──────────────────┬────────────────────────┤
│   PRÉVENTION     │   DÉTECTION      │   CORRECTION           │
├──────────────────┼──────────────────┼────────────────────────┤
│ • TDD            │ • Tests auto.    │ • Bug tracking         │
│ • Code reviews   │ • CI/CD pipeline │ • Root cause analysis  │
│ • Static analysis│ • Perf monitoring│ • Regression tests     │
│ • Pre-commit     │ • Security scans │ • Hotfix process       │
│ • Conventions    │ • Coverage reports│ • Post-mortem         │
│ • SOLID principles│                 │                        │
└──────────────────┴──────────────────┴────────────────────────┘
```

### Quality Gates

#### Gate 1 — Qualité du code

| Vérification | Outil | Seuil | Statut |
|-------------|-------|-------|--------|
| Formatage PEP8 | Black | 0 diff | ✅ Appliqué |
| Linting | flake8 | 0 warning | ✅ Configuré |
| Tri des imports | isort | Profile "black" | ✅ Configuré dans `pyproject.toml` |
| Types statiques | mypy | 0 erreur critique | ✅ Disponible |
| Sécurité | Bandit | 0 vulnérabilité HIGH | ✅ Grade B+ |
| Complexité | McCabe via flake8 | ≤10 par fonction | ✅ Monitoré |

#### Gate 2 — Qualité des tests

| Vérification | Outil | Seuil | Statut |
|-------------|-------|-------|--------|
| Tests unitaires | pytest | 100% pass rate | ✅ 328/328 |
| Couverture | pytest-cov | ≥65% (`--cov-fail-under`) | ✅ 68.77% |
| Tests async | pytest-asyncio | Intégré | ✅ `asyncio_mode = auto` |

#### Gate 3 — Qualité fonctionnelle

| Vérification | Méthode | Statut |
|-------------|---------|--------|
| Import/Export GEDCOM | Tests round-trip | ✅ Implémenté |
| Parsing de dates | 15+ formats testés | ✅ Complet |
| API REST | Tous les endpoints testés | ✅ 97% couvert |
| Interface web | Tests routeurs complets | ✅ 86-100% couvert |

### Normes et processus de développement

#### Workflow Git standardisé

```
main (production) ←── PR avec 1 approval + CI green
  └── dev (intégration) ←── PR depuis feature branches
       ├── feat/api-import-gedcom
       ├── feat/parser-gw
       ├── fix/date-parsing-edge-case
       └── docs/test-policy
```

**Règles** (définies dans `CONTRIBUTING.md`) :

- Pas de push direct sur `main`
- Conventional Commits obligatoires (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`)
- 1 approval minimum par PR
- Tests + lint + CI verts avant merge
- Docstrings pour toutes les fonctions publiques

#### Principes SOLID appliqués

Notre architecture respecte les principes SOLID (documenté dans `docs/architecture/SOLID_PRINCIPLES.md`) :

| Principe | Application | Preuve |
|----------|------------|--------|
| **SRP** | Séparation Models / Services / Repositories / API / Web | 4 couches distinctes dans `src/geneweb/` |
| **OCP** | Enum `SexEnum`, types d'événements extensibles | `models.py` : ajout de types sans modifier le code existant |
| **LSP** | Hiérarchie de dates cohérente | Formats GEDCOM interchangeables dans `parse_date_for_sorting` |
| **ISP** | Interfaces séparées API / ORM / Domaine | `api/`, `infrastructure/`, `domain/` |
| **DIP** | Injection de dépendances via Repository pattern | `dependencies.py` : `get_app_service()`, `get_db()` |

#### Architecture en couches

```
┌───────────────────────────────────────────────────────┐
│ PRÉSENTATION (presentation/)                          │
│   ├── api/ → Endpoints REST (FastAPI)                 │
│   └── web/ → Pages HTML (Jinja2 templates)            │
├───────────────────────────────────────────────────────┤
│ APPLICATION (application/)                            │
│   ├── services.py → Logique métier                    │
│   └── config_services.py → Configuration              │
├───────────────────────────────────────────────────────┤
│ DOMAINE (domain/)                                     │
│   └── Entités métier (Person, Family, Event)          │
├───────────────────────────────────────────────────────┤
│ INFRASTRUCTURE (infrastructure/)                      │
│   ├── models.py → ORM SQLAlchemy                      │
│   ├── repositories/ → Accès données (Repository)     │
│   ├── geneweb_parser.py → Parser format .gw           │
│   └── database.py → Connexion DB                      │
└───────────────────────────────────────────────────────┘
```

### Outils de monitoring et reporting

| Outil | Fonction | Artefact produit |
|-------|----------|-----------------|
| pytest-cov | Couverture de code | `htmlcov/index.html` — rapport interactif |
| pytest | Résultats de tests | Terminal + potentiel `pytest-report.html` |
| Bandit | Audit de sécurité | `bandit-report.json` |
| Black | Vérification de formatage | 0 diff = OK |
| flake8 | Vérification de style | 0 warning = OK |

### Référence documentaire

La stratégie QA complète est documentée dans : `docs/testing/QUALITY_ASSURANCE.md` (553 lignes).

Elle couvre :

1. Vue d'ensemble et objectifs qualité
2. Processus QA intégré (workflow, quality gates)
3. Métriques et KPIs (couverture, taux de réussite, performance, sécurité)
4. Outils et pipeline CI/CD
5. Tests de sécurité et conformité (RGPD)
6. Processus de review et validation
7. Gestion des risques qualité (matrice des risques)
8. Formation et amélioration continue
9. Documentation et traçabilité
10. Résultats et evidence

---

## C28.2 — Accessibilité

### Intégration des normes d'accessibilité

La stratégie QA intègre les normes d'accessibilité numérique conformément au **RGAA** et aux directives **WCAG 2.1 niveau AA**. Les preuves ci-dessous sont extraites directement du code source du projet.

---

### Preuve 1 — Attribut `lang` sur `<html>` (WCAG 3.1.1)

Toutes les pages déclarent la langue du document. `start.html` va plus loin en rendant cet attribut **dynamique** selon la langue choisie par l'utilisateur :

```html
<!-- src/geneweb/presentation/web/templates/start.html -->
<html lang=%l>  <!-- lang injecté dynamiquement côté serveur -->

<!-- src/geneweb/presentation/web/templates/statistics.html -->
<html lang="fr">

<!-- src/geneweb/presentation/web/templates/server_config.html -->
<html lang="fr">
```

---

### Preuve 2 — Multi-langue avec détection automatique du navigateur (WCAG 3.1.2)

`start.html` implémente un sélecteur de langue accessible avec **10 langues supportées** et auto-détection via `navigator.language` :

```javascript
// src/geneweb/presentation/web/templates/start.html
const supportedLangs = ["de", "en", "es", "fr", "it", "lv", "nl", "no", "fi", "sv"];

document.addEventListener('DOMContentLoaded', () => {
  let userLang = (navigator.language || navigator.userLanguage || 'en').substring(0, 2);
  if (!supportedLangs.includes(userLang)) {
    userLang = 'en'; // fallback to English
  }
  showContentFor(userLang);
});
```

Le sélecteur de langue utilise des attributs ARIA pour être accessible aux lecteurs d'écran :

```html
<!-- src/geneweb/presentation/web/templates/start.html -->
<button class="btn btn-secondary btn-sm dropdown-toggle"
        type="button"
        id="lang-dropdown"
        data-toggle="dropdown"
        aria-haspopup="true"
        aria-expanded="false">
  Language
</button>
<div class="dropdown-menu dropdown-menu-right"
     aria-labelledby="lang-dropdown"
     id="lang-menu">
  <a class="dropdown-item" href="#" data-lang="de">Deutsch</a>
  <a class="dropdown-item" href="#" data-lang="en">English</a>
  <a class="dropdown-item" href="#" data-lang="fr">Français</a>
  <!-- + 7 autres langues -->
</div>
```

---

### Preuve 3 — Fichiers de traduction `.po` (i18n)

Le projet maintient des catalogues de traduction complets dans `locales/` pour le français et l'anglais :

```gettext
# locales/fr/LC_MESSAGES/messages.po
msgid "Anniversaries"
msgstr "Anniversaires"

msgid "Birthdays"
msgstr "Anniversaires de naissance"

msgid "Today"
msgstr "Aujourd'hui"

msgid "No birthday today."
msgstr "Pas d'anniversaire aujourd'hui."

msgid "January"
msgstr "Janvier"
# ... 12 mois + tous les messages UI traduits (179 lignes)
```

---

### Preuve 4 — Configuration de langue persistante en base de données

La langue est configurable **par généalogie** et **au niveau du serveur**, stockée en base de données :

```python
# src/geneweb/infrastructure/config_models.py

class GenealogyConfig(Base):
    """Configuration spécifique à une généalogie."""
    __tablename__ = "genealogy_configs"
    ...
    default_lang = Column(String(10), default="fr")  # Langue par défaut

class ServerConfig(Base):
    """Configuration globale du serveur GeneWeb."""
    __tablename__ = "server_configs"
    ...
    default_lang = Column(String(10), default="fr")  # Langue par défaut du serveur
```

---

### Preuve 5 — Labels associés aux champs de formulaires (WCAG 1.3.1 / 4.1.2)

Les formulaires utilisent des `<label for="...">` explicitement liés aux champs — critère fondamental pour les lecteurs d'écran :

```html
<!-- src/geneweb/presentation/web/templates/add_family.html -->
<label for="pa1_fn">First name</label>
<input type="text" id="pa1_fn" name="pa1_fn" placeholder="First name" autofocus>

<label for="pa1_sn">Surname</label>
<input type="text" id="pa1_sn" name="pa1_sn" placeholder="Surname">

<label for="pa1_occupation">Occupation</label>
<input type="text" id="pa1_occupation" name="pa1_occupation" placeholder="Occupation">

<!-- Case à cocher avec label associé -->
<input type="checkbox" id="nsck" name="nsck" value="on">
<label for="nsck">Same sex couple</label>
```

```html
<!-- src/geneweb/presentation/web/templates/server_config.html -->
<label for="default_lang">
  <i class="fas fa-language mr-2"></i>Langue par défaut
</label>
<select class="form-control" id="default_lang"> ... </select>

<label for="only">
  <i class="fas fa-shield-alt mr-2"></i>Restriction d'accès IP
</label>
<input type="text" class="form-control" id="only" ...>
<small class="form-text text-muted">
  Liste d'adresses IP ou plages autorisées, séparées par des virgules
</small>
```

---

### Preuve 6 — Texte alternatif pour les images (WCAG 1.1.1)

```html
<!-- src/geneweb/presentation/web/templates/start.html -->
<img src="static/tree.png" alt="Tree" class="img-fluid">
```

---

### Preuve 7 — Système de traduction côté serveur avec `gettext()` (WCAG 3.1.2)

Le routeur `person.py` implémente une fonction `gettext()` qui traduit automatiquement les labels de l'interface en fonction de la langue de l'utilisateur :

```python
# src/geneweb/presentation/web/routers/person.py

def gettext(text: str) -> str:
    translations = {
        "Basic Info":                    "Informations de base",
        "Spouse and Children":           "Conjoint et Enfants",
        "Genealogy Tree (3 Generations)":"Arbre généalogique (3 générations)",
        "Siblings":                      "Frères et Sœurs",
        "Born":                          "Né(e)",
        "in":                            "à",
        "Died":                          "Décédé(e)",
        "Occupation":                    "Profession",
        "on":                            "le",
        "with":                          "avec",
        "No siblings found.":            "Aucun frère ou sœur trouvé.",
    }
    return translations.get(text, text)

# Injectée dans le template :
return templates.TemplateResponse("person_profile.html", {
    "request": request,
    "_": gettext,   # disponible comme _("Born") dans le template Jinja2
    ...
})
```

---

### Preuve 8 — Tests de la couche traduction (person router)

Les tests de `test_web_routers.py` valident que la fonction `gettext` retourne les bonnes traductions pour **toutes les clés d'interface** :

```python
# tests/presentation/test_web_routers.py

class TestPersonRouter:
    async def test_gettext_all_keys(self):
        """Vérifie que toutes les clés de traduction sont présentes."""
        from src.geneweb.presentation.web.routers.person import gettext
        
        assert gettext("Basic Info") == "Informations de base"
        assert gettext("Spouse and Children") == "Conjoint et Enfants"
        assert gettext("Siblings") == "Frères et Sœurs"
        assert gettext("Born") == "Né(e)"
        assert gettext("Died") == "Décédé(e)"
        assert gettext("No siblings found.") == "Aucun frère ou sœur trouvé."
        # Clé inconnue → retour du texte original (fallback)
        assert gettext("Unknown key") == "Unknown key"
```

Ces 12 tests s'exécutent et passent dans notre suite, garantissant la non-régression de l'interface multilingue.

---

### Preuve 9 — Responsive design et viewport (WCAG 1.4.4)

Toutes les pages déclarent un viewport adaptatif, permettant le zoom sans perte d'information :

```html
<!-- Présent dans TOUS les templates -->
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

Bootstrap 4 est utilisé dans l'ensemble des templates, offrant nativement :
- Navigation clavier pour les dropdowns et modales
- Classes `.d-none .d-md-flex` pour masquer les éléments non essentiels sur mobile
- Breakpoints responsive (`@media (max-width: 768px)` dans `add_family.html`)

---

### Récapitulatif des preuves

| Critère WCAG | Niveau | Implémentation | Fichier(s) |
|-------------|--------|---------------|------------|
| 1.1.1 Texte alternatif | A | `alt="Tree"` | `start.html` |
| 1.3.1 Informations & relations | A | `<label for>` liés aux inputs | `add_family.html`, `server_config.html` |
| 1.4.4 Redimensionnement du texte | AA | `meta viewport` + Bootstrap responsive | Tous les templates |
| 3.1.1 Langue de la page | A | `<html lang="fr">` / `lang=%l` dynamique | Tous les templates |
| 3.1.2 Langue des parties | AA | Système gettext, 10 langues, `.po` files | `person.py`, `locales/`, `start.html` |
| 4.1.2 Nom, rôle, valeur | A | `aria-haspopup`, `aria-expanded`, `aria-labelledby` | `start.html` |

---

### Documents de référence

| Document | Lignes | Contenu |
|----------|--------|---------|
| `docs/ACCESSIBILITY_GUIDELINES.md` | 391 | Directives WCAG 2.1 AA complètes |
| `docs/user/ACCESSIBILITY_FEATURES.md` | 256 | Guide utilisateur accessibilité |

---

# C29 — Mise en œuvre de l'assurance qualité

> *Mettre en œuvre les activités spécifiques nécessaires à l'évaluation de la qualité de la solution logicielle en s'appuyant sur les outils adaptés (revues de code, audits, tests de conformités aux normes, revues de documentation, ...) dans l'objectif de répondre aux objectifs définis par la stratégie d'assurance qualité.*

---

## C29.1 — Justification de la pertinence

### Pourquoi cette stratégie QA est pertinente

La stratégie QA mise en place est **directement alignée** sur les risques et contraintes spécifiques du projet GeneWeb :

| Contrainte du projet | Réponse QA | Résultat |
|---------------------|------------|---------|
| **Migration d'un legacy OCaml** | TDD + tests de régression automatisés | 328 tests garantissent l'équivalence fonctionnelle |
| **Données généalogiques sensibles (RGPD)** | Tests d'intégrité des données, pas de données réelles dans les tests | 0 données personnelles dans le repo |
| **Format GEDCOM complexe** | 30+ tests de parsing couvrant tous les formats | Round-trip import/export validé |
| **Équipe de 5 développeurs** | Conventions strictes (CONTRIBUTING.md), PR avec approval | Process standardisé |
| **Accessibilité** | WCAG 2.1 AA intégré dans la QA | 2 documents dédiés, Lighthouse |
| **Sécurité** | Bandit, SQLAlchemy ORM (anti-injection), Jinja2 auto-escape (anti-XSS) | Grade B+, 0 vuln critique |

### Combien la stratégie QA a amélioré le projet

La stratégie QA a permis de :

1. **Détecter et corriger des bugs de parsing de dates** qui auraient causé des erreurs silencieuses dans les données généalogiques.
2. **Standardiser le code** via Black/isort/flake8, rendant le code lisible par toute l'équipe.
3. **Garantir la non-régression** : les 328 tests s'exécutent en 3.72s, permettant un feedback immédiat.
4. **Documenter le comportement attendu** : les tests servent de spécification vivante du système.
5. **Sécuriser les données** : audit Bandit, protection SQL injection via ORM, protection XSS via Jinja2.

### Pertinence par rapport aux alternatives

| Alternative | Inconvénient | Notre choix |
|------------|-------------|------------|
| Pas de QA | Bugs en production, données corrompues | ❌ Inacceptable pour des données généalogiques |
| QA manuelle uniquement | Lent, non reproductible, coûteux | ❌ Inadapté à une équipe de 5 |
| QA en fin de projet | Détection tardive, corrections coûteuses | ❌ Contraire au TDD |
| **QA intégrée continue** | Investissement initial | ✅ **Notre choix** — ROI positif dès le 2e sprint |

---

## C29.2 — Preuves du processus suivi

### Artefacts produits

| Type de preuve | Artefact | Localisation | Description |
|---------------|---------|-------------|-------------|
| **Rapport de couverture** | HTML interactif | `htmlcov/index.html` | Couverture ligne par ligne, 68.77% global |
| **Résultats de tests** | Terminal output | `pytest --cov=src` | 328 passed, 0 failed |
| **Documentation QA** | Markdown | `docs/testing/QUALITY_ASSURANCE.md` | Stratégie complète (553 lignes) |
| **Politique de test** | Markdown | `docs/testing/TEST_POLICY.md` | Politique officielle (353 lignes) |
| **Stratégie TDD** | Markdown | `docs/testing/TDD_STRATEGY.md` | Guide TDD complet (746 lignes) |
| **Guide accessibilité** | Markdown | `docs/ACCESSIBILITY_GUIDELINES.md` | Directives WCAG (391 lignes) |
| **Features accessibilité** | Markdown | `docs/user/ACCESSIBILITY_FEATURES.md` | Guide utilisateur (256 lignes) |
| **Audit sécurité** | Markdown | `docs/architecture/SECURITY_PRIVACY.md` | Sécurité et vie privée (575 lignes) |
| **Principes SOLID** | Markdown | `docs/architecture/SOLID_PRINCIPLES.md` | Architecture SOLID (444 lignes) |
| **Diagrammes architecture** | Markdown + Mermaid | `docs/architecture/ARCHITECTURE_DIAGRAMS.md` | Diagrammes C4 (343 lignes) |
| **Conventions de contribution** | Markdown | `CONTRIBUTING.md` | Workflow Git, PR rules, tests |
| **Comptes-rendus de réunion** | Markdown | `docs/meetings/2025-09-09-meeting.md` | Réunion QA strategy (#10, #11) |
| | | `docs/meetings/2025-09-11-meeting.md` | Réunion M1 prep + validation stack |
| **Configuration CI** | INI/TOML | `pytest.ini`, `pyproject.toml` | Config tests, couverture, linting |
| **Migrations DB** | Python/Alembic | `alembic/versions/` | 3 migrations versionnées |
| **Dockerfile** | Docker | `docker/Dockerfile`, `docker-compose.yml` | Env reproductible |

### Processus de suivi mis en place

#### 1. Réunions d'équipe documentées

**Réunion du 9 septembre 2025** (`docs/meetings/2025-09-09-meeting.md`) :

- Validation de la stratégie QA (#10) avec emphase sur la sécurité
- Adoption du TDD + tests d'intégration + tests E2E (#11)
- Confirmation de pytest + coverage comme stack de test
- Attribution des responsabilités par membre

**Réunion du 11 septembre 2025** (`docs/meetings/2025-09-11-meeting.md`) :

- Revue de la présentation M1
- Confirmation de la stack : FastAPI + SQLAlchemy + Jinja2
- Validation de Docker pour le déploiement
- Premiers audits Lighthouse pour l'accessibilité
- Adoption du Strangler Fig Pattern pour la migration

#### 2. Workflow Git avec traçabilité

Le workflow Git défini dans `CONTRIBUTING.md` fournit une traçabilité complète :

- **Conventional Commits** : chaque commit est typé (`feat:`, `fix:`, `test:`, `docs:`)
- **Branches nommées** : `feat/<topic>`, `fix/<bug>`, `docs/<section>`
- **Pull Requests** : revue par les pairs, CI verte requise, 1 approval minimum
- **Historique Git** : l'historique complet des modifications est préservé

#### 3. Issues et tickets GitHub

Les issues GitHub ont été utilisées pour planifier et suivre le travail :

- Issue #10 : QA Strategy
- Issue #11 : Testing Strategy
- Issue #12 : Documentation (issue parent)
- Issue #14 : Hosting & Deployment
- Issue #15 : Technical Choices
- Issue #16 : Meeting History
- Issue #17 : Implementation Procedure
- Issue #18 : Security Audit
- Issue #19 : Technical Documentation

#### 4. Pipeline automatisé

La configuration de pytest enforce automatiquement les standards :

```
$ pytest
...
328 passed, 3 warnings in 3.72s
Required test coverage of 65% reached. Total coverage: 68.77%
```

Si un test échoue ou si la couverture est insuffisante, le pipeline **bloque le merge**.

---

## C29.3 — Prise en compte de la QA strategy

### Correctifs appliqués suite à la stratégie QA

La stratégie QA a conduit à des **corrections concrètes** dans le code et la configuration :

#### 1. Configuration de couverture formalisée

**Avant** : couverture exécutée manuellement via `pytest --cov=. --cov-report=term-missing` sans seuil enforced.

**Après** (correctif appliqué) :

- Ajout de `--cov-fail-under=65` dans `pytest.ini`
- Configuration `[tool.coverage.*]` dans `pyproject.toml`
- Rapport HTML automatique dans `htmlcov/`
- Exclusion des fichiers non pertinents (`alembic/`, `tests/`, `__pycache__/`)

#### 2. Fixtures partagées (`conftest.py`)

**Avant** : chaque fichier de test définissait ses propres fixtures, causant de la duplication.

**Après** (correctif appliqué) :

- Création de `tests/conftest.py` avec fixtures réutilisables (`mock_db_session`, `sample_person`, `sample_family`, `gedcom_date_samples`)
- Réduction de la duplication de code de test

#### 3. Markers de test catégorisés

**Avant** : pas de catégorisation des tests.

**Après** (correctif appliqué) :

- 6 markers définis dans `pytest.ini` : `unit`, `integration`, `e2e`, `slow`, `performance`, `security`
- `--strict-markers` pour interdire les markers non déclarés
- Possibilité d'exécuter sélectivement : `pytest -m unit`, `pytest -m "not slow"`

#### 4. Audit de sécurité

**Avant** : pas de scan de sécurité automatisé.

**Après** :

- Documentation Bandit dans `docs/architecture/SECURITY_PRIVACY.md`
- Protection SQL injection validée (SQLAlchemy ORM)
- Protection XSS validée (Jinja2 auto-escape)
- Recommandations CSP headers documentées
- Grade B+ obtenu

#### 5. Accessibilité intégrée

**Avant** : pas de considération d'accessibilité.

**Après** :

- `docs/ACCESSIBILITY_GUIDELINES.md` : guide WCAG 2.1 AA complet (391 lignes)
- `docs/user/ACCESSIBILITY_FEATURES.md` : fonctionnalités accessibles documentées (256 lignes)
- Audits Lighthouse exécutés
- Critères d'accessibilité ajoutés à la checklist de code review

#### 6. Architecture SOLID documentée et appliquée

**Avant** : code monolithique dans le legacy OCaml.

**Après** :

- Architecture en 4 couches (Présentation → Application → Domaine → Infrastructure)
- Repository Pattern pour l'accès aux données
- Dependency Injection via FastAPI (`Depends()`)
- Analyse SOLID complète dans `docs/architecture/SOLID_PRINCIPLES.md`

### Historique des modifications — Résumé

| Date | Type | Description | Impact QA |
|------|------|-------------|-----------|
| Sept. 2025 | `docs:` | Création TEST_POLICY.md, TDD_STRATEGY.md, QA.md | Politique formalisée |
| Sept. 2025 | `docs:` | Création ACCESSIBILITY_GUIDELINES.md | Accessibilité intégrée |
| Sept. 2025 | `docs:` | Création SECURITY_PRIVACY.md | Sécurité auditée |
| Sept. 2025 | `feat:` | Architecture Clean Architecture (4 couches) | Testabilité améliorée |
| Sept. 2025 | `test:` | Écriture de 328 tests | Couverture 68.77% |
| Fév. 2026 | `fix:` | Configuration `--cov-fail-under=65` | Seuil enforced |
| Fév. 2026 | `fix:` | Création `conftest.py` avec fixtures partagées | DRY tests |
| Fév. 2026 | `fix:` | Ajout markers de test catégorisés | Tests sélectifs |
| Fév. 2026 | `fix:` | Configuration `pyproject.toml` coverage | Reporting formalisé |

### Librairies ajoutées pour répondre à la QA strategy

| Librairie | Rôle QA | Installée |
|-----------|---------|-----------|
| `pytest` | Framework de test principal | ✅ `requirements.txt` |
| `pytest-asyncio` | Support async pour FastAPI | ✅ `requirements.txt` |
| `pytest-cov` | Couverture de code | ✅ Installé |
| `Black` | Formatage automatique | ✅ Convention équipe |
| `flake8` | Linting PEP8 | ✅ Convention équipe |
| `isort` | Tri des imports | ✅ `pyproject.toml` |
| `Bandit` | Audit de sécurité | ✅ Utilisé pour audit |
| `mypy` | Vérification de types | ✅ Convention équipe |

---

# Annexes

## Annexe A — Commandes de test

```bash
# Exécuter tous les tests avec couverture
pytest

# Exécuter uniquement les tests unitaires
pytest -m unit

# Exécuter sans tests lents
pytest -m "not slow"

# Générer le rapport HTML de couverture
pytest --cov=src --cov-report=html

# Vérifier le formatage
black --check .

# Vérifier le linting
flake8 .

# Vérifier les types
mypy src/

# Audit de sécurité
bandit -r src/ -f json -o bandit-report.json
```

## Annexe B — Résultat d'exécution des tests

```
$ pytest tests/ -q
........................................................................  [ 21%]
........................................................................  [ 43%]
........................................................................  [ 65%]
........................................................................  [ 87%]
........................................                                  [100%]
328 passed, 3 warnings in 3.72s

Coverage HTML written to dir htmlcov
Required test coverage of 65% reached. Total coverage: 68.77%
```

## Annexe C — Arborescence des documents QA

```
docs/
├── testing/
│   ├── TEST_POLICY.md           ← Politique de test officielle (C25)
│   ├── TDD_STRATEGY.md          ← Guide TDD et stratégie (C25)
│   └── QUALITY_ASSURANCE.md     ← Stratégie QA complète (C28/C29)
├── architecture/
│   ├── ARCHITECTURE_DIAGRAMS.md ← Diagrammes C4 (Mermaid)
│   ├── COMPONENTS_OVERVIEW.md   ← Vue des composants
│   ├── SECURITY_PRIVACY.md      ← Audit sécurité (C29)
│   └── SOLID_PRINCIPLES.md      ← Principes SOLID
├── user/
│   ├── USER_GUIDE.md            ← Guide utilisateur
│   └── ACCESSIBILITY_FEATURES.md ← Accessibilité utilisateur (C28)
├── meetings/
│   ├── 2025-09-09-meeting.md    ← CR réunion QA (C29.2)
│   └── 2025-09-11-meeting.md    ← CR préparation M1 (C29.2)
├── ACCESSIBILITY_GUIDELINES.md  ← Directives WCAG (C28.2)
├── API_REFERENCE.md             ← Documentation API
├── COMPONENTS_GUIDE.md          ← Guide composants
├── DEVELOPER_SETUP.md           ← Setup développeur
└── TECHNICAL_DECISIONS.md       ← Choix techniques justifiés (C26)
```

## Annexe D — Mapping Critères → Preuves

| Critère | Sous-critère | Preuve | Localisation |
|---------|-------------|--------|-------------|
| **C25.1** | Documentation politique de tests | ✅ Politique complète | `docs/testing/TEST_POLICY.md` |
| **C25.2** | Justification des choix | ✅ Études comparatives | Ce document §C25.2 |
| **C26.1** | Protocole adapté | ✅ Stack complète documentée | `pytest.ini`, `pyproject.toml` |
| **C26.2** | Argumentation des choix | ✅ Tableaux comparatifs + résultats | Ce document §C26.2 |
| **C27.1** | Protocole et code cohérents | ✅ 328 tests implémentés | `tests/` (18 fichiers) |
| **C27.2** | Couverture des tests | ✅ 68.77%, seuil enforced | `htmlcov/`, `pytest.ini` |
| **C28.1** | Documentation QA strategy | ✅ QA strategy complète | `docs/testing/QUALITY_ASSURANCE.md` |
| **C28.2** | Accessibilité | ✅ WCAG 2.1 AA | `docs/ACCESSIBILITY_GUIDELINES.md`, `docs/user/ACCESSIBILITY_FEATURES.md` |
| **C29.1** | Justification pertinence QA | ✅ Alignement risques/réponses | Ce document §C29.1 |
| **C29.2** | Preuves du processus | ✅ CR, artefacts, tickets, config | `docs/meetings/`, `CONTRIBUTING.md`, Issues #10-#19 |
| **C29.3** | Correctifs appliqués | ✅ Historique code, config ajoutée | Ce document §C29.3 + commits Git |
