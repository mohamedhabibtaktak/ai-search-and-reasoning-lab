"""Graphe d'exemple : carte routière de Roumanie (Russell & Norvig), Arad → Bucharest."""
from __future__ import annotations

from .graph import Graph

_ROADS = [
    ("Arad", "Zerind", 75), ("Arad", "Sibiu", 140), ("Arad", "Timisoara", 118),
    ("Zerind", "Oradea", 71), ("Oradea", "Sibiu", 151), ("Sibiu", "Fagaras", 99),
    ("Sibiu", "Rimnicu", 80), ("Timisoara", "Lugoj", 111), ("Lugoj", "Mehadia", 70),
    ("Mehadia", "Drobeta", 75), ("Drobeta", "Craiova", 120), ("Craiova", "Rimnicu", 146),
    ("Craiova", "Pitesti", 138), ("Rimnicu", "Pitesti", 97), ("Fagaras", "Bucharest", 211),
    ("Pitesti", "Bucharest", 101),
]
_H = {  # distance à vol d'oiseau vers Bucharest
    "Arad": 366, "Bucharest": 0, "Craiova": 160, "Drobeta": 242, "Fagaras": 176, "Lugoj": 244,
    "Mehadia": 241, "Oradea": 380, "Pitesti": 100, "Rimnicu": 193, "Sibiu": 253,
    "Timisoara": 329, "Zerind": 374,
}


def romania_graph() -> Graph:
    graph = Graph()
    for a, b, cost in _ROADS:
        graph.add_edge(a, b, cost, create_missing=True)
        graph.add_edge(b, a, cost, create_missing=True)  # routes à double sens
    for city, h in _H.items():
        graph.set_heuristic(city, h)
    graph.set_start("Arad")
    graph.set_goal("Bucharest")
    return graph
