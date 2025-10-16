# 🌳 Guide d'utilisation de l'arbre interactif GeneWeb

## ✅ Fichier tree_interactive.html : **RELIÉ AU PROJET**

Le fichier `tree_interactive.html` est **maintenant complètement intégré** au projet GeneWeb !

## 📍 URLs disponibles

### 1. **Arbre interactif D3.js**
```
http://localhost:8001/tree/interactive
```
- Visualisation interactive avec D3.js
- Zoom, pan, navigation dans l'arbre
- Affichage des détails des personnes au clic

### 2. **API de données d'arbre**
```
http://localhost:8001/api/tree/{type}/{root_id}?max_gen={generations}
```

**Paramètres :**
- `{type}` : Type d'arbre
  - `ancestors` : Arbre d'ascendance
  - `descendants` : Arbre de descendance
  - `hourglass` : Arbre en sablier (ascendance + descendance)
  - `full` : Arbre complet
  
- `{root_id}` : ID de la personne racine (exemple: 1, 2, 3...)
- `{generations}` : Nombre de générations (par défaut: 4)

**Exemples :**
```bash
# Arbre d'ascendance de la personne 1, 5 générations
http://localhost:8001/api/tree/ancestors/1?max_gen=5

# Arbre de descendance de la personne 3
http://localhost:8001/api/tree/descendants/3

# Arbre en sablier de la personne 2
http://localhost:8001/api/tree/hourglass/2
```

### 3. **Recherche avancée**
```
http://localhost:8001/search/advanced
```
- Recherche multi-critères
- Fuzzy matching (correspondance approximative)
- Soundex phonétique
- Export CSV/GEDCOM

## 🔧 Fichiers modifiés

### 1. **`core/tree_routes.py`** (nouveau)
Module contenant les routes pour l'arbre interactif :
- `/tree/interactive` : Page de visualisation
- `/api/tree/{type}/{root_id}` : API JSON
- `/search/advanced` : Recherche avancée

### 2. **`core/webapp.py`** (modifié)
Ajout de l'import des routes :
```python
from .tree_routes import add_tree_routes
add_tree_routes(self)
```

### 3. **`templates/home.html`** (modifié)
Ajout de boutons d'accès rapide :
- "Launch Tree Viewer" → `/tree/interactive`
- "Advanced Search" → `/search/advanced`

## 🚀 Comment utiliser

### Démarrer le serveur
```bash
cd /home/hgrisel/EPITECH/delivery2025-2026/Legacy/G-ING-900-PAR-9-1-legacy-1/code
/home/hgrisel/EPITECH/delivery2025-2026/Legacy/.venv/bin/python run_app.py
```

### Accéder à l'arbre interactif
1. Ouvrez votre navigateur
2. Allez sur `http://localhost:8001`
3. Cliquez sur "Launch Tree Viewer" 
4. OU allez directement sur `http://localhost:8001/tree/interactive`

### Contrôles de l'arbre
- **Sélectionner le type d'arbre** : Ancestors, Descendants, Hourglass, Full
- **ID de la personne racine** : Entrez l'ID (1, 2, 3...)
- **Nombre de générations** : 1-10
- **Zoom** : Boutons +/- ou molette de souris
- **Pan** : Cliquez-glissez pour déplacer
- **Info personne** : Cliquez sur un nœud

## 📊 Fonctionnalités de l'arbre

### Visualisation
- Rendu SVG avec D3.js v7
- Couleur par sexe (bleu = homme, rouge = femme, gris = inconnu)
- Liens hiérarchiques entre générations
- Labels avec noms complets

### Interactivité
- **Panneau de contrôles** : Type d'arbre, générations, personne racine
- **Panneau d'informations** : Détails de la personne sélectionnée
- **Boutons de zoom** : Zoom avant/arrière, réinitialiser
- **Export SVG** : Télécharger l'arbre au format SVG
- **Légende** : Code couleur pour les sexes

### Navigation
- `Redraw Tree` : Redessiner avec les nouveaux paramètres
- `Expand All` : Développer tous les nœuds
- `Collapse All` : Réduire tous les nœuds
- `Center View` : Recentrer la vue
- `Download SVG` : Télécharger l'image

## 🔍 API JSON Response Format

```json
{
  "id": 1,
  "name": "John Doe",
  "first_name": "John",
  "surname": "Doe",
  "sex": "M",
  "birth": "1950-01-15",
  "death": null,
  "occupation": "Engineer",
  "children": [
    {
      "id": 2,
      "name": "Jane Doe",
      ...
      "children": []
    }
  ]
}
```

## 🎨 Personnalisation

Le fichier `tree_interactive.html` peut être personnalisé :
- **Couleurs** : Modifier les variables CSS dans `<style>`
- **Icônes** : Font Awesome 6.0
- **Disposition** : Modifier les paramètres D3.js dans `<script>`

## ✅ Checklist d'intégration

- [x] Fichier `tree_interactive.html` créé
- [x] Module `core/tree_routes.py` créé
- [x] Routes ajoutées dans `webapp.py`
- [x] Liens ajoutés dans `home.html`
- [x] API `/api/tree/{type}/{root_id}` fonctionnelle
- [x] Dépendances installées (FastAPI, Uvicorn)
- [x] Serveur testé et opérationnel

## 🐛 Dépannage

### Erreur 404 sur `/tree-interactive`
❌ **Mauvaise URL** : `/tree-interactive`  
✅ **Bonne URL** : `/tree/interactive` (avec le slash)

### Pas de données dans l'arbre
- Vérifiez que la base de données contient des personnes
- Assurez-vous que les relations parents/enfants sont définies
- Utilisez un `root_id` valide (personne existante)

### Erreur au démarrage
```bash
# Vérifier l'installation
pip list | grep -E "fastapi|uvicorn|sqlalchemy"

# Réinstaller si nécessaire
pip install -r requirements.txt
```

## 📚 Documentation complémentaire

- **D3.js Documentation** : https://d3js.org/
- **FastAPI Documentation** : https://fastapi.tiangolo.com/
- **Code source** : `/code/templates/tree_interactive.html`
- **Routes API** : `/code/core/tree_routes.py`

---

**Créé le** : 16 octobre 2025  
**Version** : 1.0  
**Statut** : ✅ Complètement intégré et fonctionnel
