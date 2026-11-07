# Script de la vidéo de démonstration (≈ 4 min)

**Préparation** : `python run.py --gui` (ou terminal agrandi + `python run.py` pour la version console).
En GUI : onglet « Systèmes experts » → boutons Lancer / Suivant ; onglet « Recherche » → « Exemple Roumanie », choisir l'algorithme, Lancer, ▶ pas à pas, puis « Comparer tout ». Montrer aussi la création d'un graphe à la souris (double-clic, Maj+glisser).

## 1. Menu principal (10 s)
Montrer les 3 options.

## 2. Systèmes experts (≈ 1 min 30)
1. `1` → afficher la base (option 1) : faits + règles « SI … ALORS … ».
2. Objectif : `2` → `poils` → message « déjà présent dans la base de faits ». Puis `2` → `guepard`.
3. **Chaînage avant** (méthode 1) : `4`, avancer avec Entrée — voir R1 → R5 → R9.
4. **Chaînage arrière** : `3` → arrière, `4` — trace indentée (buts / sous-buts).
5. Objectif impossible : `2` → `tigre` → échec expliqué.
6. Personnaliser : ajouter `rayures_noires` puis relancer `tigre` → succès (objectif changé sans relancer l'appli).
7. Sauvegarder la base (JSON).

## 3. Algorithmes de recherche (≈ 2 min 30)
1. `2` → `8` (exemple Roumanie) → `1` (affichage du graphe : h, coûts, ▶ / ★).
2. `3` : **non informée → BFS** (chemin 450) puis **UCS** (chemin optimal 418).
3. `3` : **informée → Greedy** (450) puis **A\*** pas à pas (418) : frontière et f = g + h.
4. `4` : tableau de comparaison (★ optimal).
5. `5` → PNG : montrer le chemin surligné ; option « image par étape ».
6. Cas limites : construire un petit graphe sans chemin → message « Aucun chemin trouvé » ; heuristique non admissible → avertissement.
7. Quitter (`3`).

## Commandes utiles pour la démo
`python -m pytest -q` (95 tests) · `python run.py --no-color`
