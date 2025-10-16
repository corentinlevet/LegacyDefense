# Architecture GeneWeb Python - Diagrammes Techniques
## Documentation Visuelle Complète

**Version :** 1.0  
**Date :** September 2025  
**Équipe :** Architecture GeneWeb Python  

---

## 1. Vue d'Ensemble Système

### 1.1 Architecture Globale

```mermaid
graph TB
    subgraph "🌐 Presentation Layer"
        UI[Web Interface<br/>Jinja2 Templates]
        API[REST API<br/>FastAPI]
        CLI[Command Line<br/>Click Interface]
    end
    
    subgraph "🧠 Business Layer"
        ALG[Genealogy Algorithms<br/>Consanguinity, Sosa, Relations]
        GEDCOM[GEDCOM Parser<br/>Import/Export]
        TMPL[Template Engine<br/>Jinja2 + i18n]
    end
    
    subgraph "💾 Data Layer"
        DB[Database<br/>SQLAlchemy ORM]
        MODELS[Data Models<br/>Person, Family, Event]
        CACHE[Cache Layer<br/>LRU Memory Cache]
    end
    
    subgraph "🗄️ Storage"
        SQLITE[(SQLite<br/>Development)]
        POSTGRES[(PostgreSQL<br/>Production)]
        FILES[File Storage<br/>Images, Documents]
    end
    
    UI --> API
    CLI --> ALG
    API --> ALG
    API --> GEDCOM
    API --> TMPL
    ALG --> MODELS
    GEDCOM --> MODELS
    MODELS --> DB
    DB --> SQLITE
    DB --> POSTGRES
    API --> FILES
```

### 1.2 Migration OCaml vers Python

```mermaid
graph LR
    subgraph "🏛️ Legacy OCaml"
        GWD[gwd<br/>Web Daemon]
        GWB[.gwb Files<br/>Binary Format]
        OCAML_ALG[OCaml Algorithms<br/>consang.ml, sosa.ml]
    end
    
    subgraph "🔄 Migration Process"
        EXTRACT[Extract Logic<br/>Algorithm Analysis]
        CONVERT[Convert Data<br/>GEDCOM Bridge]
        VALIDATE[Validate Results<br/>Regression Tests]
    end
    
    subgraph "🐍 Modern Python"
        FASTAPI[FastAPI<br/>Web Application]
        SQLDB[SQL Database<br/>Relational Storage]
        PY_ALG[Python Algorithms<br/>Equivalent Logic]
    end
    
    GWD --> EXTRACT
    GWB --> CONVERT
    OCAML_ALG --> EXTRACT
    
    EXTRACT --> VALIDATE
    CONVERT --> VALIDATE
    
    VALIDATE --> FASTAPI
    VALIDATE --> SQLDB
    VALIDATE --> PY_ALG
```

---

## 2. Architecture Modulaire Détaillée

### 2.1 Structure des Modules Core

```mermaid
classDiagram
    class DatabaseManager {
        +engine: SQLAlchemy Engine
        +create_tables()
        +get_session()
        +add_person()
        +search_persons()
    }
    
    class GenealogyAlgorithms {
        +calculate_consanguinity()
        +find_relationship()
        +get_ancestors()
        +get_descendants()
        +sosa_numbering()
    }
    
    class GedcomParser {
        +parse_file()
        +export_gedcom()
        +validate_format()
    }
    
    class TemplateEnvironment {
        +render_template()
        +add_filter()
        +set_locale()
    }
    
    class GeneWebApp {
        +app: FastAPI
        +setup_routes()
        +run()
    }
    
    DatabaseManager --> PersonORM
    DatabaseManager --> FamilyORM
    GenealogyAlgorithms --> DatabaseManager
    GedcomParser --> DatabaseManager
    GeneWebApp --> GenealogyAlgorithms
    GeneWebApp --> TemplateEnvironment
```

### 2.2 Modèles de Données

```mermaid
erDiagram
    Person {
        int id PK
        string first_name
        string surname
        enum sex
        date birth_date
        date death_date
        int parent_family_id FK
        string occupation
        text notes
    }
    
    Family {
        int id PK
        int father_id FK
        int mother_id FK
        date marriage_date
        enum marriage_type
        date divorce_date
        enum divorce_type
        text notes
    }
    
    Event {
        int id PK
        int person_id FK
        enum event_type
        date event_date
        int place_id FK
        string description
        string source
    }
    
    Place {
        int id PK
        string town
        string county
        string state
        string country
        float latitude
        float longitude
    }
    
    Source {
        int id PK
        string title
        string author
        string publication
        date publication_date
        string url
        text notes
    }
    
    Person ||--o{ Event : "has events"
    Person }o--|| Family : "parent family"
    Person ||--o{ Family : "father/mother"
    Event }o--|| Place : "occurred at"
    Event }o--o{ Source : "documented by"
```

---

## 3. Flux de Données et Processing

### 3.1 Import GEDCOM Workflow

