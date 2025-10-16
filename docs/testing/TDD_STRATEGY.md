# Testing Strategy & TDD Guide

## Overview

This document outlines the testing strategy for the GeneWeb Python modernization project, following **Test-Driven Development (TDD)** principles and aiming for **≥90% code coverage** on critical modules.

---

## Testing Philosophy

### Core Principles

1. **Test First, Code Second** - Write tests before implementation
2. **Red-Green-Refactor** - Follow TDD cycle rigorously
3. **Fast Feedback** - Tests should run quickly
4. **Isolated Tests** - Each test is independent
5. **Readable Tests** - Tests serve as documentation

### Coverage Goals

| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| `models.py` | 88% | 95% | High |
| `database.py` | 78% | 90% | High |
| `algorithms.py` | 59% | 95% | **Critical** |
| `gedcom.py` | 80% | 90% | High |
| `templates.py` | 49% | 90% | Medium |
| `webapp.py` | 0% | 85% | **Critical** |
| `api.py` | 0% | 85% | **Critical** |
| `cli.py` | 0% | 80% | Medium |

**Overall Target: ≥90% coverage on critical modules**

---

## Test Pyramid

```
        /\
       /  \
      / E2E \          10% - End-to-End Tests
     /______\
    /        \
   /Integration\       30% - Integration Tests
  /____________\
 /              \
/  Unit Tests   \      60% - Unit Tests
/________________\
```

### Unit Tests (60%)
- Test individual functions/methods
- Mock external dependencies
- Fast execution (<1s per test)
- Cover edge cases and error handling

### Integration Tests (30%)
- Test module interactions
- Use test database
- Verify data flow between components
- Test API endpoints with real DB

### End-to-End Tests (10%)
- Full user workflows
- Browser automation (if applicable)
- Complete system validation
- Slowest, most fragile

---

## TDD Workflow

### Red-Green-Refactor Cycle

```python
# Step 1: RED - Write failing test
def test_calculate_consanguinity_for_siblings():
    """Test that siblings have consanguinity from common parents."""
    # Setup
    db = create_test_database()
    algo = GenealogyAlgorithms(db)
    
    # Create test family
    parent1_id = create_test_person(db, "Parent1")
    parent2_id = create_test_person(db, "Parent2")
    child1_id = create_test_person(db, "Child1")
    child2_id = create_test_person(db, "Child2")
    create_family(db, parent1_id, parent2_id, [child1_id, child2_id])
    
    # Expected: siblings should have some consanguinity from parents
    result = algo.calculate_consanguinity(child1_id)
    
    # This test FAILS initially (RED)
    assert result.consanguinity > 0.0

# Step 2: GREEN - Write minimal code to pass
class GenealogyAlgorithms:
    def calculate_consanguinity(self, person_id: int) -> ConsanguinityResult:
        # Minimal implementation to make test pass
        # (Will be improved in refactor step)
        return ConsanguinityResult(
            person_id=person_id,
            consanguinity=0.125,  # Placeholder
            relationship_paths=[],
            common_ancestors=set()
        )

# Step 3: REFACTOR - Improve implementation
class GenealogyAlgorithms:
    def calculate_consanguinity(self, person_id: int) -> ConsanguinityResult:
        """
        Calculate Wright's coefficient of consanguinity.
        
        Based on the OCaml implementation in lib/consang.ml
        """
        # Proper algorithm implementation
        common_ancestors = self._find_common_ancestors(person_id)
        paths = self._calculate_paths_to_ancestors(person_id, common_ancestors)
        coefficient = self._compute_wright_coefficient(paths)
        
        return ConsanguinityResult(
            person_id=person_id,
            consanguinity=coefficient,
            relationship_paths=paths,
            common_ancestors=common_ancestors
        )
```

---

## Test Organization

### Directory Structure

```
tests/
├── unit/
│   ├── test_models.py           # Unit tests for data models
│   ├── test_algorithms.py       # Algorithm unit tests
│   ├── test_database.py         # Database layer tests
│   └── test_gedcom.py           # GEDCOM parser tests
├── integration/
│   ├── test_api_integration.py  # API endpoint integration
│   ├── test_database_integration.py  # DB operations
│   └── test_gedcom_roundtrip.py # GEDCOM import/export
├── e2e/
│   ├── test_webapp_e2e.py       # End-to-end webapp tests
│   └── test_user_workflows.py   # Complete user scenarios
├── fixtures/
│   ├── sample_data.py           # Test data generators
│   └── gedcom_samples/          # Sample GEDCOM files
└── conftest.py                  # Pytest configuration and fixtures
```

