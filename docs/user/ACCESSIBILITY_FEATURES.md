# Fonctionnalités d'Accessibilité - Guide Utilisateur

## Bienvenue

GeneWeb Python s'engage à être accessible à tous les utilisateurs, quelles que soient leurs capacités. Ce guide décrit les fonctionnalités d'accessibilité disponibles et comment les utiliser efficacement.

---

## Table des Matières

1. [Navigation au Clavier](#navigation-au-clavier)
2. [Lecteurs d'Écran](#lecteurs-décran)
3. [Paramètres d'Affichage](#paramètres-daffichage)
4. [Alternatives Textuelles](#alternatives-textuelles)
5. [Raccourcis Clavier](#raccourcis-clavier)
6. [Support et Assistance](#support-et-assistance)

---

## Navigation au Clavier

GeneWeb Python peut être utilisé entièrement au clavier, sans souris.

### Touches de Base

| Touche | Action |
|--------|--------|
| **Tab** | Passer à l'élément suivant |
| **Shift + Tab** | Revenir à l'élément précédent |
| **Entrée** | Activer un bouton ou un lien |
| **Espace** | Cocher/décocher une case, activer un bouton |
| **Échap** | Fermer une boîte de dialogue ou un menu |
| **Flèches** | Naviguer dans les menus et les arbres |

### Navigation dans les Pages

#### Liens d'Évitement
Au début de chaque page, vous trouverez des liens d'évitement invisibles (visibles au focus) pour :
- Aller directement au contenu principal
- Aller directement à la navigation
- Aller directement au formulaire de recherche

**Comment les utiliser :**
1. Chargez une page
2. Appuyez immédiatement sur **Tab**
3. Appuyez sur **Entrée** pour sauter vers la section désirée

#### Indicateurs de Focus
Tous les éléments interactifs ont un indicateur visuel clair lorsqu'ils sont en focus (contour bleu épais).

---

## Lecteurs d'Écran

GeneWeb Python est optimisé pour les lecteurs d'écran les plus populaires.

### Lecteurs d'Écran Compatibles

| Système | Lecteur d'Écran | Statut |
|---------|-----------------|--------|
| Windows | NVDA | ✅ Entièrement supporté |
| Windows | JAWS | ✅ Entièrement supporté |
| macOS | VoiceOver | ✅ Entièrement supporté |
| Linux | Orca | ✅ Entièrement supporté |
| iOS | VoiceOver | ✅ Entièrement supporté |
| Android | TalkBack | ✅ Entièrement supporté |

### Régions Principales

Chaque page est structurée avec des régions ARIA clairement définies :

- **Navigation principale** (`<nav>`) - Menu de navigation du site
- **Contenu principal** (`<main>`) - Contenu principal de la page
- **Informations complémentaires** (`<aside>`) - Informations contextuelles
- **Pied de page** (`<footer>`) - Informations de pied de page

**Conseil :** Utilisez les commandes de navigation par région de votre lecteur d'écran pour vous déplacer rapidement.

### Titres Structurés

Toutes les pages utilisent une hiérarchie de titres logique (H1 → H2 → H3...) pour faciliter la navigation.

**Avec NVDA/JAWS :**
- **H** : Passer au titre suivant
- **1-6** : Passer au titre de niveau spécifique
- **Insert + F6** : Liste de tous les titres

---

## Paramètres d'Affichage

### Zoom

GeneWeb Python fonctionne correctement avec un zoom jusqu'à **200%**.

**Comment zoomer :**
- **Navigateur** : `Ctrl` + `+` (Windows/Linux) ou `Cmd` + `+` (macOS)
- **Dézoomer** : `Ctrl` + `-` ou `Cmd` + `-`
- **Réinitialiser** : `Ctrl` + `0` ou `Cmd` + `0`

### Modes de Contraste Élevé

L'application respecte les préférences système de contraste élevé.

**Windows :**
1. Paramètres > Facilité d'accès > Contraste élevé
2. Activez un thème à contraste élevé
3. GeneWeb s'adaptera automatiquement

**macOS :**
1. Préférences Système > Accessibilité > Affichage
2. Activez "Augmenter le contraste"

### Réduction des Animations

Si vous êtes sensible au mouvement ou préférez une interface statique :

**Windows 10/11 :**
1. Paramètres > Facilité d'accès > Affichage
2. Désactivez "Afficher les animations dans Windows"

**macOS :**
1. Préférences Système > Accessibilité > Affichage
2. Activez "Réduire les animations"

GeneWeb respectera automatiquement ce paramètre.

### Taille de Police

Vous pouvez augmenter la taille de police :

1. Utilisez le zoom du navigateur (recommandé)
2. Ou modifiez les paramètres dans votre profil utilisateur :
   - Accédez à **Paramètres > Affichage**
   - Sélectionnez une taille de police : Petite, Moyenne (défaut), Grande, Très grande

---

## Alternatives Textuelles

### Arbres Généalogiques

Chaque arbre généalogique graphique dispose d'une **vue textuelle alternative**.

**Comment y accéder :**
1. Sur la page de l'arbre, cherchez le bouton **"Vue textuelle"** ou **"Afficher en mode texte"**
2. Cliquez ou appuyez sur **Entrée**
3. L'arbre sera affiché sous forme de liste structurée

**Exemple de vue textuelle :**
```
Jean Dupont (1950-2020)
├── Mère : Marie Dupont (née Martin) (1925-2010)
│   ├── Grand-mère maternelle : Anne Martin (1900-1985)
│   └── Grand-père maternel : Louis Martin (1898-1980)
└── Père : Pierre Dupont (1920-2005)
    ├── Grand-mère paternelle : Claire Dupont (1895-1975)
    └── Grand-père paternel : Henri Dupont (1892-1970)
```

### Images

Toutes les images ont des descriptions textuelles alternatives :
- **Photos de famille** : Décrites avec les personnes présentes et le contexte
- **Icônes** : Décrites avec leur fonction
- **Graphiques** : Accompagnés de descriptions détaillées

---

## Raccourcis Clavier

### Raccourcis Globaux

| Raccourci | Action |
|-----------|--------|
| **Alt + S** | Aller au formulaire de recherche |
| **Alt + M** | Ouvrir le menu principal |
| **Alt + H** | Retour à l'accueil |
| **/** | Focus sur la recherche rapide |

### Navigation dans l'Arbre Généalogique

| Raccourci | Action |
|-----------|--------|
| **←** | Naviguer vers le parent/ancêtre gauche |
| **→** | Naviguer vers le parent/ancêtre droit |
| **↑** | Remonter d'une génération |
| **↓** | Descendre d'une génération |
| **Entrée** | Afficher les détails de la personne sélectionnée |
| **T** | Basculer entre vue graphique et texte |

### Édition et Formulaires

| Raccourci | Action |
|-----------|--------|
| **Ctrl + S** | Sauvegarder (dans les formulaires) |
| **Échap** | Annuler et fermer |
| **Ctrl + Z** | Annuler la dernière modification |

### Désactiver les Raccourcis

Si les raccourcis interfèrent avec votre lecteur d'écran ou d'autres outils :

1. Allez dans **Paramètres > Accessibilité**
2. Décochez **"Activer les raccourcis clavier"**

---

## Fonctionnalités Spécifiques

### Recherche Accessible

Le formulaire de recherche est optimisé pour l'accessibilité :

1. **Suggestions automatiques** : Annoncées aux lecteurs d'écran
2. **Navigation au clavier** : Utilisez **↑** et **↓** pour parcourir les suggestions
3. **Filtres clairs** : Chaque filtre a un label explicite

### Formulaires d'Édition

#### Validation en Temps Réel
- Les erreurs sont annoncées immédiatement
- Des suggestions de correction sont fournies
- Les champs obligatoires sont clairement indiqués

#### Assistance Contextuelle
- Chaque champ complexe a une aide contextuelle (icône **?**)
- Accessible au clavier et lecteur d'écran

### Notifications et Alertes

Toutes les notifications sont :
- Visuellement distinctes avec des icônes et couleurs
- Annoncées aux lecteurs d'écran via des régions `aria-live`
- Persistantes jusqu'à ce que vous les fermiez (pas de disparition automatique pour les messages importants)

**Types de notifications :**
- ✅ **Succès** (vert) : Opération réussie
- ℹ️ **Information** (bleu) : Information contextuelle
- ⚠️ **Avertissement** (orange) : Attention requise
- ❌ **Erreur** (rouge) : Action nécessaire


## Support et Assistance

### Signaler un Problème d'Accessibilité

Si vous rencontrez une difficulté d'accessibilité :

1. **GitHub Issues** : [https://github.com/EpitechPGE45-2025/G-ING-900-PAR-9-1-legacy-1/issues](https://github.com/EpitechPGE45-2025/G-ING-900-PAR-9-1-legacy-1/issues)
   - Sélectionnez le label "accessibility"
   
**Dernière mise à jour :** Octobre 2025

Pour toute question ou suggestion, n'hésitez pas à nous contacter !
