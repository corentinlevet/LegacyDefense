# ✅ Installation et Utilisation du Coverage - Guide Complet

## 📦 1. Installation (si nécessaire)

```bash
# Installer toutes les dépendances de développement
pip install -r code/requirements-dev.txt

# Ou installer uniquement les packages de coverage
pip install pytest pytest-cov coverage
```

## 🚀 2. Lancer les tests avec coverage

### Option A : Script automatique (le plus simple) ⭐

```bash
# Rendre le script exécutable (une seule fois)
chmod +x run_tests_with_coverage.sh

# Lancer le script
./run_tests_with_coverage.sh
```

Ce script :
- ✅ Nettoie les anciens rapports
- ✅ Lance tous les tests
- ✅ Génère les rapports (HTML, XML, Terminal)
- ✅ Affiche un résumé coloré
- ✅ Vérifie le seuil minimum (70%)

### Option B : Commande pytest directe

```bash
# Commande complète
pytest --cov=src --cov=code --cov-report=html --cov-report=term-missing -v

# Ou plus simple
pytest --cov=src --cov=code
```

### Option C : Coverage.py manuel

```bash
coverage run -m pytest tests/
coverage report
coverage html
```

## 📊 3. Consulter les rapports

### Rapport Terminal (automatique)

Après avoir lancé les tests, vous verrez directement :

```
Name                                         Stmts   Miss  Cover   Missing
--------------------------------------------------------------------------
src/geneweb/application/services.py            245     45    82%   12-15, 45-67
src/geneweb/infrastructure/repositories.py      89     10    89%   23, 45-50
src/geneweb/presentation/web/formatters.py      45      5    89%   67-71
--------------------------------------------------------------------------
TOTAL                                         1523    234    85%
```

**Lecture du rapport :**
- **Stmts** : Nombre total de lignes de code
- **Miss** : Nombre de lignes NON testées
- **Cover** : Pourcentage de couverture (% de lignes testées)
- **Missing** : Numéros des lignes qui ne sont pas couvertes

### Rapport HTML (détaillé et interactif) ⭐

```bash
# Ouvrir le rapport HTML
xdg-open htmlcov/index.html

# Ou avec Firefox
firefox htmlcov/index.html

# Ou avec Chrome
google-chrome htmlcov/index.html
```

**Le rapport HTML permet de :**
- 📊 Voir un tableau de tous les fichiers avec leur couverture
- 🔍 Cliquer sur un fichier pour voir le code source
- 🟢 Lignes en vert = testées
- 🔴 Lignes en rouge = NON testées
- 🟡 Lignes en jaune = partiellement testées
- 📈 Graphiques et statistiques

## 🎯 4. Interpréter les résultats

### Bon coverage ✅
```
src/geneweb/application/services.py      89%    # Excellent
src/geneweb/infrastructure/repositories.py 85%   # Très bon
```

### Coverage à améliorer ⚠️
```
src/geneweb/presentation/web/formatters.py 65%   # Moyen
src/geneweb/core/search.py                45%   # Faible - besoin de tests
```

### Objectifs recommandés
- 🎯 **70%+** : Minimum acceptable
- 🎯 **80%+** : Bon
- 🎯 **90%+** : Excellent (pour le code critique)

## 🔧 5. Tester des parties spécifiques

### Tester un seul fichier de test
```bash
pytest tests/application/test_date_utils.py --cov=src -v
```

### Tester une classe spécifique
```bash
pytest tests/application/test_date_utils.py::TestParseDateForSorting --cov=src -v
```

### Tester un module spécifique et voir sa couverture
```bash
# Tester seulement l'infrastructure
pytest tests/infrastructure/ --cov=src/geneweb/infrastructure --cov-report=term-missing
```

### Voir la couverture d'un fichier spécifique
```bash
coverage report --include="src/geneweb/application/services.py" --show-missing
```

## 📈 6. Améliorer la couverture

### Étape 1 : Identifier le code non testé
```bash
# Voir toutes les lignes manquantes
coverage report --show-missing

# Ou ouvrir le rapport HTML
xdg-open htmlcov/index.html
```

### Étape 2 : Regarder les lignes en rouge

Dans le rapport HTML, les lignes en rouge ne sont pas testées. Par exemple :
```python
def calculate_age(birth_date, death_date=None):  # Ligne verte (testée)
    if not birth_date:                            # Ligne verte (testée)
        return None                               # Ligne rouge (NON testée)
    # ... reste du code
```

### Étape 3 : Ajouter des tests

Créez un test pour couvrir cette ligne :
```python
def test_calculate_age_no_birth_date():
    result = calculate_age(None)
    assert result is None
```

### Étape 4 : Relancer et vérifier
```bash
./run_tests_with_coverage.sh
```

## 🆕 7. Tests ajoutés dans ce projet

**76 nouveaux tests** ont été ajoutés dans 3 fichiers :

1. **`tests/application/test_date_utils.py`** (24 tests)
   - Fonctions de parsing de dates
   - Détection de personnes vivantes
   - Formatage GEDCOM

2. **`tests/infrastructure/test_sql_repositories.py`** (19 tests)
   - Repositories SQL
   - Opérations de base de données
   - Cas limites

3. **`tests/presentation/test_formatters_advanced.py`** (33 tests)
   - Formatters de dates avancés
   - Cas limites et edge cases
   - Tests d'intégration

Voir `NOUVEAUX_TESTS.md` pour plus de détails.

## 📝 8. Commandes courantes

```bash
# Lancer tout avec coverage
./run_tests_with_coverage.sh

# Coverage rapide
pytest --cov=src --cov=code

# Coverage avec détails
pytest --cov=src --cov=code --cov-report=term-missing

# Coverage HTML
pytest --cov=src --cov=code --cov-report=html
xdg-open htmlcov/index.html

# Voir le rapport existant
coverage report

# Nettoyer
rm -rf htmlcov .coverage coverage.xml
```

## 🔍 9. Vérifier l'état actuel

Pour voir l'état actuel de votre coverage :

```bash
# Lancer les tests
./run_tests_with_coverage.sh

# Ou simplement
pytest --cov=src --cov=code --cov-report=term
```

Vous verrez immédiatement :
- ✅ Quels fichiers ont un bon coverage
- ⚠️ Quels fichiers ont besoin de plus de tests
- 📊 Le pourcentage global de couverture

## 📚 10. Documentation

- **Guide complet** : `TESTING_COVERAGE_GUIDE.md`
- **Nouveaux tests** : `NOUVEAUX_TESTS.md`
- **Commandes rapides** : `QUICK_COMMANDS.md`
- **Configuration** : `.coveragerc` et `pytest.ini`

## 💡 11. Conseils

1. **Lancez les tests régulièrement** pendant le développement
2. **Visez 70%+ de couverture** comme minimum
3. **Utilisez le rapport HTML** pour identifier précisément ce qui manque
4. **Testez d'abord le code critique** (services, repositories)
5. **N'oubliez pas les cas limites** (valeurs nulles, erreurs, etc.)

## 🎉 C'est tout !

Vous êtes maintenant prêt à utiliser le coverage de tests. Lancez simplement :

```bash
./run_tests_with_coverage.sh
```

Et consultez les résultats ! 🚀
