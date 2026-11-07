"""Registre des algorithmes : ajouter un algorithme = une fonction + une ligne ici (principe ouvert/fermé)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ...common.errors import GraphError, MissingHeuristicError
from ..graph import Graph
from .base import SearchResult, Step
from .informed import a_star, greedy, hill_climbing, ida_star
from .uninformed import bfs, dfs, dls, ids, ucs


@dataclass(frozen=True)
class AlgorithmSpec:
    key: str
    label: str
    informed: bool
    run: Callable[..., SearchResult]
    params: tuple[str, ...] = ()   # paramètres à demander à l'utilisateur (ex. limite)
    summary: str = ""


ALGORITHMS: dict[str, AlgorithmSpec] = {s.key: s for s in [
    AlgorithmSpec("bfs", "BFS — parcours en largeur", False, bfs,
                  summary="FIFO ; optimal en nombre d'arcs"),
    AlgorithmSpec("dfs", "DFS — parcours en profondeur", False, dfs,
                  summary="LIFO ; peu de mémoire, non optimal"),
    AlgorithmSpec("dls", "DLS — profondeur limitée", False, dls, ("limit",),
                  "DFS borné par une limite"),
    AlgorithmSpec("ids", "IDS — approfondissement itératif", False, ids,
                  summary="DLS à limites croissantes"),
    AlgorithmSpec("ucs", "UCS — coût uniforme", False, ucs,
                  summary="optimal en coût (g)"),
    AlgorithmSpec("greedy", "Greedy — meilleur d'abord glouton", True, greedy,
                  summary="f = h ; rapide, non optimal"),
    AlgorithmSpec("astar", "A*", True, a_star, summary="f = g + h ; optimal si h admissible"),
    AlgorithmSpec("idastar", "IDA*", True, ida_star, summary="A* en mémoire linéaire"),
    AlgorithmSpec("hill", "Hill climbing — escalade", True, hill_climbing,
                  summary="local, sans retour arrière"),
]}


def algorithms_by_category(informed: bool) -> list[AlgorithmSpec]:
    return [s for s in ALGORITHMS.values() if s.informed == informed]


def run_search(graph: Graph, key: str, **params) -> SearchResult:
    """Valide le graphe puis exécute l'algorithme. Lève GraphError / MissingHeuristicError."""
    spec = ALGORITHMS.get(key)
    if spec is None:
        raise GraphError(f"Algorithme inconnu : « {key} ».")
    if graph.start is None or graph.goal is None:
        raise GraphError("Définissez d'abord l'état initial et l'état objectif.")
    if spec.informed:
        missing = graph.missing_heuristics()
        if missing:
            raise MissingHeuristicError(
                f"Heuristique manquante pour : {', '.join(missing)}. "
                "Définissez h(n) pour tous les sommets (menu « Heuristiques »).")
    try:
        return spec.run(graph, graph.start, graph.goal, **params)
    except ValueError as exc:  # paramètre invalide (ex. limite négative)
        raise GraphError(str(exc)) from None


__all__ = ["ALGORITHMS", "AlgorithmSpec", "SearchResult", "Step", "algorithms_by_category", "run_search"]
