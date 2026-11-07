# Tâches extraites du sujet (échéance : dimanche 8 novembre 2026, minuit)

Légende : **[O]** obligatoire · **[B]** bonus mentionné dans le sujet · ✅ réalisé

## Menu principal
- ✅ [O] Menu : 1. Systèmes experts · 2. Algorithmes de recherche · 3. Quitter

## Module 1 — Systèmes experts
- ✅ [O] Afficher la base de faits initiale
- ✅ [O] Afficher les règles « SI conditions ALORS conclusion »
- ✅ [O] Choisir le fait à démontrer ; indiquer s'il est déjà dans la base
- ✅ [O] Choisir chaînage avant / arrière
- ✅ [O] Exécution interactive : étapes présentées progressivement
- ✅ [O] Changer l'objectif sans relancer l'application
- ✅ [B] Ajouter / modifier / supprimer faits et règles
- ✅ [B] Sauvegarder / recharger une base de connaissances

## Module 2 — Algorithmes de recherche
- ✅ [O] Créer les sommets · arcs orientés · coût par arc
- ✅ [O] Définir état initial et état objectif
- ✅ [O] Afficher le graphe (texte ✅ · graphique ✅)
- ✅ [O] Définir h(n) pour les algorithmes informés
- ✅ [O] Choisir la catégorie (non informée / informée) puis l'algorithme (tous ceux du cours)
- ✅ [O] Afficher état initial/objectif, étapes, visités, frontière, chemin, coût total, « aucun chemin »
- ✅ [B] Étape par étape + chemin final surligné dans le graphique
- ✅ [B] Comparaison des algorithmes · sauvegarde du graphe

## Interface
- ✅ [B] Interface graphique (Tkinter) : graphe interactif, exécution pas à pas, chemin surligné
- ✅ Interface console conservée (`python run.py`)

## Livrables
- ✅ Code source organisé et commenté (`src/ia_app/`)
- ✅ README (prérequis, installation, exécution)
- ⏳ **Vidéo de démonstration** → à enregistrer par l'étudiant : script dans `docs/DEMO.md`

## Critères d'évaluation → où c'est couvert
| Critère | Réponse |
|---|---|
| Correction des algorithmes | résultats de référence + 250 graphes aléatoires (complétude, optimalité, validité) |
| Traçabilité de l'inférence | `TraceEvent` typés, indentés par profondeur (arrière), cycles de tir (avant) |
| Graphes, coûts, heuristiques | coûts ≥ 0 validés, h complète exigée, contrôle admissible/consistante |
| Tests et cas particuliers | départ = but, pas de chemin, cycles, arcs à coût 0, plateau, limite DLS, JSON corrompu |
| Interface | menus uniformes, saisies validées, erreurs sans trace Python, mode pas à pas |
| Code / doc / démo | architecture en couches, README, script de démo |

> Hypothèse : la liste exacte des algorithmes « étudiés dans le cours » n'est pas dans le sujet.
> Les 9 algorithmes classiques sont implémentés ; en ajouter un = 1 fonction + 1 ligne dans le registre.
