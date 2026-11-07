# Skills retenus

## Dépôt `pbakaus/impeccable` (analysé)
Impeccable est un jeu de **skills de design d'interface** pour agents de code (commandes `critique`, `audit`,
`polish`, `harden`, `clarify`, `shape`, `init`…, plus un détecteur de « AI slop »). Il cible surtout des interfaces
web ; ce projet est un CLI, donc seuls ses **principes** sont transposés (le skill n'est pas installé) :

| Commande Impeccable | Application dans ce projet |
|---|---|
| `shape` / `init` | avant de coder : extraction des tâches (`TASKS.md`), contraintes et hypothèses |
| `clarify` | libellés de menus explicites, messages d'erreur qui disent quoi faire (« Format attendu : … ») |
| `harden` | cas limites : saisies invalides redemandées, JSON corrompu, graphe vide, EOF/Ctrl-C |
| `audit` / `critique` | relecture finale : lisibilité du graphe (placement par forces, nœuds en points, légende) |
| `polish` | symboles et couleurs cohérents (✔ ✘ ⚠), désactivables (`--no-color`, `NO_COLOR`) |
| anti-slop | pas de gabarit générique : visualisation dédiée au problème (chemin, frontière, explorés) |

## Skills d'ingénierie utilisés
`system-design` / `architecture` (couches, registre) · `test-driven-development` + `testing-strategy`
(tests de propriétés) · `systematic-debugging` (5 échecs de tests analysés avant correction) ·
`verification-before-completion` (aucune affirmation sans exécution) · `documentation` (README, docs/) ·
`code-review` (relecture finale).

## Compétences techniques requises
Chaînage avant/arrière · recherche dans les espaces d'états (BFS/DFS/DLS/IDS/UCS/Greedy/A*/IDA*/Hill) ·
heuristiques admissibles/consistantes · structures de données (deque, heap) · tests pytest · packaging Python ·
visualisation (matplotlib, Graphviz DOT).
