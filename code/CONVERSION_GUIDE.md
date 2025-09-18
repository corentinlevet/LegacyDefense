# GeneWeb Python Implementation Guide

## Overview

This document provides a complete guide for converting the main features of GeneWeb from OCaml to Python. The implementation includes all core functionality with modern Python tools and practices.

## Architecture Overview

The Python implementation is structured as follows:

```
geneweb-python/
├── code/
│   ├── core/
│   │   ├── models.py          # Data models (Person, Family, Event, etc.)
│   │   ├── database.py        # SQLAlchemy ORM and database operations
│   │   ├── gedcom.py          # GEDCOM import/export functionality
│   │   ├── api.py             # FastAPI REST API
│   │   ├── templates.py       # Jinja2 template system
│   │   ├── cli.py             # Command-line tools
│   │   └── algorithms.py      # Genealogical algorithms
│   ├── tests/
│   │   └── test_geneweb.py    # Comprehensive test suite
│   ├── requirements.txt       # Production dependencies
│   └── requirements-dev.txt   # Development dependencies
```

## Key Components Conversion

### 1. Data Models (`models.py`)

**Original (OCaml)**: Complex variant types and records
**Python**: Dataclasses with enums and type hints

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

class Sex(Enum):
    MALE = "male"
    FEMALE = "female"
    NEUTER = "neuter"

@dataclass
class Person:
    id: int
    name: Name
    sex: Sex = Sex.NEUTER
    birth: Optional[Event] = None
    death: Optional[Event] = None
    # ... additional fields
```

### 2. Database Layer (`database.py`)

**Original (OCaml)**: Custom binary format with manual indexing
**Python**: SQLAlchemy ORM with PostgreSQL/SQLite support

```python
from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PersonORM(Base):
    __tablename__ = 'persons'
    
    id = Column(Integer, primary_key=True)
    first_name = Column(String(255), nullable=False)
    surname = Column(String(255), nullable=False)
    sex = Column(Enum(Sex), default=Sex.NEUTER)
    # ... relationships and indexes
```

### 3. Web Interface (`api.py`)

**Original (OCaml)**: Custom HTTP daemon (gwd)
**Python**: FastAPI with automatic OpenAPI documentation

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

app = FastAPI(title="GeneWeb API", version="1.0.0")

@app.get("/persons/{person_id}")
async def get_person(person_id: int, db: Session = Depends(get_db)):
    person = db.query(PersonORM).filter(PersonORM.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person
```

### 4. Template System (`templates.py`)

**Original (OCaml)**: Jingoo templates
**Python**: Jinja2 with custom filters and internationalization

```python
from jinja2 import Environment, FileSystemLoader

class TemplateEnvironment:
    def __init__(self, template_dir: str = "templates"):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self._register_filters()
    
    @self.env.filter('person_name')
    def person_name(person: Person, format_type: str = "full") -> str:
        if format_type == "surname_first":
            return f"{person.name.surname}, {person.name.first_name}"
        return f"{person.name.first_name} {person.name.surname}"
```

### 5. Command-Line Tools (`cli.py`)

**Original (OCaml)**: Multiple separate binaries (gwc, ged2gwb, etc.)
**Python**: Single CLI with subcommands using Click

```python
import click
from .gedcom import GedcomParser

@click.group()
def cli():
    """GeneWeb Python command-line tools."""
    pass

@cli.command()
@click.argument('gedcom_file', type=click.Path(exists=True))
def import_gedcom(gedcom_file):
    """Import GEDCOM file into database."""
    parser = GedcomParser()
    persons, families = parser.parse_file(gedcom_file)
    # ... import logic
```

### 6. GEDCOM Support (`gedcom.py`)

**Original (OCaml)**: Custom GEDCOM parser
**Python**: Full GEDCOM 5.5.1 parser with validation

```python
class GedcomParser:
    def parse_file(self, file_path: str) -> Tuple[Dict[int, Person], Dict[int, Family]]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        records = self._parse_gedcom_content(content)
        # ... parsing logic
        return persons, families
```

### 7. Genealogical Algorithms (`algorithms.py`)

**Original (OCaml)**: Consanguinity calculation, relationship analysis
**Python**: Modern algorithms with caching and optimization

