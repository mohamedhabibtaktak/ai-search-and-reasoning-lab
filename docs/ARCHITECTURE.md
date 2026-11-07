# Architecture

## Principes
- **Séparation en couches** : domaine (logique pure, sans I/O) → CLI (présentation) ; le domaine ne dépend jamais du CLI.
- **Zéro dépendance obligatoire** ; matplotlib chargé paresseusement, uniquement pour dessiner.
- **Entrées/sorties injectables** (`Console`) → toute l'interface est testable sans terminal.
- **Erreurs métier typées** (`AppError`) : affichées proprement, jamais de trace Python à l'utilisateur.
- **Ouvert/fermé** : un nouvel algorithme = une fonction + une entrée dans `ALGORITHMS`.
- **Déterminisme** : successeurs triés, départage FIFO dans les files de priorité → traces reproductibles.

```
src/ia_app/
├── common/
│   ├── errors.py        AppError, KnowledgeBaseError, GraphError, MissingHeuristicError, StorageError
│   └── jsonio.py        écriture atomique, messages d'erreur lisibles
├── expert/              ── MODULE 1 (domaine)
│   ├── models.py        Rule, KnowledgeBase, parse_rule (validation, noms uniques)
│   ├── inference.py     TraceEvent, InferenceResult
│   ├── forward.py       chaînage avant (cycles de tir, point fixe)
│   ├── backward.py      chaînage arrière (DFS sur les règles, détection de cycles, mémoïsation sûre)
│   ├── storage.py · samples.py
├── search/              ── MODULE 2 (domaine)
│   ├── graph.py         Graph (arcs ≥ 0, h, début/but), analyse admissible/consistante
│   ├── algorithms/
│   │   ├── base.py        Step, SearchResult, Recorder (trace + compteurs)
│   │   ├── uninformed.py  BFS, DFS, DLS, IDS, UCS
│   │   ├── informed.py    Greedy, A*, IDA*, Hill climbing
│   │   └── __init__.py    registre ALGORITHMS + run_search (validation)
│   ├── viz.py           matplotlib (placement par forces) + export DOT + frames par étape
│   ├── storage.py · samples.py
├── gui/                 ── PRÉSENTATION (Tkinter, stdlib)
│   ├── app.py           fenêtre, menu Module, onglets · launch() gère l'absence d'écran
│   ├── expert_tab.py · search_tab.py
│   ├── graph_canvas.py  dessin interactif (arcs de Bézier, glisser, Maj+glisser, clic droit)
│   ├── playback.py      Player (précédent/suivant), indépendant de Tk
│   ├── dialogs.py       dialogues + @guarded (AppError → boîte d'erreur)
│   └── theme.py         palette sobre, une seule couleur d'accent
└── cli/                 ── PRÉSENTATION (console)
    ├── console.py       I/O injectables, saisies validées (int/float/confirm/pick)
    ├── menu.py          run_menu : boucle générique + capture des AppError
    ├── expert_cli.py · search_cli.py · main.py
tests/                   108 tests (domaine, propriétés aléatoires, CLI scripté, viz, GUI)
data/                    exemples JSON (animaux, Roumanie)
```

**Le domaine est partagé** entre CLI, GUI et visualisation : `search/layout.py` (placement), `search/formatting.py`
(libellés d'étapes). La GUI n'ajoute aucune logique métier : changer un algorithme ne touche que `search/algorithms/`.

## Choix de conception notables
| Sujet | Décision | Pourquoi |
|---|---|---|
| Trace des algorithmes | chaque algo renvoie une liste de `Step` immuables | affichage texte, pas à pas et images utilisent la même source |
| Chaînage arrière | échecs dus à un cycle **non mémoïsés** | un échec dépendant du contexte pourrait être faux ailleurs |
| A* | `best_g` + entrées obsolètes ignorées, réouverture autorisée | correct même si h est admissible mais non consistante |
| Hill climbing | amélioration **stricte** de h exigée | évite les boucles sur plateau, échec expliqué à l'utilisateur |
| DLS / IDS | cycles coupés le long du chemin courant ; IDS borné à \|V\|−1 | terminaison garantie, « cutoff » distingué de « échec » |
| GUI | Tkinter + dialogues remplaçables dans les tests | zéro dépendance ; tests sans clic réel |
| Positions des nœuds | coordonnées relatives (0..1) | redimensionnement et glisser sans recalcul |
| Coûts | négatifs, NaN, infinis, boucles refusés | hypothèses de UCS/A* respectées |
| Heuristique | exigée sur tous les sommets pour un algo informé ; saisie guidée | message clair plutôt qu'un crash en cours de route |
