"""Sauvegarde / chargement d'un graphe (JSON)."""
from __future__ import annotations

from pathlib import Path

from ..common.jsonio import load_json, save_json
from .graph import Graph


def save_graph(graph: Graph, path: str | Path) -> Path:
    return save_json(path, graph.to_dict())


def load_graph(path: str | Path) -> Graph:
    return Graph.from_dict(load_json(path))