```python
class GenealogyAlgorithms:
    def calculate_consanguinity(self, session, person_id: int) -> ConsanguinityResult:
        """Calculate consanguinity coefficient for a person."""
        # Wright's coefficient of inbreeding algorithm
        # F = Σ (1/2)^(n1 + n2 + 1) * (1 + F_ancestor)
        # ... implementation
```

## Installation and Setup

### 1. Create Python Environment

```bash
# Using uv (recommended)
uv venv
uv activate
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt

# Or using pip
python -m venv geneweb-env
source geneweb-env/bin/activate  # On Windows: geneweb-env\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Initialize Database

```python
from core.database import DatabaseManager

# Create database
db_manager = DatabaseManager("sqlite:///geneweb.db")
db_manager.create_tables()
```

### 3. Import GEDCOM Data

```bash
# Using CLI
python -m core.cli import-gedcom family.ged

# Or programmatically
from core.gedcom import GedcomParser
parser = GedcomParser()
persons, families = parser.parse_file("family.ged")
```

### 4. Start Web Server

```bash
# Development server
python -m core.api

# Production server
uvicorn core.api:app --host 0.0.0.0 --port 8000
```

## Key Features Comparison

| Feature | Original OCaml | Python Implementation |
|---------|---------------|----------------------|
| **Data Storage** | Binary format | SQLite/PostgreSQL |
| **Web Interface** | Custom HTTP daemon | FastAPI with OpenAPI |
| **Templates** | Jingoo | Jinja2 |
| **I18N** | Custom system | JSON-based translations |
| **CLI Tools** | Multiple binaries | Single CLI with subcommands |
| **Testing** | Limited | Comprehensive pytest suite |
| **Documentation** | Manual | Auto-generated API docs |
| **Deployment** | Manual setup | Docker + CI/CD ready |

## Performance Considerations

### Database Optimization
- **Indexes**: Automatic indexing on names, dates, relationships
- **Query Optimization**: SQLAlchemy query optimization
- **Caching**: Redis/Memcached integration ready

### Algorithm Optimization
- **Consanguinity**: Cached ancestor calculations
- **Search**: Full-text search with PostgreSQL
- **Relationships**: Graph algorithms for large family trees

## Migration Strategy

### Phase 1: Data Migration
1. **Export** existing GeneWeb data to GEDCOM format
2. **Import** GEDCOM files into Python implementation
3. **Validate** data integrity and relationships

### Phase 2: Feature Parity
1. **Web Interface**: Replicate all original web pages
2. **CLI Tools**: Ensure all command-line functionality works
3. **Templates**: Port existing template designs

### Phase 3: Enhanced Features
1. **REST API**: Modern API for mobile/web apps
2. **Performance**: Optimize for large databases
3. **Security**: Modern authentication and authorization

## Testing Strategy

### Unit Tests
```python
def test_person_creation():
    person = Person(id=1, name=Name(first_name="John", surname="Doe"))
    assert person.name.first_name == "John"

def test_consanguinity_calculation():
    algorithms = GenealogyAlgorithms(db_manager)
    result = algorithms.calculate_consanguinity(session, person_id)
    assert result.consanguinity >= 0.0
```

### Integration Tests
- GEDCOM import/export workflows
- API endpoint testing with real data
- Database migration testing

### Performance Tests
- Large database operations (>100k persons)
- Consanguinity calculation benchmarks
- Search performance with complex queries

## Deployment Options

### Docker Deployment
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY code/ /app/
WORKDIR /app
CMD ["uvicorn", "core.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Traditional Deployment
- **Web Server**: Nginx + Gunicorn/Uvicorn
- **Database**: PostgreSQL with backups
- **Monitoring**: Prometheus + Grafana

## Development Workflow

### Code Quality
```bash
# Formatting
black code/
isort code/

# Linting
flake8 code/
mypy code/

# Testing
pytest code/tests/ --cov=core --cov-report=html
```

### Git Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    hooks:
      - id: isort
```

## Conclusion

This Python implementation provides a complete modernization of GeneWeb with:

1. **Modern Architecture**: Clean separation of concerns
2. **Better Performance**: Optimized database and algorithms
3. **Enhanced Security**: Modern authentication and validation
4. **Improved Testing**: Comprehensive test coverage
5. **Easy Deployment**: Docker and cloud-ready
6. **API-First**: REST API for modern integrations
7. **Developer Experience**: Type hints, auto-completion, debugging

The conversion maintains all core genealogical functionality while providing a foundation for future enhancements and integrations.