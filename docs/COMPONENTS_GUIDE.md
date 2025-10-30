# Guide Simplifié des Composants GeneWeb

## Introduction

Vous souhaitez comprendre comment fonctionne GeneWeb ou contribuer au projet ? Ce guide vous explique de manière simple et accessible le rôle de chaque composant.

---

## Vue d'Ensemble en 3 Minutes

**GeneWeb est un logiciel de généalogie qui vous permet de :**
- 📊 Stocker des informations sur votre famille
- 🌳 Visualiser des arbres généalogiques
- 🔍 Rechercher des personnes
- 🧮 Calculer des relations de parenté
- 📤 Importer/Exporter des données au format GEDCOM

**Architecture simplifiée :**

```
┌─────────────────────────────────────────┐
│    VOUS (via un navigateur web)         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│    INTERFACE WEB (pages HTML)           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│    LOGIQUE MÉTIER (calculs)             │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│    BASE DE DONNÉES (vos données)        │
└─────────────────────────────────────────┘
```

---

## Les Programmes Principaux (bin/)

Ce sont les outils que vous utilisez en ligne de commande.

### 🌐 `gwd` - Le Serveur Web
**C'est quoi ?** Le programme principal qui lance le site web de GeneWeb.

**Quand l'utiliser ?** À chaque fois que vous voulez accéder à votre généalogie via un navigateur.

**Exemple :**
```bash
./gwd -bd mes_bases -p 2317
```
Puis ouvrez votre navigateur sur `http://localhost:2317`

---

### ⚙️ `gwsetup` - L'Interface d'Administration
**C'est quoi ?** Une interface pour configurer GeneWeb sans éditer de fichiers.

**Ce que vous pouvez faire :**
- Créer une nouvelle base de données
- Changer les paramètres (langue, accès, etc.)
- Nettoyer et optimiser votre base

**Exemple :**
```bash
./gwsetup -p 2316
```
Ouvrez `http://localhost:2316` pour accéder à l'admin.

---

### 📥 `ged2gwb` - Importeur GEDCOM
**C'est quoi ?** Convertit un fichier GEDCOM (format standard) en base GeneWeb.

**Quand l'utiliser ?** Quand vous avez exporté vos données d'un autre logiciel (Heredis, Geneatique, etc.).

**Exemple :**
```bash
./ged2gwb ma_famille.ged -o ma_base
```

**Format GEDCOM :** C'est le format universel pour échanger des données généalogiques entre différents logiciels.

---

### 📤 `gwb2ged` - Exporteur GEDCOM
**C'est quoi ?** L'inverse de `ged2gwb`. Exporte votre base GeneWeb en fichier GEDCOM.

**Quand l'utiliser ?** Pour faire une sauvegarde ou utiliser vos données dans un autre logiciel.

**Exemple :**
```bash
./gwb2ged ma_base -o sauvegarde.ged
```

---

### 💾 `gwu` - Décompilateur
**C'est quoi ?** Transforme votre base binaire en fichier texte lisible (.gw).

**Quand l'utiliser ?** Pour faire une sauvegarde lisible ou voir le contenu brut.

**Exemple :**
```bash
./gwu ma_base > sauvegarde.gw
```

---

### 🧬 `consang` - Calculateur de Consanguinité
**C'est quoi ?** Calcule si des personnes dans votre arbre ont des ancêtres communs (consanguinité).

**Pourquoi c'est utile ?**
- Information génétique importante
- Détecte les mariages entre cousins

**Exemple :**
```bash
./consang ma_base
```

---

### 🔗 `connex` - Vérificateur de Connexité
**C'est quoi ?** Vérifie que toutes les personnes de votre base sont connectées.

**Ce qu'il détecte :**
- Personnes isolées (sans lien avec les autres)
- Groupes familiaux séparés

**Exemple :**
```bash
./connex ma_base
```

---

### 🔧 `fixbase` - Réparateur de Base
**C'est quoi ?** Corrige les erreurs et incohérences dans votre base.

