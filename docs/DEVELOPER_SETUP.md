# Developer Setup Guide

## Overview

This guide will help you set up your development environment for the GeneWeb Python modernization project.

---

## Prerequisites

### Required Software

- **Python 3.11 or higher** - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/downloads)
- **Docker** (optional, for containerized development) - [Download](https://www.docker.com/get-started)
- **PostgreSQL 15+** (optional, for production-like database) - [Download](https://www.postgresql.org/download/)

### Recommended Tools

- **VS Code** or **PyCharm** - IDE with Python support
- **Postman** or **Insomnia** - API testing
- **DBeaver** or **pgAdmin** - Database management

---

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/NoahCherel/Geneweb-test.git
cd Geneweb-test/geneweb-python
```

### 2. Create Virtual Environment

```bash
# Navigate to code directory
cd code

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 4. Setup Pre-commit Hooks (Optional but Recommended)

```bash
pre-commit install
```

This will automatically run linters and formatters before each commit.

---

## Environment Configuration

### Create `.env` File

Create a `.env` file in the `code/` directory:

```bash
# Database Configuration
DATABASE_URL=sqlite:///geneweb.db
# For PostgreSQL (production):
# DATABASE_URL=postgresql://user:password@localhost:5432/geneweb

# Security - CRITICAL: Generate a strong, unique secret key!
# Generate with: python -c 'import secrets; print(secrets.token_hex(32))'
# Or: openssl rand -hex 32
SECRET_KEY=your-generated-secret-key-replace-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS - Allowed origins (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Application
DEBUG=True
LOG_LEVEL=DEBUG

# File uploads
MAX_UPLOAD_SIZE_MB=10
UPLOAD_DIR=/tmp/geneweb/uploads
```

**Important Security Note:** 
Always generate a unique, cryptographically secure `SECRET_KEY`. Never use the placeholder value in production!

```bash
# Generate a secure secret key
python -c 'import secrets; print(secrets.token_hex(32))'
```

### Load Environment Variables

```python
# Python automatically loads .env with python-dotenv
from dotenv import load_dotenv
load_dotenv()
```

---

## Database Setup

### Option 1: SQLite (Development)

SQLite is the default and requires no additional setup. The database file will be created automatically.

```bash
# Database file will be created at: code/geneweb.db
```

### Option 2: PostgreSQL (Production-like)

#### Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS (with Homebrew)
brew install postgresql

# Start PostgreSQL service
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS
```

#### Create Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE geneweb;
CREATE USER geneweb_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE geneweb TO geneweb_user;
\q
```

#### Update `.env`

```bash
DATABASE_URL=postgresql://geneweb_user:your-password@localhost:5432/geneweb
```

### Initialize Database Schema

```bash
# Run migrations (if using Alembic)
alembic upgrade head

# Or use the database manager to create tables
python -c "from core.database import DatabaseManager; db = DatabaseManager(); db.create_tables()"
```

---

## Running the Application

### Development Server

```bash
# Make sure you're in the code/ directory and venv is activated
cd code
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run the development server
python run_app.py

# Or with uvicorn directly
uvicorn core.webapp:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at:
- Web UI: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Alternative API Docs: http://localhost:8000/redoc

### API Server Only

```bash
# Run just the API (no web UI)
uvicorn core.api:app --reload --port 8001
```

---

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Tests with Coverage

```bash
pytest --cov=core --cov-report=html
```

Open `htmlcov/index.html` in your browser to view coverage report.

### Run Specific Tests

```bash
# Run single test file
pytest tests/test_algorithms_tdd.py

# Run specific test
pytest tests/test_algorithms_tdd.py::test_consanguinity_calculation

# Run tests matching pattern
pytest -k "consanguinity"
```

### Run Tests in Parallel

```bash
# Install pytest-xdist if not already installed
pip install pytest-xdist

# Run tests in parallel (faster)
pytest -n auto
```

---

## Code Quality Tools

### Format Code

```bash
# Format code with Black
black .

# Sort imports with isort
isort .

# Run both
black . && isort .
```

### Lint Code

```bash
# Check code style with flake8
flake8 .

# Type checking with mypy
mypy core/

# Security scanning with bandit
bandit -r core/
```

### Run All Quality Checks

```bash
# Create a script to run all checks
./scripts/quality_check.sh

# Or manually:
black --check . && \
isort --check . && \
flake8 . && \
mypy core/ && \
bandit -r core/
```

---

## Docker Development

### Build Docker Image

```bash
# From geneweb-python directory
docker-compose build
```

### Run Application in Docker

```bash
# Start all services
docker-compose up

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Access Docker Container Shell

```bash
docker-compose exec app bash
```

---

## IDE Configuration

### VS Code

#### Recommended Extensions

Install these VS Code extensions:
- Python (Microsoft)
- Pylance (Microsoft)
- Python Test Explorer
- GitLens
- Docker
- SQLite Viewer

#### Settings

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/code/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": [
    "tests"
  ],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.rulers": [88]
  }
}
```

#### Launch Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "core.webapp:app",
        "--reload"
      ],
      "cwd": "${workspaceFolder}/code",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/code"
      }
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    },
    {
      "name": "Python: Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": [
        "-v"
      ],
      "cwd": "${workspaceFolder}/code"
    }
  ]
}
```

