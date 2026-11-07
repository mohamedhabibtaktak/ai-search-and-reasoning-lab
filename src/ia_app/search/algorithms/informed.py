"""Recherches informées (heuristiques) : Greedy best-first, A*, IDA*, Hill climbing."""
from __future__ import annotations

import heapq
import math

from ..graph import Graph, format_cost
from .base import Recorder, SearchResult, fmt_list, rebuild_path


def _best_first(name: str, graph: Graph, start: str, goal: str, *, use_g: bool, use_h: bool,
                reopen: bool) -> SearchResult:
    """Noyau commun Greedy / A* : priorité f = (g si use_g) + (h si use_h)."""
    rec = Recorder()
    h = graph.heuristic

    def priority(g: float, node: str) -> float:
        return (g if use_g else 0.0) + (h(node) if use_h else 0.0)

    def label(g: float, node: str) -> str:
        if use_g and use_h:
            return f"{node}[f={format_cost(priority(g, node))}]"
        return f"{node}[h={format_cost(h(node))}]"

    counter = 0
    heap: list[tuple[float, int, str, float]] = [(priority(0.0, start), counter, start, 0.0)]
    best = {start: 0.0}
    parent: dict[str, str | None] = {start: None}
    explored: list[str] = []
    rec.generated = 1

    def snap(action: str, node: str | None, note: str) -> None:
        live = sorted(e for e in heap if e[3] <= best[e[2]])
        rec.add(action, node, [e[2] for e in live], explored, note, labels=[label(e[3], e[2]) for e in live])

    snap("init", None, "Frontière initiale = état initial.")
    while heap:
        _, _, node, g = heapq.heappop(heap)
        if g > best[node]:
            continue  # entrée obsolète
        explored.append(node)
        rec.expanded += 1
        detail = f"g={format_cost(g)}, h={format_cost(h(node))}" if use_g else f"h={format_cost(h(node))}"
        if node == goal:
            snap("goal", node, f"« {node} » est l'objectif ({detail}).")
            return rec.result(name, graph, rebuild_path(parent, goal))
        added = []
        for nxt, cost in graph.successors(node):
            new_g = g + cost
            better = new_g < best.get(nxt, math.inf) if reopen else nxt not in best
            if better:
                best[nxt] = new_g
                parent[nxt] = node
                counter += 1
                heapq.heappush(heap, (priority(new_g, nxt), counter, nxt, new_g))
                added.append(label(new_g, nxt))
                rec.generated += 1
        snap("expand", node, f"Développe « {node} » ({detail}). Ajoutés : {fmt_list(added)}.")
    snap("stop", None, "Frontière vide.")
    return rec.result(name, graph, None)


def greedy(graph: Graph, start: str, goal: str, **_) -> SearchResult:
    """Meilleur d'abord glouton : f(n) = h(n). Rapide, ni complet ni optimal en général."""
    return _best_first("Greedy (meilleur d'abord)", graph, start, goal, use_g=False, use_h=True, reopen=False)


def a_star(graph: Graph, start: str, goal: str, **_) -> SearchResult:
    """A* : f(n) = g(n) + h(n). Optimal si h est admissible (réouverture gérée si h non consistante)."""
    return _best_first("A*", graph, start, goal, use_g=True, use_h=True, reopen=True)


def ida_star(graph: Graph, start: str, goal: str, **_) -> SearchResult:
    """IDA* : A* en mémoire linéaire, par seuils croissants sur f = g + h."""
    rec = Recorder()
    h = graph.heuristic
    rec.generated = 1
    path = [start]
    on_path = {start}
    threshold = h(start)

    def search(node: str, g: float) -> tuple[bool, float]:
        """Renvoie (trouvé, plus petit f dépassant le seuil)."""
        f = g + h(node)
        rec.expanded += 1
        if f > threshold + 1e-12:
            rec.add("cutoff", node, (), path, f"f({node}) = {format_cost(f)} > seuil {format_cost(threshold)} : coupure.")
            return False, f
        if node == goal:
            rec.add("goal", node, (), path, f"Objectif atteint, f = {format_cost(f)}.")
            return True, f
        rec.add("expand", node, (), path,
                f"g={format_cost(g)}, h={format_cost(h(node))}, f={format_cost(f)} ≤ seuil {format_cost(threshold)}.")
        smallest = math.inf
        for nxt, cost in graph.successors(node):
            if nxt in on_path:
                continue
            rec.generated += 1
            path.append(nxt)
            on_path.add(nxt)
            found, value = search(nxt, g + cost)
            if found:
                return True, value
            smallest = min(smallest, value)
            path.pop()
            on_path.discard(nxt)
        return False, smallest

    while True:
        rec.add("info", None, (), (), f"=== Seuil f = {format_cost(threshold)} ===")
        found, value = search(start, 0.0)
        if found:
            return rec.result("IDA*", graph, list(path))
        if math.isinf(value):
            rec.add("stop", None, (), (), "Aucun sommet au-delà du seuil : espace épuisé.")
            return rec.result("IDA*", graph, None)
        threshold = value


def hill_climbing(graph: Graph, start: str, goal: str, **_) -> SearchResult:
    """Escalade (steepest-ascent) : se déplace vers le successeur de plus petit h, sans retour arrière."""
    rec = Recorder()
    h = graph.heuristic
    path = [start]
    explored: list[str] = []
    rec.generated = 1
    rec.add("init", None, (), explored, f"Départ en « {start} » (h={format_cost(h(start))}).")
    current = start
    while True:
        explored.append(current)
        rec.expanded += 1
        if current == goal:
            rec.add("goal", current, (), explored, f"« {current} » est l'objectif.")
            return rec.result("Hill climbing (escalade)", graph, path)
        options = [(h(n), n) for n, _ in graph.successors(current) if n not in path]
        rec.generated += len(options)
        labels = [f"{n}[h={format_cost(v)}]" for v, n in sorted(options)]
        if not options:
            rec.add("stop", current, (), explored, f"Impasse en « {current} » : aucun successeur non visité.")
            return rec.result("Hill climbing (escalade)", graph, None,
                              "Échec : impasse (aucun successeur utilisable).")
        best_h, best = min(options)
        if best_h >= h(current):
            rec.add("stop", current, [n for _, n in sorted(options)], explored,
                    f"Aucun successeur n'améliore h={format_cost(h(current))} (meilleur : {best}, h={format_cost(best_h)}) : "
                    "minimum local ou plateau.", labels=labels)
            return rec.result("Hill climbing (escalade)", graph, None,
                              "Échec : minimum local / plateau (l'algorithme ne revient jamais en arrière).")
        rec.add("expand", current, [n for _, n in sorted(options)], explored,
                f"Candidats : {fmt_list(labels)} → choisit « {best} ».", labels=labels)
        path.append(best)
        current = best