**Problèmes corrigés :**
- Références cassées
- Dates incohérentes
- Doublons

**Exemple :**
```bash
./fixbase ma_base
```

⚠️ **Conseil :** Faites une sauvegarde avant !

---

## Les Bibliothèques (lib/)

C'est le "moteur" de GeneWeb. Vous n'interagissez pas directement avec ces fichiers, mais ils font tout le travail en coulisses.

### 📚 Catégories Principales

#### 1. **Définitions de Données** (`def/`, `core/`)
**Rôle :** Définit ce qu'est une "personne", une "famille", un "événement", etc.

**Exemple de données :**
```
Personne :
- Prénom : Jean
- Nom : Dupont
- Date de naissance : 15/03/1950
- Père : Pierre Dupont
- Mère : Marie Martin
```

---

#### 2. **Algorithmes Généalogiques**

##### `relation.ml` - Calcul de Relations
**Rôle :** Détermine la relation entre deux personnes.

**Exemples de relations détectées :**
- Frère/Sœur
- Cousin(e) germain(e)
- Oncle/Tante
- Arrière-grand-parent
- Cousin(e) au 3ème degré

**Comment ça marche ?**
1. Cherche les ancêtres communs
2. Compte le nombre de générations
3. Détermine le type de relation

---

##### `consang.ml` - Consanguinité
**Rôle :** Calcule le coefficient de consanguinité.

**Qu'est-ce que c'est ?**
C'est un nombre entre 0 et 1 qui indique si vos parents sont apparentés.

**Exemples :**
- Parents non apparentés : 0
- Parents cousins germains : 0.0625 (1/16)
- Parents frère/sœur : 0.25 (1/4)

**Formule (simplifié) :**
Pour chaque ancêtre commun, on ajoute (1/2)^nombre_de_générations

---

##### `sosa/` - Numérotation Sosa
**Rôle :** Attribue un numéro unique à chaque ancêtre.

**Le système Sosa-Stradonitz :**
```
         Vous : 1
         /        \
    Père : 2    Mère : 3
      /  \        /  \
   4     5      6     7
(GP paternel...) (GP maternel...)
```

**Règle :** 
- Père = 2 × numéro de l'enfant
- Mère = 2 × numéro de l'enfant + 1

**Utilité :** Navigation rapide dans l'arbre.

---

#### 3. **Affichage** (tous les `*Display.ml`)

Ces fichiers génèrent les pages HTML que vous voyez.

| Fichier | Ce qu'il affiche |
|---------|------------------|
| `perso.ml` | Page de détails d'une personne |
| `ascendDisplay.ml` | Arbre d'ascendance (ancêtres) |
| `descendDisplay.ml` | Arbre de descendance (descendants) |
| `dagDisplay.ml` | Graphes complexes avec boucles |
| `birthdayDisplay.ml` | Liste des anniversaires |
| `statsDisplay.ml` | Statistiques de la base |

---

#### 4. **Édition et Mise à Jour**

| Fichier | Fonction |
|---------|----------|
| `update.ml` | Mise à jour générale |
| `updateInd.ml` | Modification d'une personne |
| `updateFam.ml` | Modification d'une famille |
| `merge*.ml` | Fusion de doublons |

---

#### 5. **Recherche**

##### `searchName.ml` - Recherche par Nom
**Fonctionnalités :**
- Recherche exacte : "Dupont"
- Recherche phonétique : "Dupon" trouve "Dupont"
- Recherche approximative : "Dupond" trouve "Dupont"

**Algorithmes utilisés :**
- **Soundex** : Compare les sons
- **Levenshtein** : Mesure la similarité

---

#### 6. **Validation** (`check.ml`, `checkData.ml`)

**Rôle :** Détecte les erreurs dans vos données.

**Exemples de vérifications :**
- ❌ Naissance après décès
- ❌ Personne mariée à 5 ans
- ❌ Personne ayant un enfant à 90 ans
- ❌ Dates impossibles (32/13/1999)