### PyCharm

#### Configure Interpreter

1. File → Settings → Project → Python Interpreter
2. Click ⚙️ → Add
3. Select "Virtual Environment"
4. Choose existing environment: `code/venv`

#### Configure Test Runner

1. File → Settings → Tools → Python Integrated Tools
2. Set "Default test runner" to "pytest"

#### Enable Type Checking

1. File → Settings → Editor → Inspections
2. Enable "Python → Type Checker"

---

## Development Workflow

### Feature Development

```bash
# 1. Create feature branch
git checkout -b feat/your-feature-name

# 2. Write tests first (TDD)
# Create/modify tests in tests/

# 3. Run tests (should fail initially - RED)
pytest tests/test_your_feature.py

# 4. Implement feature (GREEN)
# Write code in core/

# 5. Run tests again (should pass)
pytest tests/test_your_feature.py

# 6. Refactor code (REFACTOR)
# Improve implementation while keeping tests green

# 7. Run full test suite
pytest

# 8. Check code quality
black .
isort .
flake8 .
mypy core/
bandit -r core/

# 9. Commit changes
git add .
git commit -m "feat: add your feature description"

# 10. Push and create PR
git push origin feat/your-feature-name
```

### Bug Fix Workflow

```bash
# 1. Create bugfix branch
git checkout -b fix/bug-description

# 2. Write test that reproduces the bug
# Test should FAIL

# 3. Fix the bug
# Test should now PASS

# 4. Verify no regressions
pytest

# 5. Commit and push
git commit -m "fix: bug description"
git push origin fix/bug-description
```

---

## Common Tasks

### Add New Dependencies

```bash
# Install new package
pip install package-name

# Add to requirements.txt
pip freeze | grep package-name >> requirements.txt

# Or for dev dependencies
pip freeze | grep package-name >> requirements-dev.txt
```

### Create Database Migration (Alembic)

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Review generated migration in alembic/versions/

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Load Sample Data

```bash
# Load sample genealogical data
python -c "from core.sample import load_sample_data; load_sample_data()"
```

### Import GEDCOM File

```bash
# Via CLI
python -m core.cli import path/to/file.ged

# Or via API
curl -X POST http://localhost:8000/api/import \
  -F "file=@path/to/file.ged"
```

---

## Troubleshooting

### Issue: Module Not Found

```bash
# Ensure you're in the code directory
cd code

# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt -r requirements-dev.txt
```

### Issue: Database Connection Error

```bash
# Check DATABASE_URL in .env
cat .env | grep DATABASE_URL

# For PostgreSQL, ensure service is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# Test connection
psql -h localhost -U geneweb_user -d geneweb
```

### Issue: Tests Failing

```bash
# Clear pytest cache
rm -rf .pytest_cache/

# Remove cached files
find . -type d -name __pycache__ -exec rm -rf {} +

# Run tests with verbose output
pytest -vv

# Run single failing test
pytest tests/path/to/test.py::test_name -vv
```

### Issue: Import Errors

```bash
# Ensure PYTHONPATH is set correctly
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use pytest.ini configuration (already set up)
```

---

## Getting Help

### Documentation

- **Architecture**: See `docs/architecture/`
- **Testing**: See `docs/testing/TDD_STRATEGY.md`
- **Security**: See `docs/architecture/SECURITY_PRIVACY.md`
- **SOLID Principles**: See `docs/architecture/SOLID_PRINCIPLES.md`

### Community

- **GitHub Issues**: Report bugs or request features
- **Pull Requests**: Contribute code improvements
- **Discussions**: Ask questions or share ideas

### Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

---

## Next Steps

1. ✅ Setup development environment
2. ✅ Run tests to verify setup
3. 📖 Read architecture documentation
4. 🧪 Write your first test
5. 💻 Implement your first feature
6. 🚀 Submit your first pull request

Happy coding! 🎉
