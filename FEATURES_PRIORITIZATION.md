# Priorisation des Fonctionnalités - Modernisation GeneWeb OCaml vers Python

## Vue d'ensemble

Ce document classe toutes les fonctionnalités de GeneWeb par ordre d'importance pour la modernisation Python. L'objectif est d'implémenter d'abord les fonctionnalités critiques qui constituent le cœur métier, puis progressivement les fonctionnalités de confort.

## Classification des Priorités

### 🔴 CRITIQUE (Priorité 1) - À implémenter en premier
*Fonctionnalités essentielles sans lesquelles l'application ne peut fonctionner*

#### 1. Modèles de données de base
- **Status**: ✅ En grande partie implémenté
- **Structures**: Person, Family, Event, Date, Place, Name
- **Justification**: Foundation de toute l'application, requis pour toutes les autres fonctionnalités
- **Fichiers OCaml de référence**: `lib/def/def.ml`, `lib/db/driver.ml`

#### 2. Base de données et persistance
- **Status**: ✅ En grande partie implémenté (SQLAlchemy + PostgreSQL)
- **Fonctionnalités**: CRUD persons/families, indexation noms
- **Justification**: Stockage des données généalogiques, remplacement du format .gwb
- **Fichiers OCaml de référence**: `lib/db/driver.ml`, `bin/gwc/`

#### 3. Calculs de parenté et consanguinité
- **Status**: ⏳ À compléter
- **Algorithmes requis**:
  - Calcul de consanguinité (coefficient de consanguinité)
  - Recherche d'ancêtres communs
  - Calcul des relations familiales (cousin, arrière-grand-père, etc.)
  - Numérotation Sosa (système de numérotation des ancêtres)
- **Justification**: Cœur métier de la généalogie, calculs complexes impossibles à reproduire manuellement
- **Fichiers OCaml de référence**: 
  - `lib/relation.ml` (calculs de relations)
  - `lib/consang.ml` (calcul de consanguinité)
  - `lib/sosa/` (numérotation Sosa)
  - `lib/sosaCache.ml` (optimisations)

#### 4. Import/Export GEDCOM
- **Status**: ⏳ Structure en place, à finaliser
- **Fonctionnalités**:
  - Parser GEDCOM 5.5.1 complet
  - Export vers GEDCOM standard
  - Gestion des encodages (UTF-8, ANSEL)
  - Préservation des données lors des round-trips
- **Justification**: Format standard d'échange, migration depuis/vers autres logiciels
- **Fichiers OCaml de référence**: `bin/ged2gwb/`, `bin/gwb2ged/`

#### 5. API REST de base
- **Status**: ✅ En grande partie implémenté
- **Endpoints essentiels**:
  - CRUD persons/families
  - Recherche par nom
  - Récupération d'ancêtres/descendants
  - Statistiques de base
- **Justification**: Interface pour toutes les applications clientes
- **Fichiers OCaml de référence**: `bin/gwd/` (serveur web original)

### 🟠 HAUTE (Priorité 2) - Fonctionnalités importantes
*Fonctionnalités qui améliorent significativement l'expérience utilisateur*

#### 6. Interface utilisateur web moderne
- **Status**: ❌ À implémenter
- **Composants**:
  - Templates Jinja2 remplaçant les templates OCaml
  - Interface responsive (HTML/CSS/JavaScript)
  - Navigation d'arbres généalogiques
  - Formulaires de saisie/modification
- **Justification**: Interface principale pour les utilisateurs finaux
- **Fichiers OCaml de référence**: `hd/` (templates HTML originaux)

#### 7. Système de templates et localisation
- **Status**: ⏳ Structure en place, à compléter
- **Fonctionnalités**:
  - Migration des templates OCaml vers Jinja2
  - Support multilingue (français, anglais, etc.)
  - Filtres de templating pour dates, noms, relations
- **Justification**: Flexibilité d'affichage, support international
- **Fichiers OCaml de référence**: `hd/lang/`, `hd/etc/`

#### 8. Recherche avancée
- **Status**: ⏳ Recherche de base implémentée
- **Fonctionnalités avancées**:
  - Recherche par critères multiples (dates, lieux, événements)
  - Recherche floue (similitude de noms)
  - Recherche par relations familiales
  - Index full-text
- **Justification**: Navigation efficace dans de grandes bases de données
- **Fichiers OCaml de référence**: `lib/ansel.ml`, `lib/alln.ml`

#### 9. Génération d'arbres visuels
- **Status**: ❌ À implémenter
- **Types d'arbres**:
  - Arbres d'ascendance
  - Arbres de descendance
  - Arbres en éventail
  - Export PDF/SVG
- **Justification**: Visualisation essentielle pour la généalogie
- **Fichiers OCaml de référence**: `hd/etc/modules/arbre_*`

#### 10. Gestion des événements
- **Status**: ⏳ Modèles en place, logique à compléter
- **Types d'événements**:
  - Événements personnels (naissance, mariage, décès, etc.)
  - Événements familiaux
  - Événements historiques
  - Sources et témoins
