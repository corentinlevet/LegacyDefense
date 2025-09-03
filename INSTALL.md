# 🛠️ Installation Guide — Legacy

This document explains how to set up a development environment for the **Legacy** project.  
You have two options:

- **Option 1**: use **Docker** (recommended for consistency across all systems).
- **Option 2**: use a **Python virtual environment (venv)** locally.

---

## Option 1 — Docker 🐳

### Requirements
- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose plugin

### Build the container
```bash
docker compose build
```

### Start an interactive shell inside the container
```bash
docker compose run --rm app bash
```

Once inside the container:
```bash
pytest               # run tests
black .              # auto-format code
flake8 .             # lint check
```

---

## Option 2 — Local venv 🐍

### Requirements
- Python 3.11+ (3.13 supported)
- pip

### 1. Create a virtual environment

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate
```

**Linux/MacOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

👉 You should now see `(.venv)` in your terminal prompt.

### 2. Install dependencies
```bash
pip install -r code/requirements.txt
pip install -r code/requirements-dev.txt
```

### 3. Verify installation
```bash
pytest
black --check .
flake8 .
```

---

## Pre-commit hooks ⚡

We use **pre-commit** to automatically run linters and formatters on commit.

### Install hooks
```bash
pre-commit install
```

### Run on all files (first time)
```bash
pre-commit run --all-files
```

From now on, Black/Isort/Flake8 will be executed automatically when you commit.