---

#### 7. **Base de Données** (`db/`)

**Rôle :** Lit et écrit les données dans la base.

**Ce qu'il gère :**
- Stockage efficace sur le disque
- Index pour recherche rapide
- Cohérence des données

---

## Version Python : La Modernisation

La version Python réorganise tout selon une architecture moderne et plus facile à maintenir.

### Structure en 4 Couches

```
┌──────────────────────────────────────┐
│  PRÉSENTATION (Interface)            │ ← Ce que vous voyez
│  - Pages Web                         │
│  - API REST                          │
└──────────────────────────────────────┘
             ▼
┌──────────────────────────────────────┐
│  APPLICATION (Services)              │ ← Coordination
│  - PersonService                     │
│  - SearchService                     │
└──────────────────────────────────────┘
             ▼
┌──────────────────────────────────────┐
│  DOMAINE (Logique Métier)            │ ← Le cerveau
│  - Algorithmes                       │
│  - Modèles de données                │
└──────────────────────────────────────┘
             ▼
┌──────────────────────────────────────┐
│  INFRASTRUCTURE (Technique)          │ ← La plomberie
│  - Base de données PostgreSQL        │
│  - Import/Export GEDCOM              │
└──────────────────────────────────────┘
```

---

### Nouveautés de la Version Python

#### ✅ API REST Moderne
**Avant :** Seulement une interface web.
**Maintenant :** Aussi une API pour les développeurs.

**Exemples d'utilisation :**
```bash
# Récupérer une personne
GET /api/v1/persons/123

# Rechercher
GET /api/v1/search?name=Dupont

# Calculer une relation
GET /api/v1/relationship?p1=123&p2=456
```

---

#### ✅ Base de Données Relationnelle
**Avant :** Format binaire propriétaire.
**Maintenant :** PostgreSQL (ou SQLite).

**Avantages :**
- Sauvegardes faciles
- Outils standard
- Requêtes SQL puissantes

---

#### ✅ Tests Automatisés
**Avant :** Tests manuels.
**Maintenant :** Tests automatiques à chaque modification.

**Exemple de test :**
```python
def test_relationship_between_siblings():
    # Crée deux frères
    brother1 = create_person("Jean", "Dupont")
    brother2 = create_person("Paul", "Dupont")
    
    # Vérifie la relation
    relation = find_relationship(brother1, brother2)
    assert relation == "Frère"
```

---

#### ✅ Documentation Automatique
L'API est automatiquement documentée avec **Swagger/OpenAPI**.

Accédez à `http://localhost:8000/docs` pour voir toutes les fonctions disponibles.

---

## Comment les Composants Travaillent Ensemble ?

### Exemple Concret : "Afficher la page de Jean Dupont"

#### Étape 1 : Vous cliquez sur "Jean Dupont"
```
Navigateur → Envoie requête GET /person/123
```

#### Étape 2 : Le serveur reçoit la requête
```python
# presentation/api/routers/persons.py
@router.get("/persons/{person_id}")
def get_person(person_id: int):
    return person_service.get_person(person_id)
```

#### Étape 3 : Le service récupère les données
```python
# application/services/person_service.py
def get_person(self, person_id: int):
    # Récupère la personne
    person = self.person_repo.get_by_id(person_id)
    
    # Récupère ses parents
    father = self.person_repo.get_by_id(person.father_id)
    mother = self.person_repo.get_by_id(person.mother_id)
    
    return {
        "person": person,
        "father": father,
        "mother": mother
    }
```

#### Étape 4 : La base de données est interrogée
```python
# infrastructure/repositories/sql_person_repository.py
def get_by_id(self, person_id: int):
    return db.query(Person).filter(Person.id == person_id).first()
```

#### Étape 5 : Les données remontent et sont affichées
```
Base de données → Repository → Service → API → Navigateur
```

---

