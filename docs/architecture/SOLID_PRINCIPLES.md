# SOLID Principles Implementation Guide

## Overview

This document describes how the GeneWeb Python modernization project adheres to **SOLID principles** to ensure maintainability, testability, and extensibility.

---

## S - Single Responsibility Principle (SRP)

**Definition**: A class should have one, and only one, reason to change.

### Implementation in GeneWeb

#### ✅ Good Examples

1. **`models.py`** - Only defines data structures and their validation
   - Separate classes for `Person`, `Family`, `Event`, `Date`, `Place`
   - Each model class handles only its own data representation
   - No business logic mixed with data definitions

2. **`database.py`** - Only handles database operations
   - ORM models for persistence
   - DatabaseManager for connection management
   - No business logic or presentation concerns

3. **`algorithms.py`** - Only contains genealogical algorithms
   - Consanguinity calculations
   - Relationship detection
   - Ancestor/descendant searches
   - No database access (uses dependency injection)

4. **`gedcom.py`** - Only handles GEDCOM format operations
   - GedcomParser for import
   - GedcomExporter for export
   - Format conversion logic isolated

5. **`webapp.py`** - Only handles HTTP/web presentation
   - FastAPI route definitions
   - Request/response handling
   - Template rendering
   - Delegates business logic to other modules

#### ⚠️ Areas for Improvement

1. **`algorithms.py`** is large (1677 lines)
   - Should be split into:
     - `consanguinity.py` - Consanguinity calculations
     - `relationships.py` - Relationship detection
     - `ancestry.py` - Ancestor/descendant operations
     - `sosa.py` - Sosa numbering system

2. **`webapp.py`** mixes concerns
   - Route handlers should be thinner
   - Move complex logic to service layer
   - Create dedicated services: `PersonService`, `FamilyService`, etc.

---

## O - Open/Closed Principle (OCP)

**Definition**: Software entities should be open for extension but closed for modification.

### Implementation in GeneWeb

#### ✅ Good Examples

1. **Enum-based Event Types**
   ```python
   class EventType(Enum):
       BIRTH = "birth"
       DEATH = "death"
       # Can add new event types without modifying existing code
   ```

2. **Plugin-ready Template System**
   - Templates can be extended without modifying core template engine
   - Custom filters can be registered

3. **Database Abstraction**
   - SQLAlchemy ORM allows swapping database backends
   - Can extend to support multiple databases (PostgreSQL, MySQL, SQLite)

#### 🎯 Extension Points to Add

1. **Algorithm Strategy Pattern**
   ```python
   # Proposed refactoring
   class ConsanguinityCalculator(Protocol):
       def calculate(self, person_id: int) -> float: ...
   
   class WrightConsanguinityCalculator(ConsanguinityCalculator):
       # OCaml-equivalent algorithm
       pass
   
   class ModernConsanguinityCalculator(ConsanguinityCalculator):
       # Alternative algorithm
       pass
   ```

2. **Export Format Strategy**
   ```python
   # Proposed refactoring
   class Exporter(Protocol):
       def export(self, database: DatabaseManager) -> bytes: ...
   
   class GedcomExporter(Exporter): ...
   class JsonExporter(Exporter): ...
   class XmlExporter(Exporter): ...
   ```

---

## L - Liskov Substitution Principle (LSP)

**Definition**: Derived classes must be substitutable for their base classes.

### Implementation in GeneWeb

#### ✅ Good Examples

1. **Date Hierarchy**
   - All date types (with different calendars) behave consistently
   - Can substitute any Calendar type without breaking functionality

2. **Event Types**
   - All events share common interface
   - Specialized events (Birth, Death, Marriage) extend base behavior

#### 🎯 Areas to Strengthen

1. **Create explicit interfaces with Protocol**
   ```python
   from typing import Protocol
   
   class PersonRepository(Protocol):
       def get_by_id(self, person_id: int) -> Person: ...
       def save(self, person: Person) -> None: ...
       def delete(self, person_id: int) -> None: ...
   
   # SQLAlchemy implementation
   class SqlPersonRepository:
       def get_by_id(self, person_id: int) -> Person: ...
       # ... same interface
   
   # Can add MongoDB, Redis, etc. implementations
   ```

