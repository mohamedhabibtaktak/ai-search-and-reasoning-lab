"""Recherches non informées (aveugles) : BFS, DFS, DLS, IDS, UCS.

Convention : le test de but est effectué à l'extraction (développement) du sommet.
Les successeurs sont parcourus par ordre alphabétique pour des résultats reproductibles.
"""
from __future__ import annotations

import heapq
import math
from collections import deque

from ..graph import Graph, format_cost
from .base import Recorder, SearchResult, fmt_list, rebuild_path


def bfs(graph: Graph, start: str, goal: str, **_) -> SearchResult:
    """Parcours en largeur : FIFO, optimal en nombre d'arcs."""
    rec = Recorder()
    queue = deque([start])
    seen = {start}
    parent: dict[str, str | None] = {start: None}
    explored: list[str] = []
    rec.generated = 1
    rec.add("init", None, queue, explored, "Frontière initiale = état initial.")
    while queue:
        node = queue.popleft()
        explored.append(node)
        rec.expanded += 1
        if node == goal:
            rec.add("goal", node, queue, explored, f"« {node} » est l'état objectif.")
            return rec.result("BFS (largeur)", graph, rebuild_path(parent, goal))
        added = []
        for nxt, _ in graph.successors(node):
            if nxt not in seen:
                seen.add(nxt)
                parent[nxt] = node
                queue.append(nxt)
                added.append(nxt)
                rec.generated += 1
        rec.add("expand", node, queue, explored, f"Ajoutés en fin de file : {fmt_list(added)}.")
    rec.add("stop", None, (), explored, "Frontière vide.")
    return rec.result("BFS (largeur)", graph, None)


def dfs(graph: Graph, start: str, goal: str, **_) -> SearchResult:
    """Parcours en profondeur : LIFO, avec ensemble des explorés (évite les cycles)."""
    rec = Recorder()
    stack: list[tuple[str, str | None]] = [(start, None)]
    parent: dict[str, str | None] = {}
    explored: list[str] = []
    rec.generated = 1

    def frontier() -> list[str]:  # sommet de pile en premier, sans doublons
        return list(dict.fromkeys(n for n, _ in reversed(stack) if n not in explored))

    rec.add("init", None, frontier(), explored, "Pile initiale = état initial.")
    while stack:
        node, prev = stack.pop()
        if node in explored:
            rec.add("skip", node, frontier(), explored, f"« {node} » déjà exploré : ignoré.")
            continue
        parent[node] = prev
        explored.append(node)
        rec.expanded += 1
        if node == goal:
            rec.add("goal", node, frontier(), explored, f"« {node} » est l'état objectif.")
            return rec.result("DFS (profondeur)", graph, rebuild_path(parent, goal))
        added = []
        for nxt, _ in reversed(graph.successors(node)):  # empilé à l'envers → alphabétique au dépilage
            if nxt not in explored:
                stack.append((nxt, node))
                added.append(nxt)
                rec.generated += 1
        rec.add("expand", node, frontier(), explored, f"Empilés : {fmt_list(reversed(added))}.")
    rec.add("stop", None, (), explored, "Pile vide.")
    return rec.result("DFS (profondeur)", graph, None)


_FOUND, _CUTOFF, _FAIL = "found", "cutoff", "fail"


def _dls(graph: Graph, node: str, goal: str, limit: int, path: list[str], on_path: set[str],
         rec: Recorder, explored: list[str]) -> str:
    explored.append(node)
    rec.expanded += 1
    depth = len(path) - 1
    trail = " → ".join(path)
    if node == goal:
        rec.add("goal", node, (), explored, f"Objectif atteint (profondeur {depth}). Chemin courant : {trail}.")
        return _FOUND
    if depth >= limit:
        rec.add("cutoff", node, (), explored, f"Limite {limit} atteinte en « {node} » : coupure. Chemin : {trail}.")
        return _CUTOFF
    rec.add("expand", node, (), explored, f"Profondeur {depth}/{limit}. Chemin courant : {trail}.")
    cutoff = False
    for nxt, _ in graph.successors(node):
        if nxt in on_path:  # évite les cycles le long du chemin courant
            continue
        rec.generated += 1
        path.append(nxt)
        on_path.add(nxt)
        status = _dls(graph, nxt, goal, limit, path, on_path, rec, explored)
        if status == _FOUND:
            return _FOUND
        cutoff = cutoff or status == _CUTOFF
        path.pop()
        on_path.discard(nxt)
    return _CUTOFF if cutoff else _FAIL