```mermaid
sequenceDiagram
    participant User as 👤 Utilisateur
    participant UI as 🌐 Interface Web
    participant API as 🔌 API FastAPI
    participant Parser as 📄 GEDCOM Parser
    participant DB as 💾 Database
    participant Validator as ✅ Validator
    
    User->>UI: Upload GEDCOM file
    UI->>API: POST /import/gedcom
    API->>Parser: parse_file(gedcom_content)
    Parser->>Parser: Parse GEDCOM structure
    Parser->>Validator: validate_data(persons, families)
    Validator-->>Parser: validation_result
    Parser->>DB: batch_insert(validated_data)
    DB-->>Parser: insert_results
    Parser-->>API: import_summary
    API-->>UI: JSON response
    UI-->>User: Display import results
```

### 3.2 Calcul de Consanguinité

```mermaid
flowchart TD
    A[👤 Person ID] --> B[🔍 Get Parents]
    B --> C{Parents Found?}
    C -->|No| D[🚫 Consanguinity = 0.0]
    C -->|Yes| E[🔍 Find Common Ancestors]
    E --> F{Common Ancestors?}
    F -->|No| D
    F -->|Yes| G[📏 Calculate Distances]
    G --> H[🧮 Wright's Formula]
    H --> I[🔄 For Each Path]
    I --> J[📊 Sum Contributions]
    J --> K[✅ Consanguinity Result]
    
    subgraph "Wright's Formula"
        H --> L["(1/2)^(n1 + n2 + 1)"]
        L --> M["× (1 + F_ancestor)"]
    end
```

### 3.3 Recherche et Navigation

```mermaid
stateDiagram-v2
    [*] --> SearchInput
    SearchInput --> Processing : Submit Query
    Processing --> DatabaseQuery : Parse & Validate
    DatabaseQuery --> ResultsFound : SQL Query
    DatabaseQuery --> NoResults : Empty Result
    ResultsFound --> DisplayResults : Format Results
    NoResults --> SuggestAlternatives : Fuzzy Search
    SuggestAlternatives --> DisplayResults : Show Suggestions
    DisplayResults --> PersonDetail : Select Person
    DisplayResults --> RefineSearch : New Search
    PersonDetail --> RelatedPersons : Navigation
    RelatedPersons --> PersonDetail : Select Related
    PersonDetail --> [*] : Close
    RefineSearch --> SearchInput : Update Criteria
```

---

## 4. Architecture de Test

### 4.1 Stratégie Multi-niveaux

```mermaid
graph TD
    subgraph "🌐 End-to-End Tests (5%)"
        E2E1[Playwright Browser Tests]
        E2E2[Full User Scenarios]
        E2E3[GEDCOM Import Workflow]
    end
    
    subgraph "🔗 Integration Tests (35%)"
        INT1[API Endpoint Tests]
        INT2[Database Integration Tests]
        INT3[GEDCOM Round-trip Tests]
        INT4[Template Rendering Tests]
        INT5[Algorithm Integration Tests]
    end
    
    subgraph "🧪 Unit Tests (60%)"
        UNIT1[Algorithm Unit Tests]
        UNIT2[Model Validation Tests]
        UNIT3[Utility Function Tests]
        UNIT4[Parser Unit Tests]
        UNIT5[Database Model Tests]
        UNIT6[Template Filter Tests]
    end
    
    E2E1 --> INT1
    E2E2 --> INT2
    E2E3 --> INT3
    
    INT1 --> UNIT1
    INT2 --> UNIT2
    INT3 --> UNIT4
    INT4 --> UNIT6
    INT5 --> UNIT1
    
    style E2E1 fill:#ff6b6b
    style E2E2 fill:#ff6b6b
    style E2E3 fill:#ff6b6b
    style INT1 fill:#4ecdc4
    style INT2 fill:#4ecdc4
    style INT3 fill:#4ecdc4
    style INT4 fill:#4ecdc4
    style INT5 fill:#4ecdc4
    style UNIT1 fill:#95e1d3
    style UNIT2 fill:#95e1d3
    style UNIT3 fill:#95e1d3
    style UNIT4 fill:#95e1d3
    style UNIT5 fill:#95e1d3
    style UNIT6 fill:#95e1d3
```

**Répartition des Tests :**
- 🧪 **Tests Unitaires (60%)** : 45+ tests isolés sur fonctions individuelles
- 🔗 **Tests d'Intégration (35%)** : 25+ tests sur interactions entre composants  
- 🌐 **Tests E2E (5%)** : 5+ tests sur workflows utilisateur complets

**Tests Actuellement Implémentés :**
```python
# Résultats réels des tests
test_results = {
    'unit_tests': '35 tests - Algorithmes, modèles, utilitaires', 
    'integration_tests': '15 tests - API, DB, GEDCOM',
    'e2e_tests': '5 tests - Workflows complets (skippés)',
    'total_coverage': '51% - Code critique couvert',
    'passing_rate': '74% - 55/74 tests passent'
}
```