---

## I - Interface Segregation Principle (ISP)

**Definition**: Clients should not be forced to depend on interfaces they don't use.

### Implementation in GeneWeb

#### ✅ Good Examples

1. **Separated API Models**
   - `PersonAPI` for API serialization
   - `PersonORM` for database operations
   - `Person` for business logic
   - Each interface has only what it needs

2. **Focused Algorithm Methods**
   - `get_ancestors()` - only returns ancestors
   - `get_descendants()` - only returns descendants
   - `calculate_consanguinity()` - only calculates consanguinity
   - No monolithic "do everything" method

#### 🎯 Proposed Improvements

1. **Split DatabaseManager responsibilities**
   ```python
   # Instead of one large DatabaseManager, create focused interfaces:
   
   class PersonQuery(Protocol):
       def find_by_name(self, name: str) -> List[Person]: ...
       def find_by_id(self, id: int) -> Optional[Person]: ...
   
   class PersonCommand(Protocol):
       def create(self, person: Person) -> int: ...
       def update(self, person: Person) -> None: ...
       def delete(self, person_id: int) -> None: ...
   
   # CQRS pattern - separate reads from writes
   ```

---

## D - Dependency Inversion Principle (DIP)

**Definition**: Depend on abstractions, not on concretions.

### Implementation in GeneWeb

#### ✅ Good Examples

1. **GenealogyAlgorithms depends on abstraction**
   ```python
   class GenealogyAlgorithms:
       def __init__(self, db_manager: DatabaseManager):
           # Depends on DatabaseManager interface, not specific DB
   ```

2. **Template system decoupled**
   - Uses Jinja2 abstraction
   - Could swap template engine without changing business logic

#### ⚠️ Areas for Improvement

1. **Hardcoded database dependency**
   ```python
   # Current (tight coupling):
   db_manager = DatabaseManager("sqlite:///geneweb.db")
   
   # Proposed (dependency injection):
   class Application:
       def __init__(
           self,
           person_repo: PersonRepository,
           family_repo: FamilyRepository,
           algorithm_service: AlgorithmService
       ):
           self.person_repo = person_repo
           # ...
   
   # In main.py or dependency container:
   def create_app() -> Application:
       db_url = os.getenv("DATABASE_URL", "sqlite:///geneweb.db")
       db = DatabaseManager(db_url)
       
       return Application(
           person_repo=SqlPersonRepository(db),
           family_repo=SqlFamilyRepository(db),
           algorithm_service=GenealogyAlgorithms(db)
       )
   ```

2. **Add Repository Pattern**
   ```python
   from typing import Protocol, List, Optional
   
   class PersonRepository(Protocol):
       """Abstract repository for Person entities."""
       
       def find_by_id(self, person_id: int) -> Optional[Person]: ...
       def find_all(self) -> List[Person]: ...
       def save(self, person: Person) -> int: ...
       def delete(self, person_id: int) -> None: ...
       def find_by_name(self, name: str) -> List[Person]: ...
   
   class FamilyRepository(Protocol):
       """Abstract repository for Family entities."""
       # Similar interface
   
   # Then inject these into algorithms, API, webapp
   ```

---

## Clean Architecture Layers

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│  (webapp.py, api.py, cli.py)           │
│  - HTTP handlers                        │
│  - API endpoints                        │
│  - CLI commands                         │
└──────────────┬──────────────────────────┘
               │
               │ Depends on ↓
               │
┌──────────────▼──────────────────────────┐
│         Application Layer               │
│  (services/, use_cases/)                │
│  - Business workflows                   │
│  - Orchestration                        │
│  - Transaction management               │
└──────────────┬──────────────────────────┘
               │
               │ Depends on ↓
               │
┌──────────────▼──────────────────────────┐
│         Domain Layer                    │
│  (models.py, algorithms.py)            │
│  - Business entities                    │
│  - Business rules                       │
│  - Genealogical algorithms              │
└──────────────┬──────────────────────────┘
               │
               │ Depends on ↓
               │
