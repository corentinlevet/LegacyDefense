.PHONY: help install lint lint-check format security test all

# Default target
help:
	@echo "Available targets:"
	@echo "  install       Install dev dependencies"
	@echo "  lint          Run linters (flake8, black --check, isort --check)"
	@echo "  lint-fix      Run formatters to auto-fix issues (black, isort)"
	@echo "  format        Alias for lint-fix"
	@echo "  security      Run bandit security scan"
	@echo "  test          Run tests with coverage"
	@echo "  all           Run lint + security + test"

install:
	pip install -r requirements-dev.txt

lint:
	flake8 src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/

lint-fix:
	black src/ tests/
	isort src/ tests/

format: lint-fix

security:
	bandit -c pyproject.toml -r src/

test:
	python -m pytest tests/ --cov=src/geneweb --cov-report=term --cov-report=html -q

all: lint security test