---

## Writing Effective Tests

### Test Naming Convention

```python
# Pattern: test_<what>_<when>_<expected>

def test_consanguinity_with_no_common_ancestors_returns_zero():
    """Consanguinity should be 0 when no common ancestors exist."""
    pass

def test_person_creation_with_invalid_birth_date_raises_validation_error():
    """Creating person with invalid birth date should raise ValidationError."""
    pass

def test_gedcom_import_with_utf8_encoding_preserves_special_characters():
    """GEDCOM import should correctly handle UTF-8 special characters."""
    pass
```

### Arrange-Act-Assert (AAA) Pattern

```python
def test_find_ancestors_returns_all_generations():
    # ARRANGE - Setup test data
    db = create_test_database()
    algo = GenealogyAlgorithms(db)
    grandparent_id = create_test_person(db, "Grandparent")
    parent_id = create_test_person(db, "Parent")
    child_id = create_test_person(db, "Child")
    create_family(db, grandparent_id, None, [parent_id])
    create_family(db, parent_id, None, [child_id])
    
    # ACT - Execute the code under test
    ancestors = algo.get_ancestors(child_id)
    
    # ASSERT - Verify expected outcomes
    assert len(ancestors) == 2
    assert parent_id in ancestors
    assert grandparent_id in ancestors
```

### Test Fixtures

```python
# conftest.py
import pytest
from core.database import DatabaseManager, PersonORM

@pytest.fixture
def test_db():
    """Create a clean test database for each test."""
    db = DatabaseManager("sqlite:///:memory:")
    db.create_tables()
    yield db
    # Cleanup happens automatically with in-memory DB

@pytest.fixture
def sample_person(test_db):
    """Create a sample person for testing."""
    person = PersonORM(
        first_name="John",
        surname="Doe",
        sex=Sex.MALE
    )
    session = test_db.get_session()
    session.add(person)
    session.commit()
    yield person
    session.close()

@pytest.fixture
def sample_family(test_db, sample_person):
    """Create a sample family structure."""
    # Create parents and children
    # ... implementation
    yield family
```

---

## Testing Strategies by Module

### Testing Models (`models.py`)

```python
class TestPersonModel:
    """Unit tests for Person model."""
    
    def test_person_creation_with_valid_data(self):
        """Person should be created with valid data."""
        person = Person(
            id=1,
            name=Name(first_name="John", surname="Doe"),
            sex=Sex.MALE
        )
        assert person.id == 1
        assert person.name.first_name == "John"
    
    def test_person_age_calculation(self):
        """Age calculation should be accurate."""
        birth = Date(day=1, month=1, year=1990)
        person = Person(id=1, name=Name("Test", "User"), sex=Sex.MALE)
        # Test age calculation logic
        # ...
    
    def test_person_serialization_to_api_model(self):
        """Person should serialize correctly to API model."""
        person = Person(...)
        api_model = PersonAPI.from_orm(person)
        assert api_model.first_name == person.name.first_name
```

### Testing Algorithms (`algorithms.py`)

```python
class TestConsanguinityCalculation:
    """Test consanguinity calculation against OCaml reference."""
    
    def test_consanguinity_for_unrelated_persons(self, test_db):
        """Unrelated persons should have consanguinity of 0."""
        algo = GenealogyAlgorithms(test_db)
        person_id = create_isolated_person(test_db)
        result = algo.calculate_consanguinity(person_id)
        assert result.consanguinity == 0.0
    
    def test_consanguinity_for_first_cousins(self, test_db):
        """First cousins should have consanguinity of 1/16."""
        # Setup family tree with first cousins
        cousin1_id, cousin2_id = create_first_cousin_pair(test_db)
        
        algo = GenealogyAlgorithms(test_db)
        result = algo.calculate_consanguinity(cousin1_id)
        
        # Wright's coefficient for first cousins = 1/16 = 0.0625
        assert abs(result.consanguinity - 0.0625) < 1e-6
    
    @pytest.mark.parametrize("relationship,expected_coefficient", [
        ("siblings", 0.25),
        ("half_siblings", 0.125),
        ("first_cousins", 0.0625),
        ("second_cousins", 0.015625),
    ])
    def test_consanguinity_coefficients(
        self, test_db, relationship, expected_coefficient
    ):
        """Test various relationship consanguinity coefficients."""
        person_id = create_relationship_pair(test_db, relationship)
        algo = GenealogyAlgorithms(test_db)
        result = algo.calculate_consanguinity(person_id)
        assert abs(result.consanguinity - expected_coefficient) < 1e-6
```