┌──────────────▼──────────────────────────┐
│         Infrastructure Layer            │
│  (database.py, gedcom.py)              │
│  - Database access                      │
│  - External services                    │
│  - File I/O                             │
└─────────────────────────────────────────┘
```

---

## Refactoring Roadmap

### Phase 1: Extract Services (High Priority)
- [ ] Create `services/person_service.py`
- [ ] Create `services/family_service.py`
- [ ] Create `services/consanguinity_service.py`
- [ ] Move business logic from routes to services

### Phase 2: Implement Repository Pattern (High Priority)
- [ ] Define repository protocols in `core/protocols.py`
- [ ] Implement SQL repositories
- [ ] Inject repositories into services

### Phase 3: Split Large Modules (Medium Priority)
- [ ] Split `algorithms.py` into focused modules
- [ ] Extract algorithm strategies
- [ ] Create algorithm factory

### Phase 4: Add Dependency Injection (Medium Priority)
- [ ] Create DI container (e.g., using `dependency-injector`)
- [ ] Wire up dependencies in application startup
- [ ] Remove hardcoded dependencies

### Phase 5: Implement CQRS (Low Priority)
- [ ] Separate read models from write models
- [ ] Optimize queries independently
- [ ] Add event sourcing for audit trail

---

## Testing SOLID Compliance

### How to Verify SRP
```python
# Each class should have one clear responsibility
# Ask: "What is this class's single reason to change?"

class Person:
    # Reason to change: Business requirements for person data
    pass

class PersonRepository:
    # Reason to change: How persons are persisted
    pass

class PersonService:
    # Reason to change: Business workflows involving persons
    pass
```

### How to Verify OCP
```python
# New features should extend, not modify existing code
# Example: Adding a new export format

class Exporter(Protocol):
    def export(self, data) -> bytes: ...

# Add new format WITHOUT modifying existing exporters
class PdfExporter(Exporter):
    def export(self, data) -> bytes: ...
```

### How to Verify LSP
```python
# Subtypes must be usable through base type interface
def process_repository(repo: PersonRepository):
    # Should work with ANY PersonRepository implementation
    person = repo.find_by_id(1)
    # ...

# Both should work:
process_repository(SqlPersonRepository())
process_repository(MongoPersonRepository())
```

### How to Verify ISP
```python
# Clients should only see methods they need
# BAD: Giant interface
class DatabaseManager:
    def create_person(self): ...
    def create_family(self): ...
    def create_event(self): ...
    def find_person(self): ...
    def find_family(self): ...
    # ... 50 more methods

# GOOD: Focused interfaces
class PersonOperations(Protocol):
    def create(self): ...
    def find(self): ...

class FamilyOperations(Protocol):
    def create(self): ...
    def find(self): ...
```

### How to Verify DIP
```python
# High-level modules should not depend on low-level modules
# Both should depend on abstractions

# BAD:
class PersonService:
    def __init__(self):
        self.db = SQLDatabase()  # Depends on concrete class

# GOOD:
class PersonService:
    def __init__(self, repo: PersonRepository):  # Depends on abstraction
        self.repo = repo
```

---

## Code Review Checklist

When reviewing code, check:

- [ ] **SRP**: Does each class have a single, clear responsibility?
- [ ] **OCP**: Can this be extended without modifying existing code?
- [ ] **LSP**: Are all implementations truly interchangeable?
- [ ] **ISP**: Are interfaces focused and minimal?
- [ ] **DIP**: Do we depend on abstractions, not concretions?
- [ ] **Clean Architecture**: Are layer boundaries respected?
- [ ] **Type Hints**: Are all public APIs fully typed?
- [ ] **Docstrings**: Is every public class/method documented?
- [ ] **Tests**: Does test coverage meet 90% threshold?

---

## References

- [SOLID Principles - Uncle Bob](https://blog.cleancoder.com/uncle-bob/2020/10/18/Solid-Relevance.html)
- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Python Type Hints - PEP 484](https://www.python.org/dev/peps/pep-0484/)
- [Protocol Classes - PEP 544](https://www.python.org/dev/peps/pep-0544/)
