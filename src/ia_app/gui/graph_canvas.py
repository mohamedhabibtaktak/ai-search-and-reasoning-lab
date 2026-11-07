"""Canvas interactif du graphe : dessin, glisser-déposer, création d'arcs, coloration par étape."""
from __future__ import annotations

import math
import tkinter as tk
from typing import Callable, Iterable

from ..search.graph import Graph, format_cost
from ..search.layout import force_layout
from ..search.viz import COLORS
from .theme import ACCENT, INK, MUTED, PANEL

R = 31            # rayon d'un nœud (px)
MARGIN = 62
CURVE = 0.16      # courbure des arcs (permet de distinguer A→B de B→A)
SHIFT = 0x0001


class GraphCanvas(tk.Canvas):
    def __init__(self, master, graph: Graph, *, on_add_vertex: Callable[[float, float], None],
                 on_add_edge: Callable[[str, str], None], on_set_start: Callable[[str], None],
                 on_set_goal: Callable[[str], None], on_remove_vertex: Callable[[str], None]) -> None:
        super().__init__(master, background=PANEL, highlightthickness=1, highlightbackground="#d8dce3")
        self.graph = graph
        self.rel: dict[str, tuple[float, float]] = {}      # positions relatives (0..1) → indépendantes de la taille
        self._cb = (on_add_vertex, on_add_edge, on_set_start, on_set_goal, on_remove_vertex)
        self.explored: set[str] = set()
        self.frontier: set[str] = set()
        self.current: str | None = None
        self.path: list[str] = []
        self._drag: str | None = None
        self._edge_from: str | None = None
        self.bind("<Configure>", lambda _e: self.redraw())
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<B1-Motion>", self._motion)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<Double-Button-1>", self._double)
        for seq in ("<Button-3>", "<Button-2>", "<Control-Button-1>"):
            self.bind(seq, self._context)

    # --- données --------------------------------------------------------
    def set_graph(self, graph: Graph, relayout: bool = False) -> None:
        self.graph = graph
        if relayout:
            self.rel.clear()
            if graph.vertices:
                self.rel = {v: ((x + 1) / 2, (y + 1) / 2) for v, (x, y) in force_layout(graph).items()}
        self.sync()

    def sync(self) -> None:
        """Retire les positions orphelines, place les nouveaux sommets dans l'espace libre, redessine."""
        for v in [v for v in self.rel if v not in self.graph.vertices]:
            del self.rel[v]
        for v in self.graph.vertices:
            if v not in self.rel:
                self.rel[v] = self._free_spot()
        self.redraw()

    def _free_spot(self) -> tuple[float, float]:
        candidates = [(i / 10, j / 10) for i in range(1, 10) for j in range(1, 10)]
        if not self.rel:
            return 0.5, 0.5
        return max(candidates, key=lambda c: min(math.dist(c, p) for p in self.rel.values()))

    def show_state(self, explored: Iterable[str] = (), frontier: Iterable[str] = (),
                   current: str | None = None, path: Iterable[str] = ()) -> None:
        self.explored, self.frontier, self.current, self.path = set(explored), set(frontier), current, list(path)
        self.redraw()

    def clear_state(self) -> None:
        self.show_state()

    # --- géométrie -------------------------------------------------------
    def _size(self) -> tuple[int, int]:
        return max(self.winfo_width(), 320), max(self.winfo_height(), 240)

    def _px(self, v: str) -> tuple[float, float]:
        w, h = self._size()
        rx, ry = self.rel[v]
        return MARGIN + rx * (w - 2 * MARGIN), MARGIN + ry * (h - 2 * MARGIN)

    def _to_rel(self, x: float, y: float) -> tuple[float, float]:
        w, h = self._size()
        return (min(max((x - MARGIN) / (w - 2 * MARGIN), 0.0), 1.0),
                min(max((y - MARGIN) / (h - 2 * MARGIN), 0.0), 1.0))

    def _hit(self, x: float, y: float) -> str | None:
        for v in reversed(self.graph.vertices):
            if v in self.rel and math.dist((x, y), self._px(v)) <= R:
                return v
        return None

    # --- dessin ----------------------------------------------------------
    def redraw(self) -> None:
        self.delete("all")
        g = self.graph
        if not g.vertices:
            w, h = self._size()
            self.create_text(w / 2, h / 2, fill=MUTED, justify="center", font=("TkDefaultFont", 11),
                             text="Graphe vide\n\nDouble-clic pour ajouter un sommet\nou chargez l'exemple « Roumanie »")
            return
        path_edges = set(zip(self.path, self.path[1:]))
        for u, v, cost in g.edges():
            self._draw_edge(u, v, cost, (u, v) in path_edges)
        for v in g.vertices:
            self._draw_node(v)

    def _bezier(self, a, b, n: int = 36) -> list[tuple[float, float]]:
        (x1, y1), (x2, y2) = a, b
        cx, cy = (x1 + x2) / 2 + CURVE * (y2 - y1), (y1 + y2) / 2 - CURVE * (x2 - x1)
        return [((1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t * t * x2,
                 (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t * t * y2) for t in (i / n for i in range(n + 1))]

    def _draw_edge(self, u: str, v: str, cost: float, hot: bool) -> None:
        a, b = self._px(u), self._px(v)
        pts = self._bezier(a, b)
        keep = [p for p in pts if math.dist(p, a) > R + 1 and math.dist(p, b) > R + 4]
        if len(keep) < 2:
            return
        color = COLORS["path"] if hot else COLORS["edge"]
        self.create_line(*[c for p in keep for c in p], fill=color, width=4 if hot else 1.6,
                         arrow=tk.LAST, arrowshape=(13, 15, 5), smooth=False)
        mx, my = pts[len(pts) // 2]
        text = self.create_text(mx, my, text=format_cost(cost), fill=COLORS["path"] if hot else INK,
                                font=("TkDefaultFont", 9, "bold" if hot else "normal"))
        x0, y0, x1, y1 = self.bbox(text)
        box = self.create_rectangle(x0 - 3, y0 - 1, x1 + 3, y1 + 1, fill=PANEL, outline="")
        self.tag_raise(text, box)

    def _draw_node(self, v: str) -> None:
        g = self.graph
        x, y = self._px(v)
        fill = (COLORS["start"] if v == g.start else COLORS["goal"] if v == g.goal
                else COLORS["frontier"] if v in self.frontier else COLORS["explored"] if v in self.explored
                else COLORS["node"])
        outline, width = ("#444", 1.5)
        if v in self.path:
            outline, width = COLORS["path"], 4
        if v == self.current:
            outline, width = ACCENT, 4
        self.create_oval(x - R, y - R, x + R, y + R, fill=fill, outline=outline, width=width)
        h = g.heuristics.get(v)
        label = v if h is None else f"{v}\nh={format_cost(h)}"
        self.create_text(x, y, text=label, fill=INK, justify="center",
                         font=("TkDefaultFont", 9 if len(v) < 8 else 8, "bold"))

    # --- interactions ---------------------------------------------------------
    def _press(self, e: tk.Event) -> None:
        v = self._hit(e.x, e.y)
        self._drag = self._edge_from = None
        if v is None:
            return
        if e.state & SHIFT:
            self._edge_from = v          # Maj + glisser : créer un arc
        else:
            self._drag = v               # glisser : déplacer le sommet

    def _motion(self, e: tk.Event) -> None:
        if self._drag:
            self.rel[self._drag] = self._to_rel(e.x, e.y)
            self.redraw()
        elif self._edge_from:
            self.delete("rubber")
            x, y = self._px(self._edge_from)
            self.create_line(x, y, e.x, e.y, dash=(5, 4), fill=ACCENT, width=2, arrow=tk.LAST, tags="rubber")

    def _release(self, e: tk.Event) -> None:
        src, self._edge_from, self._drag = self._edge_from, None, None
        self.delete("rubber")
        if src:
            dst = self._hit(e.x, e.y)
            if dst and dst != src:
                self._cb[1](src, dst)

    def _double(self, e: tk.Event) -> None:
        if self._hit(e.x, e.y) is None:
            self._cb[0](*self._to_rel(e.x, e.y))

    def _context(self, e: tk.Event) -> None:
        v = self._hit(e.x, e.y)
        if v is None:
            return
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label=f"« {v} » = état initial", command=lambda: self._cb[2](v))
        menu.add_command(label=f"« {v} » = état objectif", command=lambda: self._cb[3](v))
        menu.add_separator()
        menu.add_command(label=f"Supprimer « {v} »", command=lambda: self._cb[4](v))
        menu.tk_popup(e.x_root, e.y_root)
