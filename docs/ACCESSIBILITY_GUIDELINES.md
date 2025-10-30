# Directives d'Accessibilité - GeneWeb Python

## Vue d'ensemble

Ce document décrit les recommandations et directives d'accessibilité pour le projet GeneWeb Python. L'accessibilité est une priorité fondamentale qui garantit que notre application de généalogie est utilisable par tous, indépendamment de leurs capacités physiques ou cognitives.

## Objectifs

- **Conformité WCAG 2.1 Niveau AA** : Atteindre et maintenir la conformité aux Directives pour l'accessibilité des contenus Web (WCAG) 2.1 niveau AA
- **Inclusivité** : Garantir que tous les utilisateurs peuvent accéder aux fonctionnalités principales
- **Tests réguliers** : Valider l'accessibilité à chaque itération du développement

---

## 1. Principes POUR (POUR = Perceivable, Operable, Understandable, Robust)

### 1.1 Perceptible

L'information et les composants de l'interface utilisateur doivent être présentés de manière à ce que les utilisateurs puissent les percevoir.

#### Alternatives textuelles
- **Images** : Toutes les images doivent avoir un attribut `alt` descriptif
  ```html
  <img src="arbre_genealogique.png" alt="Arbre généalogique de la famille Dupont sur 4 générations">
  ```
- **Icônes** : Utiliser des attributs `aria-label` pour les icônes fonctionnelles
  ```html
  <button aria-label="Ajouter une nouvelle personne">
    <i class="icon-plus"></i>
  </button>
  ```

#### Contraste des couleurs
- **Ratio minimum** : 4.5:1 pour le texte normal, 3:1 pour le texte large (18pt+)
- **Outils de vérification** : Utiliser WebAIM Contrast Checker ou similaire
- **Ne pas se fier uniquement à la couleur** : Utiliser des textures, des motifs ou des labels en plus de la couleur pour transmettre l'information

#### Contenu multimédia
- **Transcriptions** : Fournir des transcriptions textuelles pour tout contenu audio
- **Sous-titres** : Ajouter des sous-titres pour les vidéos tutorielles

### 1.2 Utilisable

Les composants de l'interface utilisateur et la navigation doivent être utilisables.

#### Navigation au clavier
- **Tabulation** : Tous les éléments interactifs doivent être accessibles via la touche Tab
- **Ordre logique** : L'ordre de tabulation doit suivre un flux logique
- **Indicateurs de focus visibles** : Styles CSS pour `:focus` et `:focus-visible`
  ```css
  button:focus-visible,
  a:focus-visible {
    outline: 3px solid #005fcc;
    outline-offset: 2px;
  }
  ```
- **Raccourcis clavier** : Documenter tous les raccourcis clavier disponibles

#### Pas de piège au clavier
- Les utilisateurs doivent pouvoir sortir de tous les composants en utilisant uniquement le clavier
- Modalités et boîtes de dialogue doivent être fermables avec la touche Échap

#### Temps suffisant
- **Pas de limite de temps arbitraire** : Éviter les sessions qui expirent sans avertissement
- **Avertissements** : Informer l'utilisateur avant l'expiration d'une session et permettre l'extension
- **Pause/arrêt** : Permettre de mettre en pause ou d'arrêter le contenu en mouvement automatique

#### Prévention des crises
- **Pas de flashs** : Éviter tout contenu qui flashe plus de 3 fois par seconde
- **Animations** : Respecter la préférence `prefers-reduced-motion`
  ```css
  @media (prefers-reduced-motion: reduce) {
    * {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
    }
  }
  ```

### 1.3 Compréhensible

L'information et l'utilisation de l'interface utilisateur doivent être compréhensibles.

#### Langage clair
- **Simplicité** : Utiliser un langage simple et direct
- **Définitions** : Fournir des définitions pour les termes généalogiques spécialisés
- **Langue de la page** : Déclarer la langue principale avec `<html lang="fr">`

#### Prévisibilité
- **Navigation cohérente** : Maintenir la même structure de navigation sur toutes les pages
- **Identifications cohérentes** : Les mêmes fonctionnalités doivent avoir les mêmes labels

#### Aide à la saisie
- **Labels explicites** : Chaque champ de formulaire doit avoir un label clair
  ```html
  <label for="nom">Nom de famille</label>
  <input type="text" id="nom" name="nom" required>
  ```
- **Messages d'erreur** : Fournir des messages d'erreur descriptifs et des suggestions de correction
- **Validation** : Indiquer clairement les champs obligatoires et le format attendu

### 1.4 Robuste

Le contenu doit être suffisamment robuste pour être interprété de manière fiable par une grande variété d'agents utilisateurs, y compris les technologies d'assistance.

#### Code HTML valide
- **Validation W3C** : Utiliser le validateur W3C pour s'assurer que le HTML est conforme
- **Sémantique HTML5** : Utiliser les balises sémantiques appropriées (`<nav>`, `<main>`, `<article>`, `<aside>`)

#### ARIA (Accessible Rich Internet Applications)
- **Utilisation appropriée** : N'utiliser ARIA que lorsque le HTML natif ne suffit pas
- **Rôles ARIA** : Définir les rôles pour les composants personnalisés
  ```html
  <div role="navigation" aria-label="Navigation principale">
    <!-- contenu -->
  </div>
  ```
- **États et propriétés** : Utiliser `aria-expanded`, `aria-selected`, `aria-current`, etc.

---

## 2. Composants Spécifiques

### 2.1 Formulaires

#### Bonnes pratiques
- Associer chaque `<input>` avec un `<label>` explicite
- Utiliser `fieldset` et `legend` pour grouper les champs liés
- Indiquer les champs obligatoires avec `required` et un indicateur visuel
- Fournir des instructions claires avant le formulaire
- Valider en temps réel avec des messages d'erreur accessibles

