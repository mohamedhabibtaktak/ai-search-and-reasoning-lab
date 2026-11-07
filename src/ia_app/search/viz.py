"""Visualisation du graphe : image matplotlib (optionnelle) et export Graphviz DOT (sans dépendance)."""
from __future__ import annotations

import math
from pathlib import Path

from ..common.errors import VisualizationUnavailable
from .algorithms.base import SearchResult, Step
from .graph import Graph, format_cost
from .layout import force_layout

COLORS = {
    "node": "#eef1f6", "explored": "#b9d3f5", "frontier": "#fde7a8",
    "start": "#a6dcae", "goal": "#f2a7a7", "edge": "#8a93a3", "path": "#d9480f",
}


def to_dot(graph: Graph, result: SearchResult | None = None) -> str:
    """Graphviz DOT : `dot -Tpng graphe.dot -o graphe.png`. Le chemin trouvé est surligné."""
    on_path = set(zip(result.path, result.path[1:])) if result and result.found else set()
    path_nodes = set(result.path) if result and result.found else set()
    lines = ["digraph G {", "  rankdir=LR;", '  node [shape=circle, style=filled, fillcolor="#eef1f6"];']
    for v in graph.vertices:
        label = v if v not in graph.heuristics else f"{v}\\nh={format_cost(graph.heuristics[v])}"
        fill = COLORS["start"] if v == graph.start else COLORS["goal"] if v == graph.goal else COLORS["node"]
        pen = ', penwidth=3, color="#d9480f"' if v in path_nodes else ""
        lines.append(f'  "{v}" [label="{label}", fillcolor="{fill}"{pen}];')
    for u, v, c in graph.edges():
        extra = ', color="#d9480f", penwidth=3' if (u, v) in on_path else ""
        lines.append(f'  "{u}" -> "{v}" [label="{format_cost(c)}"{extra}];')
    lines.append("}")
    return "\n".join(lines) + "\n"


def _pyplot(headless: bool):
    try:
        import matplotlib
        if headless:
            matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyArrowPatch
    except ImportError:
        raise VisualizationUnavailable(
            "matplotlib n'est pas installé (pip install matplotlib). "
            "Vous pouvez exporter le graphe au format DOT à la place.") from None
    return plt, FancyArrowPatch


def draw_graph(graph: Graph, result: SearchResult | None = None, *, step: Step | None = None,
               save_to: str | Path | None = None, show: bool = False, title: str | None = None) -> Path | None:
    """Dessine le graphe. `step` montre l'état intermédiaire ; sans `step`, `result` montre l'état final.

    save_to : enregistre un PNG ; show : ouvre une fenêtre (nécessite un environnement graphique).
    """
    plt, FancyArrowPatch = _pyplot(headless=not show)
    pos = force_layout(graph)
    node_area = 2600 if len(pos) <= 14 else 1500   # taille des nœuds en points² (indépendante de l'échelle)
    shrink = math.sqrt(node_area) / 2 + 3

    explored: set[str] = set()
    frontier: set[str] = set()
    path: list[str] = []
    if step is not None:
        explored, frontier = set(step.explored), set(step.frontier)
    elif result is not None:
        explored = set(result.steps[-1].explored) if result.steps else set()
        path = result.path
    path_edges = set(zip(path, path[1:]))
    if step is not None and step.action == "goal":
        pass  # le chemin n'est montré que sur le résultat final

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)
    rad = 0.14
    for u, v, c in graph.edges():
        (x1, y1), (x2, y2) = pos[u], pos[v]
        hot = (u, v) in path_edges
        ax.add_patch(FancyArrowPatch(
            (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14, shrinkA=shrink, shrinkB=shrink,
            connectionstyle=f"arc3,rad={rad}", color=COLORS["path"] if hot else COLORS["edge"],
            lw=3 if hot else 1.2, zorder=1))
        dx, dy = x2 - x1, y2 - y1
        mx, my = (x1 + x2) / 2 + 0.5 * rad * dy, (y1 + y2) / 2 - 0.5 * rad * dx  # milieu de l'arc
        ax.text(mx, my, format_cost(c), ha="center", va="center", fontsize=8, zorder=3,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9))
    for v, (x, y) in pos.items():
        fill = (COLORS["start"] if v == graph.start else COLORS["goal"] if v == graph.goal
                else COLORS["frontier"] if v in frontier else COLORS["explored"] if v in explored
                else COLORS["node"])
        ax.scatter([x], [y], s=node_area, c=fill, edgecolors=COLORS["path"] if v in path else "#444",
                   linewidths=3 if v in path else 1.2, zorder=2)
        h = graph.heuristics.get(v)
        label = v if h is None else f"{v}\nh={format_cost(h)}"
        ax.text(x, y, label, ha="center", va="center", fontsize=7.5, zorder=4)

    if title is None and result is not None:
        title = f"{result.algorithm} — " + (f"coût {result.cost_text}" if result.found else "aucun chemin")
    if title:
        ax.set_title(title, fontsize=12)
    handles = [plt.Line2D([], [], marker="o", ls="", mfc=COLORS[k], mec="#444", label=lab)
               for k, lab in [("start", "initial"), ("goal", "objectif"), ("explored", "exploré"),
                              ("frontier", "frontière")]]
    ax.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=8)

    saved = None
    if save_to is not None:
        saved = Path(save_to)
        saved.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(saved, dpi=130, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)
    return saved


def render_frames(graph: Graph, result: SearchResult, out_dir: str | Path) -> list[Path]:
    """Une image par étape (frame_001.png, ...) + image finale avec le chemin : utile pour la vidéo de démo."""
    out = Path(out_dir)
    frames = [draw_graph(graph, step=s, save_to=out / f"frame_{s.index:03d}.png",
                         title=f"{result.algorithm} — étape {s.index} : {s.note[:70]}")
              for s in result.steps]
    frames.append(draw_graph(graph, result, save_to=out / "final.png"))
    return [f for f in frames if f]