### Testing Database Layer (`database.py`)

```python
class TestDatabaseOperations:
    """Test database CRUD operations."""
    
    def test_create_person(self, test_db):
        """Person should be created and retrievable."""
        session = test_db.get_session()
        person = PersonORM(first_name="Jane", surname="Smith")
        session.add(person)
        session.commit()
        
        retrieved = session.query(PersonORM).filter_by(
            first_name="Jane"
        ).first()
        assert retrieved is not None
        assert retrieved.surname == "Smith"
    
    def test_cascade_delete_family(self, test_db):
        """Deleting family should handle children correctly."""
        # Test cascading deletes and constraints
        # ...
    
    def test_database_transaction_rollback(self, test_db):
        """Failed transaction should rollback properly."""
        session = test_db.get_session()
        try:
            person = PersonORM(first_name="Test")
            session.add(person)
            # Cause an error
            raise Exception("Simulated error")
        except Exception:
            session.rollback()
        
        # Verify nothing was committed
        count = session.query(PersonORM).count()
        assert count == 0
```

### Testing GEDCOM Parser (`gedcom.py`)

```python
class TestGedcomParser:
    """Test GEDCOM import functionality."""
    
    def test_parse_minimal_gedcom(self, tmp_path):
        """Parser should handle minimal valid GEDCOM."""
        gedcom_content = """
        0 HEAD
        1 GEDC
        2 VERS 5.5.1
        0 @I1@ INDI
        1 NAME John /Doe/
        0 TRLR
        """
        gedcom_file = tmp_path / "minimal.ged"
        gedcom_file.write_text(gedcom_content)
        
        parser = GedcomParser()
        database = parser.parse(str(gedcom_file))
        
        assert len(database.persons) == 1
        person = database.persons["@I1@"]
        assert person.name.first_name == "John"
        assert person.name.surname == "Doe"
    
    def test_gedcom_roundtrip_preserves_data(self, tmp_path, sample_database):
        """Export and re-import should preserve all data."""
        # Export database to GEDCOM
        exporter = GedcomExporter()
        gedcom_path = tmp_path / "export.ged"
        exporter.export(sample_database, str(gedcom_path))
        
        # Re-import
        parser = GedcomParser()
        reimported = parser.parse(str(gedcom_path))
        
        # Verify data preservation
        assert len(reimported.persons) == len(sample_database.persons)
        # More detailed checks...
    
    def test_gedcom_utf8_encoding(self, tmp_path):
        """Parser should handle UTF-8 encoded names."""
        gedcom_content = """
        0 HEAD
        1 CHAR UTF-8
        0 @I1@ INDI
        1 NAME François /Müller/
        0 TRLR
        """
        # Test UTF-8 handling...
```

### Testing API Endpoints (`api.py`)

```python
from fastapi.testclient import TestClient

class TestPersonAPI:
    """Test Person API endpoints."""
    
    def test_get_person_returns_200(self, test_client, sample_person):
        """GET /api/persons/{id} should return person data."""
        response = test_client.get(f"/api/persons/{sample_person.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == sample_person.first_name
    
    def test_create_person_with_valid_data(self, test_client):
        """POST /api/persons should create new person."""
        person_data = {
            "first_name": "Alice",
            "surname": "Johnson",
            "sex": "female"
        }
        response = test_client.post("/api/persons", json=person_data)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
    
    def test_create_person_with_invalid_data_returns_422(self, test_client):
        """POST with invalid data should return validation error."""
        invalid_data = {
            "first_name": "",  # Invalid: empty name
            "sex": "invalid"   # Invalid: not a valid Sex enum
        }
        response = test_client.post("/api/persons", json=invalid_data)
        assert response.status_code == 422
    
    def test_authentication_required(self, test_client):
        """Protected endpoints should require authentication."""
        response = test_client.delete("/api/persons/1")
        assert response.status_code == 401
```

### Testing Web Application (`webapp.py`)

```python
class TestWebAppRoutes:
    """Test web application routes."""
    
    def test_home_page_loads(self, test_client):
        """Home page should load successfully."""
        response = test_client.get("/")
        assert response.status_code == 200
        assert b"GeneWeb" in response.content
    
    def test_person_detail_page(self, test_client, sample_person):
        """Person detail page should display person data."""
        response = test_client.get(f"/person/{sample_person.id}")
        assert response.status_code == 200
        assert sample_person.first_name.encode() in response.content
    
    def test_search_functionality(self, test_client, sample_database):
        """Search should find persons by name."""
        response = test_client.get("/search?q=Doe")
        assert response.status_code == 200
        # Verify search results in response
```

