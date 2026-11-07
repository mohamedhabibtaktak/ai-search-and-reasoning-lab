"""Types et utilitaires partagés par tous les algorithmes de recherche."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from ..graph import Graph, format_cost


@dataclass(frozen=True)
class Step:
    """Instantané d'une étape : sommet traité, frontière et sommets déjà explorés."""

    index: int
    action: str                      # "init" | "expand" | "goal" | "skip" | "cutoff" | "info" | "stop"
    current: str | None
    frontier: tuple[str, ...]        # noms (pour la visualisation)
    frontier_labels: tuple[str, ...] # noms + priorité (pour l'affichage texte)
    explored: tuple[str, ...]
    note: str = ""


@dataclass
class SearchResult:
    algorithm: str
    found: bool
    path: list[str] = field(default_factory=list)
    cost: float | None = None
    steps: list[Step] = field(default_factory=list)
    expanded: int = 0                # sommets développés
    generated: int = 0               # sommets générés (ajoutés à la frontière)
    message: str = ""

    @property
    def cost_text(self) -> str:
        return "—" if self.cost is None else format_cost(self.cost)


class Recorder:
    """Enregistre les étapes et les compteurs pendant qu'un algorithme s'exécute."""

    def __init__(self) -> None:
        self.steps: list[Step] = []
        self.expanded = 0
        self.generated = 0

    def add(self, action: str, current: str | None, frontier=(), explored=(), note: str = "",
            labels=None) -> None:
        frontier = tuple(frontier)
        self.steps.append(Step(len(self.steps) + 1, action, current, frontier,
                               tuple(labels) if labels is not None else frontier,
                               tuple(explored), note))

    def result(self, name: str, graph: Graph, path: list[str] | None, message: str = "") -> SearchResult:
        found = path is not None
        return SearchResult(
            algorithm=name, found=found, path=list(path or []),
            cost=graph.path_cost(path) if path else None,
            steps=self.steps, expanded=self.expanded, generated=self.generated,
            message=message or ("Chemin trouvé." if found else "Aucun chemin trouvé."),
        )


def rebuild_path(parent: dict[str, str | None], goal: str) -> list[str]:
    path: list[str] = []
    node: str | None = goal
    while node is not None:
        path.append(node)
        node = parent[node]
    return path[::-1]


def fmt_list(items) -> str:
    items = list(items)
    return ", ".join(items) if items else "∅"


Algorithm = Callable[..., SearchResult]
