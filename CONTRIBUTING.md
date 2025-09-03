# CONTRIBUTING

This guide defines the rules and best practices for collaboration on this repository.

> ℹ️ These guidelines apply as a **team convention** (no direct pushes to `main`).

---

## 🌿 Git workflow

- Stable branch: **`main`**.
- Integration branch: **`dev`** (receives feature PRs).
- Feature branches: **`feat/<name>`** (e.g. `feat/api-import-gedcom`).
- Urgent bugfix branches: **`hotfix/<description>`**.

### Branch naming
- `feat/<short-topic>`
- `fix/<bug-id-or-topic>`
- `docs/<section>`

---

## 🔀 Pull Requests (PRs)

1. Create your branch from `dev` (or from `main` for a hotfix).
2. Commit often, push regularly.
3. Open a **PR into `dev`** (or into `main` for hotfix).
4. Requirements before merge:
   - ✅ **Tests** pass (`pytest`).
   - ✅ **Lint/format** OK (`black`, `flake8`, `isort`).
   - ✅ **CI** is green (GitHub Actions).
   - ✅ **1 approval** (peer).

---

## 📝 Commit rules (Conventional Commits)

- `feat: ...` → new feature
- `fix: ...` → bug fix
- `docs: ...` → documentation
- `test: ...` → add/modify tests
- `refactor: ...` → refactor without behavior change
- `perf: ...` → performance improvement

Examples:
```
feat: add Sosa calculation in core/sosa.py
fix: correct GEDCOM export for incomplete dates
docs: clarify installation guide on Windows
```

---

## 🧪 Tests

- Framework: **pytest** (+ `pytest-cov`).
- Coverage target: **≥ 80%**.
- Useful commands:
```bash
pytest
pytest --cov=. --cov-report=term-missing
```

Expected test levels:
- **Unit tests** (functions/domain logic).
- **Integration tests** (API/CLI with sample data).
- **End-to-end** (launch API locally and check key routes).

---

## 🧹 Code quality

- Style: **PEP8**
- Tools:
```bash
black .
isort .
flake8 .
mypy .
```
- No lint/warning before merge.

---

## 📚 Documentation

- **Docstrings** (Google or NumPy style) for all public APIs.
- Update the **README** if interfaces change.
- Add guides in `docs/` (architecture, deployment, test policy).

---

## 🔒 Security & GDPR

- Genealogical data is **sensitive**.
- Never commit or publish real personal data.
- Provide **anonymization** of living individuals in exports.
- Secrets/credentials only via environment variables (never committed).

---

Thanks for your contributions 🙌
