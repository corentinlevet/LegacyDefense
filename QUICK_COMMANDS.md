# 📋 Commandes Rapides - Test Coverage

## 🚀 Lancer les tests avec coverage

### Méthode la plus simple (recommandée)
```bash
./run_tests_with_coverage.sh
```

### Avec pytest directement
```bash
# Coverage basique
pytest --cov=src --cov=code

# Coverage avec détails des lignes manquantes
pytest --cov=src --cov=code --cov-report=term-missing

# Coverage avec rapport HTML
pytest --cov=src --cov=code --cov-report=html
xdg-open htmlcov/index.html
```

### Avec coverage.py directement
```bash
coverage run -m pytest tests/
coverage report
coverage html
```

## 🎯 Tests spécifiques

```bash
# Nouveaux tests uniquement
pytest tests/application/test_date_utils.py \
       tests/infrastructure/test_sql_repositories.py \
       tests/presentation/test_formatters_advanced.py -v

# Un seul fichier
pytest tests/application/test_date_utils.py -v

# Une seule classe de tests
pytest tests/application/test_date_utils.py::TestParseDateForSorting -v

# Un seul test
pytest tests/application/test_date_utils.py::TestParseDateForSorting::test_empty_date -v
```

## 📊 Voir les rapports

```bash
# Rapport rapide dans le terminal
coverage report

# Rapport détaillé avec lignes manquantes
coverage report --show-missing

# Rapport d'un fichier spécifique
coverage report --include="src/geneweb/application/services.py" --show-missing

# Ouvrir le rapport HTML
xdg-open htmlcov/index.html
# ou
firefox htmlcov/index.html
```

## 🧹 Nettoyage

```bash
# Supprimer les rapports de coverage
rm -rf htmlcov .coverage coverage.xml

# Supprimer les caches pytest
rm -rf .pytest_cache
find . -type d -name __pycache__ -exec rm -rf {} +
```

## 🔍 Vérifications utiles

```bash
# Vérifier que pytest est installé
pytest --version

# Vérifier que coverage est installé
coverage --version

# Lister tous les tests sans les exécuter
pytest --collect-only

# Exécuter les tests en mode verbose
pytest -v

# Exécuter les tests et s'arrêter au premier échec
pytest -x

# Exécuter les tests en mode verbose avec output complet
pytest -vv -s
```

## 📈 Objectifs de coverage

```bash
# Avec seuil minimum de 70%
pytest --cov=src --cov=code --cov-fail-under=70

# Avec seuil minimum de 80%
pytest --cov=src --cov=code --cov-fail-under=80
```

## 🎨 Formats de rapport

```bash
# Terminal uniquement
pytest --cov=src --cov-report=term

# Terminal avec lignes manquantes
pytest --cov=src --cov-report=term-missing

# HTML
pytest --cov=src --cov-report=html

# XML (pour CI/CD)
pytest --cov=src --cov-report=xml

# Tous en même temps
pytest --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml
```

## 💡 Tips

```bash
# Parallel execution (plus rapide)
pytest -n auto --cov=src

# Avec marqueurs
pytest -m "not slow" --cov=src

# Mode quiet
pytest -q --cov=src

# Avec timer pour voir les tests lents
pytest --durations=10 --cov=src
```

## 📝 Exemples de sortie

### Sortie Terminal
```
Name                                         Stmts   Miss  Cover   Missing
--------------------------------------------------------------------------
src/geneweb/application/services.py            245     45    82%   12-15, 45-67
src/geneweb/infrastructure/repositories.py      89     10    89%   23, 45-50
--------------------------------------------------------------------------
TOTAL                                         1523    234    85%
```

### Interprétation
- **Stmts** = Nombre total de lignes de code
- **Miss** = Lignes non couvertes par les tests
- **Cover** = Pourcentage de couverture
- **Missing** = Numéros des lignes non testées

## 🆘 En cas de problème

```bash
# Réinstaller les dépendances
pip install -r code/requirements-dev.txt

# Vérifier PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Lancer depuis la racine
cd /home/hgrisel/EPITECH/delivery2025-2026/Legacy/G-ING-900-PAR-9-1-legacy-1
pytest --cov=src
```

## 📚 Documentation

- Guide complet : `TESTING_COVERAGE_GUIDE.md`
- Nouveaux tests : `NOUVEAUX_TESTS.md`
- Configuration : `.coveragerc`
