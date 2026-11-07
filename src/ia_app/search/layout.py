"""Placement automatique des sommets (partagé par la visualisation matplotlib et la GUI)."""
from __future__ import annotations

import math
import random

from .graph import Graph


def force_layout(graph: Graph) -> dict[str, tuple[float, float]]:
    """Placement par forces (Fruchterman-Reingold), déterministe : les voisins se rapprochent,
    les sommets non liés se repoussent. Résultat normalisé dans [-1, 1]²."""
    vertices = graph.vertices
    n = len(vertices)
    if n <= 3:
        return {v: (math.cos(2 * math.pi * i / max(n, 1) - math.pi / 2),
                    math.sin(2 * math.pi * i / max(n, 1) - math.pi / 2)) for i, v in enumerate(vertices)}
    rng = random.Random(7)
    pos = {v: [math.cos(2 * math.pi * i / n) + rng.uniform(-.05, .05),
               math.sin(2 * math.pi * i / n) + rng.uniform(-.05, .05)] for i, v in enumerate(vertices)}
    links = {frozenset((u, v)) for u, v, _ in graph.edges()}
    k = 2 / math.sqrt(n)
    iterations = 300
    for it in range(iterations):
        temp = 0.3 * (1 - it / iterations) + 0.005
        disp = {v: [0.0, 0.0] for v in vertices}
        for i, u in enumerate(vertices):
            for v in vertices[i + 1:]:
                dx, dy = pos[u][0] - pos[v][0], pos[u][1] - pos[v][1]
                d = math.hypot(dx, dy) or 1e-6
                f = k * k / d
                disp[u][0] += dx / d * f; disp[u][1] += dy / d * f
                disp[v][0] -= dx / d * f; disp[v][1] -= dy / d * f
        for link in links:
            u, v = tuple(link)
            dx, dy = pos[u][0] - pos[v][0], pos[u][1] - pos[v][1]
            d = math.hypot(dx, dy) or 1e-6
            f = d * d / k
            disp[u][0] -= dx / d * f; disp[u][1] -= dy / d * f
            disp[v][0] += dx / d * f; disp[v][1] += dy / d * f
        for v in vertices:
            d = math.hypot(*disp[v]) or 1e-6
            step = min(d, temp)
            pos[v][0] += disp[v][0] / d * step
            pos[v][1] += disp[v][1] / d * step
    xs, ys = [p[0] for p in pos.values()], [p[1] for p in pos.values()]
    span = max(max(xs) - min(xs), max(ys) - min(ys)) or 1.0
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    return {v: (2 * (p[0] - cx) / span, 2 * (p[1] - cy) / span) for v, p in pos.items()}