def dls(graph: Graph, start: str, goal: str, limit: int = 3, **_) -> SearchResult:
    """Profondeur limitée : DFS récursif coupé à la profondeur `limit`."""
    limit = int(limit)
    if limit < 0:
        raise ValueError("La limite de profondeur doit être positive ou nulle.")
    if limit > 900:
        raise ValueError("Limite trop grande (max 900) : risque de dépassement de la pile.")
    rec = Recorder()
    rec.generated = 1
    rec.add("init", None, (), (), f"Recherche en profondeur limitée à {limit}.")
    path = [start]
    status = _dls(graph, start, goal, limit, path, {start}, rec, [])
    if status == _FOUND:
        return rec.result(f"DLS (limite {limit})", graph, path)
    msg = ("Échec par coupure : la limite est peut-être trop faible." if status == _CUTOFF
           else "Aucun chemin trouvé.")
    return rec.result(f"DLS (limite {limit})", graph, None, msg)


def ids(graph: Graph, start: str, goal: str, **_) -> SearchResult:
    """Approfondissement itératif : DLS avec limite 0, 1, 2, ... (complet et optimal en nombre d'arcs)."""
    rec = Recorder()
    rec.generated = 1
    max_limit = max(len(graph.vertices) - 1, 0)  # un chemin simple ne dépasse pas |V|-1 arcs
    for limit in range(max_limit + 1):
        rec.add("info", None, (), (), f"=== Itération : limite de profondeur = {limit} ===")
        path = [start]
        status = _dls(graph, start, goal, limit, path, {start}, rec, [])
        if status == _FOUND:
            return rec.result("IDS (approfondissement itératif)", graph, path)
        if status == _FAIL:  # aucun cutoff : tout l'espace a été exploré
            break
    return rec.result("IDS (approfondissement itératif)", graph, None)


def ucs(graph: Graph, start: str, goal: str, **_) -> SearchResult:
    """Coût uniforme (Dijkstra) : développe le sommet de plus petit g(n) ; optimal en coût."""
    rec = Recorder()
    counter = 0
    heap: list[tuple[float, int, str]] = [(0.0, counter, start)]
    best = {start: 0.0}
    parent: dict[str, str | None] = {start: None}
    explored: list[str] = []
    rec.generated = 1

    def frontier() -> list[tuple[str, str]]:
        live = sorted((g, c, n) for g, c, n in heap if g <= best[n])
        return [(n, f"{n}[g={format_cost(g)}]") for g, _, n in live]

    def snap(action: str, node: str | None, note: str) -> None:
        items = frontier()
        rec.add(action, node, [n for n, _ in items], explored, note, labels=[l for _, l in items])

    snap("init", None, "Frontière initiale = état initial (g=0).")
    while heap:
        g, _, node = heapq.heappop(heap)
        if g > best[node]:
            continue  # entrée obsolète
        explored.append(node)
        rec.expanded += 1
        if node == goal:
            snap("goal", node, f"« {node} » est l'objectif, coût optimal g = {format_cost(g)}.")
            return rec.result("UCS (coût uniforme)", graph, rebuild_path(parent, goal))
        added = []
        for nxt, cost in graph.successors(node):
            new_g = g + cost
            if new_g < best.get(nxt, math.inf):
                best[nxt] = new_g
                parent[nxt] = node
                counter += 1
                heapq.heappush(heap, (new_g, counter, nxt))
                added.append(f"{nxt}(g={format_cost(new_g)})")
                rec.generated += 1
        snap("expand", node, f"g({node}) = {format_cost(g)}. Générés/améliorés : {fmt_list(added)}.")
    snap("stop", None, "Frontière vide.")
    return rec.result("UCS (coût uniforme)", graph, None)
