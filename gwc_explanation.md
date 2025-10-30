# Analyse de la commande `gwc -f -o test`

Cette documentation explique le fonctionnement de la commande `gwc -f -o test` utilisée dans le projet GeneWeb original (en OCaml) et propose une approche pour implémenter une fonctionnalité équivalente dans le projet `geneweb-python`.

## Fonctionnement dans le projet OCaml

La commande `gwc` est l'outil de compilation et de création de bases généalogiques de GeneWeb.

`gwc -f -o test`

- **`gwc`**: L'exécutable qui gère la création de la base.
- **`-o test`**: Spécifie le nom de la base de sortie. Dans ce cas, `test`.
- **`-f`**: L'option "force". Si une base nommée `test` existe déjà, elle sera supprimée et recréée. Sans cette option, le programme s'arrêterait avec une erreur si la base existait.

### Processus de création

1.  **Analyse des arguments** : Le programme identifie le nom de la base (`test`) et l'option `-f`.
2.  **Vérification de l'existence** : Le programme vérifie si une base nommée `test` existe. Grâce à l'option `-f`, il procède à la suppression des anciens fichiers si c'est le cas.
3.  **Création du répertoire de la base** : Il crée un nouveau répertoire pour stocker les fichiers de la base. Le nom du répertoire est conventionnellement le nom de la base suivi de l'extension `.gwb`. Pour notre commande, cela crée le dossier `bases/test.gwb/`.
4.  **Création des fichiers de données** : À l'intérieur de `test.gwb/`, `gwc` initialise un ensemble de fichiers binaires qui constituent la structure d'une base de données GeneWeb vide. Ces fichiers contiendront les données sur les individus, les familles, les notes, les sources, etc.
5.  **Création du fichier de configuration** : Un fichier de configuration par défaut, `test.gwf`, est également créé. Il contient les paramètres spécifiques à cette base (langue, titres, etc.).

En résumé, la commande crée un **squelette de base de données généalogique vide** sous la forme d'un répertoire et de fichiers dédiés.

## Implémentation dans `geneweb-python`

Le projet `geneweb-python` utilise une approche différente, basée sur une base de données SQL unique (probablement SQLite, PostgreSQL, etc.) gérée par SQLAlchemy. Il n'y a pas de système de fichiers par base comme dans l'original.

L'équivalent de "créer une généalogie" serait d'isoler les données d'une généalogie des autres au sein de la même base de données.

### Approche proposée

Pour ce faire, nous pouvons ajouter une nouvelle table (un nouveau modèle SQLAlchemy) que nous appellerons `Genealogy` ou `Base`.

**1. Mettre à jour `models.py`**

Nous devons ajouter un modèle `Genealogy` et lier nos modèles existants (`Person`, `Family`, etc.) à celui-ci avec une clé étrangère.

```python
# Dans src/geneweb/infrastructure/models.py

class Genealogy(Base):
    __tablename__ = "genealogies"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    # On pourrait ajouter d'autres métadonnées ici (créateur, date, etc.)

# Ensuite, modifier Person, Family, etc. pour inclure une référence à la généalogie :

class Person(Base):
    __tablename__ = "persons"

    # ... autres colonnes
    genealogy_id = Column(Integer, ForeignKey("genealogies.id"), nullable=False, index=True)
    genealogy = relationship("Genealogy")

class Family(Base):
    __tablename__ = "families"

    # ... autres colonnes
    genealogy_id = Column(Integer, ForeignKey("genealogies.id"), nullable=False, index=True)
    genealogy = relationship("Genealogy")

# Et ainsi de suite pour les autres modèles...
```

**2. Créer un service pour la création**

Nous créerons ensuite une fonction ou un service (par exemple, dans la couche `application`) qui :
1.  Prend un nom de généalogie en entrée.
2.  Vérifie si une généalogie avec ce nom existe déjà.
3.  Si l'option "force" est activée, supprime l'ancienne généalogie et toutes les données associées (personnes, familles, etc.).
4.  Crée une nouvelle entrée dans la table `genealogies`.

Cette approche permet de gérer plusieurs généalogies de manière isolée au sein d'une seule base de données moderne, tout en respectant la logique de la commande `gwc` originale.
