# 🧪 Nouveaux Tests Ajoutés

Ce document résume les nouveaux tests ajoutés pour améliorer la couverture du code.

## 📊 Résumé

**76 nouveaux tests** ont été ajoutés répartis sur 3 fichiers :

| Fichier de Test | Nombre de Tests | Ce qui est testé |
|----------------|-----------------|------------------|
| `tests/application/test_date_utils.py` | 24 tests | Fonctions utilitaires de dates |
| `tests/infrastructure/test_sql_repositories.py` | 19 tests | Repositories SQL et base de données |
| `tests/presentation/test_formatters_advanced.py` | 33 tests | Formatters avancés et cas limites |

## 📁 Détails des fichiers de tests

### 1. `tests/application/test_date_utils.py`

Tests pour les fonctions utilitaires de gestion des dates dans `src/geneweb/application/services.py`.

#### `TestParseDateForSorting` (10 tests)
Teste la fonction `parse_date_for_sorting()` qui convertit des dates texte en tuples pour le tri :
- ✅ Dates vides/nulles
- ✅ Dates avec préfixe "Avant"/"Before"
- ✅ Dates estimées "Estimé"/"About"
- ✅ Dates "Entre X et Y"
- ✅ Années simples
- ✅ Formats de dates complètes (DD/MM/YYYY, YYYY-MM-DD)
- ✅ Dates invalides
- ✅ Cas limites (année 0, 9999)

#### `TestIsPossiblyAlive` (8 tests)
Teste la fonction `is_possibly_alive()` qui détermine si une personne est potentiellement vivante :
- ✅ Personne avec date de décès
- ✅ Personne sans date de naissance
- ✅ Personne née récemment
- ✅ Personne née il y a 120 ans (limite)
- ✅ Personne née il y a plus de 120 ans
- ✅ Date de naissance invalide
- ✅ Date de naissance estimée

#### `TestFormatDateForGedcom` (6 tests)
Teste la fonction `_format_date_for_gedcom()` qui convertit des dates Python en format GEDCOM :
- ✅ Valeur None
- ✅ Chaînes de caractères
- ✅ Objets `date`
- ✅ Objets `datetime`
- ✅ Tous les mois de l'année

### 2. `tests/infrastructure/test_sql_repositories.py`

Tests pour les repositories SQL qui gèrent l'accès à la base de données.

#### `TestSQLPersonRepository` (7 tests)
Teste `SQLPersonRepository` :
- ✅ Récupération d'une personne existante par ID
- ✅ Récupération d'une personne inexistante
- ✅ Ajout d'une nouvelle personne
- ✅ Ajout avec dates de naissance et décès
- ✅ Ajout de plusieurs personnes

#### `TestSQLGenealogyRepository` (6 tests)
Teste `SQLGenealogyRepository` :
- ✅ Récupération par nom (existante/inexistante)
- ✅ Sensibilité à la casse
- ✅ Création de généalogie
- ✅ Généalogie avec personnes associées

#### `TestRepositoryEdgeCases` (6 tests)
Tests des cas limites :
- ✅ Noms vides
- ✅ Noms très longs (200 caractères)
- ✅ Caractères spéciaux (François-René, O'Connor-Smith)
- ✅ ID = 0
- ✅ ID négatif

### 3. `tests/presentation/test_formatters_advanced.py`

Tests avancés pour les formatters de dates avec cas limites.

#### `TestFormatDateNaturalAdvanced` (15 tests)
Tests avancés pour `format_date_natural()` :
- ✅ Espaces supplémentaires
- ✅ Préfixes imbriqués
- ✅ Entrées en minuscules/casse mixte
- ✅ Mois inconnus/invalides
- ✅ Jours invalides
- ✅ Années limites (0001, 9999)
- ✅ Tous les préfixes supportés
- ✅ Jours à un ou deux chiffres
- ✅ Formats ne matchant aucun pattern

#### `TestParseDateToYearAdvanced` (15 tests)
Tests avancés pour `parse_date_to_year()` :
- ✅ Dates vides
- ✅ Années simples
- ✅ Années avec préfixes/suffixes
- ✅ Dates complètes
- ✅ Dates "entre X et Y"
- ✅ Texte sans année
- ✅ Années limites
- ✅ Années multiples
- ✅ Caractères spéciaux autour de l'année
- ✅ Nombres à 3 ou 5 chiffres
- ✅ Dates formatées en français

#### `TestFormattersIntegration` (3 tests)
Tests d'intégration :
- ✅ Formatage puis parsing
- ✅ Aller-retour avec différents formats
- ✅ Cohérence avec dates vides

## 🚀 Lancer les nouveaux tests

### Tous les nouveaux tests
```bash
pytest tests/application/test_date_utils.py tests/infrastructure/test_sql_repositories.py tests/presentation/test_formatters_advanced.py -v
```

### Par fichier
```bash
# Tests des utilitaires de dates
pytest tests/application/test_date_utils.py -v

# Tests des repositories
pytest tests/infrastructure/test_sql_repositories.py -v

# Tests des formatters avancés
pytest tests/presentation/test_formatters_advanced.py -v
```

### Avec coverage
```bash
# Voir la couverture des nouveaux tests
pytest tests/application/test_date_utils.py --cov=src/geneweb/application/services --cov-report=term-missing
```

## 📈 Impact sur la couverture

Ces tests devraient améliorer significativement la couverture de :

- **`src/geneweb/application/services.py`** : Fonctions utilitaires (+20-30%)
- **`src/geneweb/infrastructure/repositories/`** : Repositories SQL (+40-50%)
- **`src/geneweb/presentation/web/formatters.py`** : Formatters (+15-25%)

## 🔍 Vérifier la couverture

Pour voir l'impact des nouveaux tests sur la couverture :

```bash
# Lancer tous les tests avec coverage
./run_tests_with_coverage.sh

# Ou manuellement
pytest --cov=src --cov=code --cov-report=html
xdg-open htmlcov/index.html
```

## 📝 Notes

- Tous les tests utilisent des bases de données en mémoire (SQLite) pour l'isolation
- Les fixtures pytest permettent de réutiliser la configuration
- Les tests sont organisés en classes pour une meilleure lisibilité
- Les cas limites et edge cases sont bien couverts

## ✅ Prochaines étapes

Pour continuer à améliorer la couverture :

1. Identifier les fonctions non testées avec `coverage report --show-missing`
2. Ajouter des tests pour les routes web (`routers`)
3. Tester les cas d'erreurs et exceptions
4. Ajouter des tests d'intégration end-to-end

---

📖 Voir le fichier `TESTING_COVERAGE_GUIDE.md` pour le guide complet du coverage.
