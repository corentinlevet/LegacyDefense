# Guide de Test Coverage

Ce guide explique comment utiliser le coverage de tests pour mesurer la couverture de code.

## 📦 Installation des dépendances

Si ce n'est pas déjà fait, installez les dépendances de test :

```bash
pip install -r code/requirements-dev.txt
```

Ou installez uniquement les packages de coverage :

```bash
pip install pytest pytest-cov coverage
```

## 🧪 Lancer les tests avec coverage

### Option 1 : Avec pytest (recommandé)

```bash
# Coverage basique avec rapport dans le terminal
pytest --cov=src --cov=code --cov-report=term-missing

# Coverage avec rapport HTML
pytest --cov=src --cov=code --cov-report=html --cov-report=term-missing

# Coverage avec tous les rapports (HTML, XML, terminal)
pytest --cov=src --cov=code --cov-report=html --cov-report=xml --cov-report=term-missing
```

### Option 2 : Avec coverage directement

```bash
# Exécuter les tests avec coverage
coverage run -m pytest tests/

# Afficher le rapport dans le terminal
coverage report

# Générer un rapport HTML
coverage html

# Générer un rapport XML (pour CI/CD)
coverage xml
```

### Option 3 : Utiliser le script fourni

Un script bash est fourni pour simplifier l'exécution :

```bash
# Rendre le script exécutable (une seule fois)
chmod +x run_tests_with_coverage.sh

# Lancer le script
./run_tests_with_coverage.sh
```

## 📊 Comprendre les rapports

### Rapport Terminal

Le rapport terminal montre :
- **Stmts** : Nombre total de lignes de code
- **Miss** : Nombre de lignes non couvertes par les tests
- **Cover** : Pourcentage de couverture
- **Missing** : Numéros des lignes non testées

Exemple :
```
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
src/geneweb/application/services.py      245     45    82%   12-15, 45-67
```

### Rapport HTML

Le rapport HTML est généré dans le dossier `htmlcov/` :

```bash
# Ouvrir le rapport dans le navigateur
firefox htmlcov/index.html
# ou
google-chrome htmlcov/index.html
# ou
xdg-open htmlcov/index.html
```

Le rapport HTML permet de :
- ✅ Voir quelles lignes sont couvertes (en vert)
- ❌ Voir quelles lignes ne sont pas testées (en rouge)
- ⚠️ Voir les branches partiellement couvertes (en orange)
- 📈 Naviguer dans tout le code source

### Rapport XML

Le rapport XML (`coverage.xml`) est utile pour :
- Intégration CI/CD
- Outils d'analyse de code (SonarQube, Codecov, etc.)

## 🎯 Objectifs de couverture

Pour ce projet, nous visons :
- **70%** de couverture minimum (actuellement configuré)
- **80%** de couverture recommandé
- **90%+** pour le code critique (services, repositories)

## 📝 Lancer des tests spécifiques

```bash
# Tester un fichier spécifique
pytest tests/application/test_date_utils.py --cov=src

# Tester une classe spécifique
pytest tests/application/test_date_utils.py::TestParseDateForSorting --cov=src

# Tester une fonction spécifique
pytest tests/application/test_date_utils.py::TestParseDateForSorting::test_empty_date --cov=src

# Tester un module spécifique avec coverage
pytest tests/infrastructure/ --cov=src/geneweb/infrastructure
```

## 🔍 Exclure des fichiers du coverage

Le fichier `.coveragerc` (à créer) permet de configurer quels fichiers exclure :

```ini
[run]
omit =
    */tests/*
    */migrations/*
    */__pycache__/*
```

## 📈 Améliorer la couverture

1. **Identifier le code non testé** :
   ```bash
   coverage report --show-missing
   ```

2. **Voir les détails d'un fichier** :
   ```bash
   coverage report --include="src/geneweb/application/services.py"
   ```

3. **Ajouter des tests** pour les lignes manquantes

4. **Re-tester** et vérifier l'amélioration

## 🚀 Nouveaux tests ajoutés

Les nouveaux fichiers de tests suivants ont été créés :

### `tests/application/test_date_utils.py`
Tests pour les fonctions utilitaires de dates :
- `parse_date_for_sorting()` - 10 tests
- `is_possibly_alive()` - 8 tests  
- `_format_date_for_gedcom()` - 6 tests

### `tests/infrastructure/test_sql_repositories.py`
Tests pour les repositories SQL :
- `SQLPersonRepository` - 7 tests
- `SQLGenealogyRepository` - 6 tests
- Cas limites - 6 tests

### `tests/presentation/test_formatters_advanced.py`
Tests avancés pour les formatters :
- `format_date_natural()` cas avancés - 15 tests
- `parse_date_to_year()` cas avancés - 15 tests
- Tests d'intégration - 3 tests

**Total : 76 nouveaux tests** 🎉

## 📊 Commandes rapides

```bash
# Voir le coverage rapidement
pytest --cov=src --cov=code --cov-report=term

# Coverage détaillé avec HTML
pytest --cov=src --cov=code --cov-report=html && xdg-open htmlcov/index.html

# Coverage avec seuil minimum (échec si < 70%)
pytest --cov=src --cov=code --cov-fail-under=70

# Nettoyer les rapports précédents
rm -rf htmlcov .coverage coverage.xml
```

## 🔧 Troubleshooting

### Les tests ne se lancent pas

```bash
# Vérifier l'installation de pytest
pytest --version

# Réinstaller les dépendances
pip install -r code/requirements-dev.txt
```

### Coverage à 0%

```bash
# Vérifier le chemin des sources
pytest --cov=src --cov=code -v

# Vérifier que les tests passent d'abord
pytest tests/ -v
```

### ImportError

```bash
# Vérifier PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Ou lancer depuis la racine du projet
cd /home/hgrisel/EPITECH/delivery2025-2026/Legacy/G-ING-900-PAR-9-1-legacy-1
pytest --cov=src
```

## 📚 Ressources

- [Pytest Coverage Documentation](https://pytest-cov.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