---

## Mocking and Test Doubles

### When to Mock

✅ **DO mock:**
- External services (APIs, file systems)
- Slow operations (network calls)
- Non-deterministic behavior (random, time)
- Complex dependencies in unit tests

❌ **DON'T mock:**
- Simple value objects
- Data models
- Your own code in integration tests
- Database in integration tests (use test DB)

### Mock Examples

```python
from unittest.mock import Mock, patch, MagicMock

def test_gedcom_import_handles_file_error():
    """Parser should handle file read errors gracefully."""
    with patch('builtins.open', side_effect=IOError("File not found")):
        parser = GedcomParser()
        with pytest.raises(FileNotFoundError):
            parser.parse("nonexistent.ged")

def test_external_api_call():
    """Test code that calls external API."""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {"result": "success"}
        # Test code that uses requests.get
```

---

## Performance Testing

### Benchmark Critical Operations

```python
import pytest
import time

@pytest.mark.slow
def test_consanguinity_calculation_performance(large_database):
    """Consanguinity calculation should complete within time limit."""
    algo = GenealogyAlgorithms(large_database)
    
    start = time.time()
    result = algo.calculate_consanguinity(person_id=1000)
    duration = time.time() - start
    
    # Should complete in less than 1 second
    assert duration < 1.0

@pytest.mark.parametrize("num_persons", [100, 1000, 10000])
def test_search_scales_linearly(num_persons):
    """Search performance should scale linearly with database size."""
    # Create database with num_persons
    # Measure search time
    # Assert time is proportional to size
```

---

## Regression Testing

### Ensure Compatibility with OCaml

```python
class TestOCamlCompatibility:
    """Verify functional equivalence with OCaml implementation."""
    
    def test_consanguinity_matches_ocaml_reference(self):
        """Python consanguinity should match OCaml output."""
        # Load reference test case from OCaml test suite
        reference_data = load_ocaml_test_case("consanguinity_test_1.json")
        
        # Run Python implementation
        db = create_database_from_reference(reference_data)
        algo = GenealogyAlgorithms(db)
        result = algo.calculate_consanguinity(reference_data["person_id"])
        
        # Compare with OCaml output
        assert abs(result.consanguinity - reference_data["expected"]) < 1e-10
    
    def test_gedcom_export_matches_ocaml_format(self):
        """GEDCOM export should match OCaml version format."""
        # Compare output byte-by-byte
        # (allowing for acceptable differences like timestamps)
```

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linters
      run: |
        black --check .
        isort --check .
        flake8 .
        mypy .
    
    - name: Run security scan
      run: bandit -r core/
    
    - name: Run tests with coverage
      run: |
        pytest --cov=core --cov-report=xml --cov-report=term-missing
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
    
    - name: Check coverage threshold
      run: |
        coverage report --fail-under=90
```

---

## Test Commands

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov-report=html

# Run specific test file
pytest tests/unit/test_algorithms.py

# Run specific test
pytest tests/unit/test_algorithms.py::test_consanguinity_calculation

# Run tests matching pattern
pytest -k "consanguinity"

# Run with verbose output
pytest -v

# Run in parallel (faster)
pytest -n auto

# Run only failed tests from last run
pytest --lf

# Show print statements
pytest -s
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=core --cov-report=html
open htmlcov/index.html

# Show missing lines
pytest --cov=core --cov-report=term-missing

# Generate XML for CI
pytest --cov=core --cov-report=xml
```

---

## Quality Metrics

### Test Quality Indicators

✅ **Good Tests:**
- Fast (<100ms per unit test)
- Isolated (no test interdependencies)
- Repeatable (same result every time)
- Descriptive names
- Clear failure messages

❌ **Test Smells:**
- Slow tests (>1s for unit test)
- Flaky tests (intermittent failures)
- Unclear test names
- Testing implementation details
- Too many mocks

### Coverage Goals

- **Critical modules (algorithms, database, gedcom)**: ≥95%
- **API/Web layer**: ≥85%
- **Utilities**: ≥80%
- **Overall project**: ≥90%

---

## References

- [Test-Driven Development - Kent Beck](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530)
- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [The Testing Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