## Tableau Récapitulatif : OCaml → Python

| Vous voulez... | OCaml | Python |
|----------------|-------|--------|
| Lancer le serveur web | `./gwd` | `uvicorn main:app` |
| Importer un GEDCOM | `./ged2gwb fichier.ged` | API POST `/api/v1/gedcom/import` |
| Calculer la consanguinité | `./consang base` | Fonction `calculate_consanguinity()` |
| Chercher une personne | Interface web | API GET `/api/v1/search?name=...` |
| Voir une personne | `http://localhost:2317/person?p=123` | `http://localhost:8000/persons/123` |

---

## FAQ - Questions Fréquentes

### Dois-je comprendre OCaml pour contribuer à la version Python ?
**Non.** La version Python est indépendante. Cependant, comprendre les algorithmes OCaml aide pour les porter.

### Puis-je utiliser mes données GeneWeb existantes avec la version Python ?
**Oui**, via un export GEDCOM :
1. Exportez : `./gwb2ged ma_base -o export.ged`
2. Importez dans Python : POST `/api/v1/gedcom/import`

### Quelle version dois-je utiliser ?
- **OCaml** : Mature, stable, utilisée par des milliers de personnes
- **Python** : Moderne, en développement, pour les nouveaux projets

### Comment contribuer ?
1. Lisez [CONTRIBUTING.md](../CONTRIBUTING.md)
2. Choisissez une fonctionnalité à implémenter
3. Écrivez les tests d'abord (TDD)
4. Implémentez le code
5. Soumettez une Pull Request

---

## Ressources pour Aller Plus Loin

### Documentation Technique
- [Architecture Détaillée](COMPONENTS_OVERVIEW.md) - Pour les développeurs
- [Principes SOLID](SOLID_PRINCIPLES.md) - Architecture Python
- [Guide du développeur](DEVELOPER_SETUP.md) - Installation

### Algorithmes
- [Algorithme de Jacquard](https://en.wikipedia.org/wiki/Coefficient_of_relationship) - Consanguinité
- [Numérotation Sosa](https://en.wikipedia.org/wiki/Ahnentafel) - Système de numérotation

### Format GEDCOM
- [Spécification GEDCOM 5.5.1](https://www.gedcom.org/)

---

## Glossaire

| Terme | Définition |
|-------|------------|
| **GEDCOM** | Format standard pour échanger des données généalogiques |
| **Consanguinité** | Degré de parenté entre les parents d'une personne |
| **Sosa** | Système de numérotation des ancêtres |
| **De cujus** | La personne de référence dans un arbre (vous) |
| **Ascendance** | Vos ancêtres (parents, grands-parents...) |
| **Descendance** | Vos descendants (enfants, petits-enfants...) |
| **DAG** | Directed Acyclic Graph - Graphe pour relations complexes |
| **API REST** | Interface pour accéder aux données programmatiquement |
| **TDD** | Test-Driven Development - Écrire les tests avant le code |
| **ORM** | Object-Relational Mapping - Passerelle entre objets et BDD |

---

## Conclusion

GeneWeb est composé de nombreux outils qui travaillent ensemble pour gérer votre généalogie :

1. **Programmes en ligne de commande** (`gwd`, `ged2gwb`, etc.) pour l'interaction
2. **Bibliothèques** (`lib/`) pour la logique métier
3. **Base de données** pour stocker vos données
4. **Interface web** pour visualiser et éditer

La version Python modernise cette architecture tout en conservant les algorithmes éprouvés.

**Prochaines étapes :**
- Consultez le [guide utilisateur](../user/USER_GUIDE.md) pour utiliser GeneWeb
- Lisez le [guide de développement](DEVELOPER_SETUP.md) pour contribuer
- Explorez les [exemples de code](../../tests/) pour comprendre le fonctionnement

---

**Dernière mise à jour :** Octobre 2025

**Besoin d'aide ?** Ouvrez une issue sur GitHub ou consultez la documentation complète.