- **Justification**: Richesse des données généalogiques
- **Fichiers OCaml de référence**: `lib/def/def.ml` (types d'événements)

### 🟡 MOYENNE (Priorité 3) - Fonctionnalités utiles
*Améliorations qui enrichissent l'expérience sans être essentielles*

#### 11. Gestion des lieux et géolocalisation
- **Status**: ⏳ Modèle Place de base implémenté
- **Fonctionnalités**:
  - Standardisation des noms de lieux
  - Géocodage automatique
  - Cartes interactives
  - Migration des lieux entre formats
- **Justification**: Contextualisation géographique des événements

#### 12. Gestion des images et documents
- **Status**: ❌ À implémenter
- **Fonctionnalités**:
  - Upload et stockage d'images
  - Association images/personnes/événements
  - Galeries familiales
  - Documents numériques (actes, correspondances)
- **Justification**: Enrichissement multimédia des données

#### 13. Statistiques et rapports avancés
- **Status**: ⏳ Statistiques de base implémentées
- **Rapports avancés**:
  - Rapports de consanguinité détaillés
  - Analyses démographiques
  - Longévité par familles
  - Graphiques de distribution
- **Justification**: Analyse fine des données généalogiques

#### 14. Gestion des sources et citations
- **Status**: ⏳ Champs sources en place, à étendre
- **Fonctionnalités**:
  - Système de citations standardisé
  - Bibliographie automatique
  - Validation des sources
  - Liens vers archives en ligne
- **Justification**: Rigueur scientifique de la recherche

#### 15. Système d'annotations et notes
- **Status**: ⏳ Champs notes de base implémentés
- **Fonctionnalités étendues**:
  - Notes riches (HTML/Markdown)
  - Annotations collaboratives
  - Historique des modifications
  - Tags et catégories
- **Justification**: Documentation des recherches

### 🟢 BASSE (Priorité 4) - Fonctionnalités optionnelles
*Features "nice-to-have" qui peuvent être ajoutées plus tard*

#### 16. Gestion des utilisateurs et permissions
- **Status**: ⏳ Authentification JWT de base
- **Fonctionnalités avancées**:
  - Gestion fine des permissions par branche
  - Collaboration multi-utilisateurs
  - Historique des modifications
  - Validation des modifications
- **Justification**: Utile pour usage collaboratif mais pas essentiel

#### 17. Intégrations externes
- **Status**: ❌ À implémenter plus tard
- **Types d'intégrations**:
  - APIs d'archives en ligne (FamilySearch, etc.)
  - Import depuis autres logiciels
  - Synchronisation cloud
  - APIs de géocodage
- **Justification**: Enrichissement automatique, mais complexe

#### 18. Fonctionnalités avancées d'affichage
- **Status**: ❌ À implémenter plus tard
- **Fonctionnalités**:
  - Thèmes personnalisables
  - Impression avancée
  - Exports multiples (PDF, RTF, etc.)
  - Modes d'affichage spécialisés
- **Justification**: Confort d'usage mais pas essentiel

#### 19. Intelligence artificielle et suggestions
- **Status**: ❌ Future extension
- **Fonctionnalités**:
  - Détection automatique de doublons
  - Suggestions de liens familiaux
  - OCR automatique de documents
  - Analyse de cohérence des dates
- **Justification**: Innovation mais pas dans le scope initial

#### 20. Optimisations de performance
- **Status**: ❌ À optimiser plus tard
- **Domaines**:
  - Mise en cache avancée
  - Indexation sophistiquée
  - Calculs asynchrones
  - Compression des données
- **Justification**: Important pour de très grandes bases, mais pas critique initialement

## Plan d'implémentation recommandé

### Phase 1 (MVP - Minimum Viable Product)
- ✅ Modèles de données de base
- ✅ Base de données et persistance 
- ⏳ Calculs de parenté et consanguinité
- ⏳ Import/Export GEDCOM
- ✅ API REST de base

### Phase 2 (Interface utilisateur)
- Interface utilisateur web moderne
- Système de templates et localisation
- Recherche avancée
- Génération d'arbres visuels

### Phase 3 (Enrichissement)
- Gestion des événements complète
- Gestion des lieux et géolocalisation
- Statistiques et rapports avancés
- Gestion des sources et citations

### Phase 4 (Extensions)
- Fonctionnalités restantes selon besoins utilisateurs
- Optimisations de performance
- Intégrations externes
- Features d'IA

## Critères de réussite

### Pour chaque fonctionnalité CRITIQUE
- [ ] Tests unitaires avec 90%+ de couverture
- [ ] Tests d'intégration avec données réelles
- [ ] Performance équivalente ou supérieure à la version OCaml
- [ ] Compatibilité totale avec les données existantes

### Pour l'ensemble du projet
- [ ] Migration complète d'une base OCaml vers Python sans perte de données
- [ ] Interface utilisateur au moins équivalente à l'original
- [ ] Documentation complète pour développeurs et utilisateurs
- [ ] Déploiement Docker fonctionnel

## Notes d'implémentation

### Algorithmes complexes à porter avec attention
1. **Calcul de consanguinité** (`lib/consang.ml`)
   - Algorithme de recherche d'ancêtres communs
   - Calcul des coefficients de Wright
   - Optimisations pour éviter les recalculs

2. **Numérotation Sosa** (`lib/sosa/`)
   - Système binaire de numérotation des ancêtres
   - Navigation dans l'arbre par numéros Sosa
   - Cache des numéros pour performance

3. **Détection de relations** (`lib/relation.ml`)
   - Calcul automatique du type de relation entre deux personnes
   - Gestion des relations complexes (cousins, etc.)
   - Prise en compte des remariages

### Défis de migration identifiés
1. **Performance**: Les algorithmes OCaml sont très optimisés
2. **Exactitude**: Les calculs de consanguinité doivent être identiques
3. **Compatibilité**: Format de données et templates à préserver
4. **Complexité**: Certains algorithmes sont très sophistiqués

Ce document sera mis à jour au fur et à mesure de l'avancement du projet.