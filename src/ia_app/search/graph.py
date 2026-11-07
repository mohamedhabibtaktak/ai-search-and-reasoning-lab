"""Graphe orienté et pondéré avec heuristiques, état initial et état objectif."""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from typing import Any

from ..common.errors import GraphError, MissingHeuristicError


def format_cost(value: float) -> str:
    """12.0 -> '12' ; 2.5 -> '2.5'."""
    return str(int(value)) if float(value).is_integer() else f"{value:g}"


@dataclass
class HeuristicReport:
    """Qualité de l'heuristique : admissible (h <= coût réel) et consistante (h(u) <= c(u,v)+h(v))."""

    admissible: bool = True
    consistent: bool = True
    goal_is_zero: bool = True
    problems: list[str] = field(default_factory=list)


def _check_name(name: str) -> str:
    name = str(name).strip()
    if not name:
        raise GraphError("Le nom d'un sommet ne peut pas être vide.")
    return name


def _check_number(value: float, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise GraphError(f"{label} doit être un nombre.") from None
    if math.isnan(number) or math.isinf(number):
        raise GraphError(f"{label} doit être un nombre fini.")
    if number < 0:
        raise GraphError(f"{label} ne peut pas être négatif (reçu {format_cost(number)}).")
    return number


class Graph:
    def __init__(self) -> None:
        self._adj: dict[str, dict[str, float]] = {}
        self._h: dict[str, float] = {}
        self.start: str | None = None
        self.goal: str | None = None

    # --- sommets -----------------------------------------------------
    @property
    def vertices(self) -> list[str]:
        return list(self._adj)

    def has_vertex(self, name: str) -> bool:
        return name.strip() in self._adj

    def _require(self, name: str) -> str:
        name = _check_name(name)
        if name not in self._adj:
            raise GraphError(f"Sommet inconnu : « {name} ».")
        return name

    def add_vertex(self, name: str) -> bool:
        name = _check_name(name)
        if name in self._adj:
            return False
        self._adj[name] = {}
        return True

    def remove_vertex(self, name: str) -> None:
        name = self._require(name)
        del self._adj[name]
        for targets in self._adj.values():
            targets.pop(name, None)
        self._h.pop(name, None)
        if self.start == name:
            self.start = None
        if self.goal == name:
            self.goal = None

    # --- arcs --------------------------------------------------------
    def add_edge(self, src: str, dst: str, cost: float, *, create_missing: bool = False) -> None:
        """Ajoute (ou remplace) l'arc orienté src -> dst. Coût >= 0, pas de boucle."""
        src, dst = _check_name(src), _check_name(dst)
        if src == dst:
            raise GraphError("Les boucles (arc d'un sommet vers lui-même) ne sont pas autorisées.")
        value = _check_number(cost, "Le coût")
        if not create_missing:
            self._require(src)
            self._require(dst)
        self.add_vertex(src)
        self.add_vertex(dst)
        self._adj[src][dst] = value

    def remove_edge(self, src: str, dst: str) -> None:
        src, dst = self._require(src), self._require(dst)
        if dst not in self._adj[src]:
            raise GraphError(f"Il n'existe pas d'arc {src} → {dst}.")
        del self._adj[src][dst]

    def successors(self, vertex: str) -> list[tuple[str, float]]:
        """Successeurs triés par nom : ordre d'exploration déterministe."""
        return sorted(self._adj[self._require(vertex)].items())

    def edges(self) -> list[tuple[str, str, float]]:
        return [(u, v, c) for u, targets in self._adj.items() for v, c in sorted(targets.items())]

    def path_cost(self, path: list[str]) -> float:
        total = 0.0
        for u, v in zip(path, path[1:]):
            if v not in self._adj.get(u, {}):
                raise GraphError(f"Chemin invalide : pas d'arc {u} → {v}.")
            total += self._adj[u][v]
        return total

    # --- heuristique, état initial / objectif ------------------------
    def set_heuristic(self, vertex: str, value: float) -> None:
        self._h[self._require(vertex)] = _check_number(value, "L'heuristique")

    def heuristic(self, vertex: str) -> float:
        if vertex not in self._h:
            raise MissingHeuristicError(f"Heuristique manquante pour « {vertex} ».")
        return self._h[vertex]

    @property
    def heuristics(self) -> dict[str, float]:
        return dict(self._h)

    def missing_heuristics(self) -> list[str]:
        return [v for v in self._adj if v not in self._h]

    def set_start(self, vertex: str) -> None:
        self.start = self._require(vertex)

    def set_goal(self, vertex: str) -> None:
        self.goal = self._require(vertex)

    def clear(self) -> None:
        self._adj.clear()
        self._h.clear()
        self.start = self.goal = None

    # --- analyse de l'heuristique -----------------------------------
    def true_costs_to(self, target: str) -> dict[str, float]:
        """Coût optimal réel de chaque sommet vers `target` (Dijkstra sur le graphe inversé)."""
        reverse: dict[str, list[tuple[str, float]]] = {v: [] for v in self._adj}
        for u, v, c in self.edges():
            reverse[v].append((u, c))
        dist = {target: 0.0}
        heap = [(0.0, target)]
        while heap:
            d, node = heapq.heappop(heap)
            if d > dist.get(node, math.inf):
                continue
            for prev, c in reverse[node]:
                nd = d + c
                if nd < dist.get(prev, math.inf):
                    dist[prev] = nd
                    heapq.heappush(heap, (nd, prev))
        return dist

    def check_heuristic(self) -> HeuristicReport:
        report = HeuristicReport()
        if self.goal is None:
            return report
        if self._h.get(self.goal, 0.0) != 0:
            report.goal_is_zero = False
            report.problems.append(f"h({self.goal}) devrait valoir 0 pour l'état objectif.")
        for vertex, true_cost in self.true_costs_to(self.goal).items():
            if vertex in self._h and self._h[vertex] > true_cost + 1e-9:
                report.admissible = False
                report.problems.append(
                    f"Non admissible : h({vertex}) = {format_cost(self._h[vertex])} "
                    f"> coût réel {format_cost(true_cost)}.")
        for u, v, c in self.edges():
            if u in self._h and v in self._h and self._h[u] > c + self._h[v] + 1e-9:
                report.consistent = False
                report.problems.append(
                    f"Non consistante : h({u}) = {format_cost(self._h[u])} > "
                    f"c({u},{v}) + h({v}) = {format_cost(c + self._h[v])}.")
        return report

    # --- (dé)sérialisation ------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {
            "vertices": self.vertices,
            "edges": [{"from": u, "to": v, "cost": c} for u, v, c in self.edges()],
            "heuristics": dict(self._h),
            "start": self.start,
            "goal": self.goal,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Graph":
        graph = cls()
        try:
            for name in data.get("vertices", []):
                graph.add_vertex(name)
            for edge in data.get("edges", []):
                graph.add_edge(edge["from"], edge["to"], edge["cost"])
            for name, value in dict(data.get("heuristics", {})).items():
                graph.set_heuristic(name, value)
            if data.get("start"):
                graph.set_start(data["start"])
            if data.get("goal"):
                graph.set_goal(data["goal"])
        except (KeyError, TypeError, AttributeError, ValueError):
            raise GraphError(
                "Graphe invalide : attendu vertices, edges [{from,to,cost}], heuristics, start, goal."
            ) from None
        return graph