#### Exemple
```html
<form>
  <fieldset>
    <legend>Informations personnelles</legend>
    
    <div class="form-group">
      <label for="prenom">Prénom <span aria-label="requis">*</span></label>
      <input type="text" id="prenom" name="prenom" required aria-required="true">
      <span id="prenom-error" class="error" role="alert"></span>
    </div>
    
    <div class="form-group">
      <label for="date-naissance">Date de naissance (JJ/MM/AAAA)</label>
      <input type="date" id="date-naissance" name="date-naissance" aria-describedby="date-help">
      <span id="date-help" class="help-text">Format attendu : jour/mois/année</span>
    </div>
  </fieldset>
</form>
```

### 2.2 Navigation et Menus

#### Structure
```html
<nav aria-label="Navigation principale">
  <ul>
    <li><a href="/" aria-current="page">Accueil</a></li>
    <li><a href="/personnes">Personnes</a></li>
    <li><a href="/recherche">Recherche</a></li>
  </ul>
</nav>
```

#### Menu déroulant accessible
```html
<div class="dropdown">
  <button aria-expanded="false" aria-controls="menu-actions" aria-haspopup="true">
    Actions
  </button>
  <ul id="menu-actions" hidden>
    <li><a href="/ajouter">Ajouter une personne</a></li>
    <li><a href="/importer">Importer GEDCOM</a></li>
  </ul>
</div>
```

### 2.3 Tableaux de Données

#### Structure sémantique
```html
<table>
  <caption>Liste des personnes dans la base de données</caption>
  <thead>
    <tr>
      <th scope="col">Nom</th>
      <th scope="col">Prénom</th>
      <th scope="col">Date de naissance</th>
      <th scope="col">Actions</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">Dupont</th>
      <td>Jean</td>
      <td>15/03/1950</td>
      <td><a href="/personne/123">Voir détails</a></td>
    </tr>
  </tbody>
</table>
```

### 2.4 Arbres Généalogiques Graphiques

L'arbre généalogique est un composant central et complexe. Voici les recommandations spécifiques :

#### Alternatives accessibles
- **Vue texte** : Offrir une vue textuelle de l'arbre en complément de la vue graphique
- **Navigation au clavier** : Permettre la navigation dans l'arbre avec les flèches du clavier
- **Annonces ARIA** : Utiliser `aria-live` pour annoncer les changements dynamiques

#### Exemple de structure
```html
<div role="tree" aria-label="Arbre généalogique de Jean Dupont">
  <div role="treeitem" aria-expanded="true" aria-level="1">
    <span>Jean Dupont (1950-2020)</span>
    <div role="group">
      <div role="treeitem" aria-level="2" aria-expanded="false">
        <span>Marie Dupont (née Martin) (1925-2010) - Mère</span>
      </div>
      <div role="treeitem" aria-level="2" aria-expanded="false">
        <span>Pierre Dupont (1920-2005) - Père</span>
      </div>
    </div>
  </div>
</div>

<!-- Vue alternative textuelle -->
<details>
  <summary>Vue textuelle de l'arbre</summary>
  <ul>
    <li>Jean Dupont (1950-2020)
      <ul>
        <li>Mère : Marie Dupont (née Martin) (1925-2010)</li>
        <li>Père : Pierre Dupont (1920-2005)</li>
      </ul>
    </li>
  </ul>
</details>
```

### 2.5 Modales et Boîtes de Dialogue

#### Gestion du focus
```javascript
// Exemple de gestion du focus dans une modale
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  const focusableElements = modal.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];
  
  modal.setAttribute('aria-hidden', 'false');
  modal.removeAttribute('hidden');
  firstElement.focus();
  
  // Piège au clavier dans la modale
  modal.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModal(modalId);
    }
    if (e.key === 'Tab') {
      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    }
  });
}
```

---

## 3. API REST Accessible

### Documentation de l'API
- **OpenAPI/Swagger** : Documenter tous les endpoints avec des descriptions claires
- **Messages d'erreur** : Fournir des messages d'erreur descriptifs et des codes HTTP appropriés
- **Pagination** : Implémenter la pagination pour éviter les réponses trop volumineuses

### Exemple de structure de réponse
```json
{
  "success": true,
  "data": {
    "id": 123,
    "nom": "Dupont",
    "prenom": "Jean"
  },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100
  },
  "errors": []
}
```

---

### Tests Manuels

#### Checklist de vérification
- [ ] Navigation complète au clavier sans souris
- [ ] Test avec un lecteur d'écran (NVDA, JAWS, VoiceOver)
- [ ] Vérification du contraste avec un outil dédié
- [ ] Test avec un zoom à 200%
- [ ] Désactivation de CSS pour vérifier la structure HTML
- [ ] Test sur différents navigateurs et appareils

#### Lecteurs d'écran recommandés
- **Windows** : NVDA (gratuit), JAWS
- **macOS** : VoiceOver (intégré)
- **Linux** : Orca
- **Mobile** : TalkBack (Android), VoiceOver (iOS)

---

## 5. Bonnes Pratiques de Développement

### Code Review
- Inclure l'accessibilité dans la checklist de code review
- Vérifier les attributs ARIA et les labels
- Tester la navigation au clavier

### Documentation
- Documenter les composants personnalisés et leur accessibilité
- Maintenir une liste des raccourcis clavier

### Formation
- Former l'équipe aux principes d'accessibilité
- Effectuer des audits réguliers

---

## Contact et Support

Pour toute question ou suggestion concernant l'accessibilité, veuillez contacter l'équipe de développement ou ouvrir une issue sur le dépôt GitHub.

**Dernière mise à jour** : Octobre 2025
