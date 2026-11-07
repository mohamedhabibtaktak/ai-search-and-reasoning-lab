"""Onglet « Algorithmes de recherche »."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from ..common.errors import GraphError
from ..search import ALGORITHMS, Graph, algorithms_by_category, run_search
from ..search.algorithms import SearchResult
from ..search.formatting import step_details, step_title
from ..search.graph import format_cost
from ..search.samples import romania_graph
from ..search.storage import load_graph, save_graph
from ..search.viz import draw_graph, to_dot
from . import dialogs
from .dialogs import guarded
from .graph_canvas import GraphCanvas
from .playback import Player
from .theme import ERR, INK, MUTED, OK, WARN

HINT = "Double-clic : sommet  ·  Glisser : déplacer  ·  Maj+glisser : arc  ·  Clic droit : menu"


class SearchTab(ttk.Frame):
    def __init__(self, master, graph: Graph | None = None) -> None:
        super().__init__(master, padding=10)
        self.graph = graph or Graph()
        self.result: SearchResult | None = None
        self.player: Player | None = None
        self._job: str | None = None
        self.informed_var = tk.IntVar(value=0)
        self.algo_var = tk.StringVar()
        self.limit_var = tk.IntVar(value=3)
        self.start_var, self.goal_var = tk.StringVar(), tk.StringVar()
        self._specs = []
        self._build()
        self._fill_algorithms()
        self.refresh(relayout=True)

    # --- construction ------------------------------------------------------
    def _build(self) -> None:
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 8))
        for text, cmd in (("Nouveau", self.new_graph), ("Exemple « Roumanie »", self.load_sample),
                          ("Ouvrir…", self.open_file), ("Enregistrer…", self.save_file),
                          ("Exporter PNG…", self.export_png), ("Exporter DOT…", self.export_dot)):
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=(0, 6))
        panes = ttk.PanedWindow(self, orient="horizontal")
        panes.pack(fill="both", expand=True)
        left, center, right = ttk.Frame(panes, width=300), ttk.Frame(panes), ttk.Frame(panes, width=350)
        panes.add(left, weight=0)
        panes.add(center, weight=1)
        panes.add(right, weight=0)
        self._build_left(left)
        self._build_center(center)
        self._build_right(right)

    def _tree(self, parent, columns: dict[str, tuple[str, int]], height: int) -> ttk.Treeview:
        holder = ttk.Frame(parent)
        holder.pack(fill="both", expand=True)
        tree = ttk.Treeview(holder, columns=list(columns), show="headings", height=height, selectmode="browse")
        for key, (title, width) in columns.items():
            tree.heading(key, text=title)
            tree.column(key, width=width, anchor="w" if key == "v" or key == "u" else "center")
        sb = ttk.Scrollbar(holder, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return tree

    def _build_left(self, left: ttk.Frame) -> None:
        states = ttk.LabelFrame(left, text="ÉTATS", padding=8)
        states.pack(fill="x")
        for row, (label, var) in enumerate((("Initial", self.start_var), ("Objectif", self.goal_var))):
            ttk.Label(states, text=label).grid(row=row, column=0, sticky="w", pady=2)
            box = ttk.Combobox(states, textvariable=var, state="readonly", width=20)
            box.grid(row=row, column=1, padx=(10, 0), pady=2, sticky="ew")
            box.bind("<<ComboboxSelected>>", lambda _e: self._states_changed())
            setattr(self, "start_box" if row == 0 else "goal_box", box)
        states.columnconfigure(1, weight=1)

        verts = ttk.LabelFrame(left, text="SOMMETS  ·  h(n)", padding=8)
        verts.pack(fill="both", expand=True, pady=(8, 0))
        self.vertex_tree = self._tree(verts, {"v": ("Sommet", 150), "h": ("h(n)", 70)}, 6)
        self.vertex_tree.bind("<Double-Button-1>", lambda _e: self.edit_heuristic())
        row = ttk.Frame(verts)
        row.pack(fill="x", pady=(6, 0))
        ttk.Button(row, text="+ Sommet", command=self.add_vertex).pack(side="left")
        ttk.Button(row, text="Supprimer", command=self.remove_vertex).pack(side="left", padx=4)
        ttk.Button(row, text="Saisir h…", command=self.fill_heuristics).pack(side="left")
        self.h_report = ttk.Label(verts, text="", style="Muted.TLabel", wraplength=270)
        self.h_report.pack(anchor="w", pady=(6, 0))

        edges = ttk.LabelFrame(left, text="ARCS ORIENTÉS  ·  COÛT", padding=8)
        edges.pack(fill="both", expand=True, pady=(8, 0))
        self.edge_tree = self._tree(edges, {"u": ("De", 90), "w": ("Vers", 90), "c": ("Coût", 60)}, 6)
        self.edge_tree.bind("<Double-Button-1>", lambda _e: self.edit_edge_cost())
        row = ttk.Frame(edges)
        row.pack(fill="x", pady=(6, 0))
        ttk.Button(row, text="+ Arc", command=self.add_edge).pack(side="left")
        ttk.Button(row, text="Supprimer", command=self.remove_edge).pack(side="left", padx=4)

    def _build_center(self, center: ttk.Frame) -> None:
        self.canvas = GraphCanvas(center, self.graph, on_add_vertex=self._canvas_add_vertex,
                                  on_add_edge=self._canvas_add_edge, on_set_start=self._set_start,
                                  on_set_goal=self._set_goal, on_remove_vertex=self._remove_named)
        self.canvas.pack(fill="both", expand=True, padx=10)
        ttk.Label(center, text=HINT, style="Muted.TLabel", wraplength=460, justify="center").pack(pady=(6, 0))

    def _build_right(self, right: ttk.Frame) -> None:
        box = ttk.LabelFrame(right, text="RECHERCHE", padding=10)
        box.pack(fill="x", padx=(10, 0))
        for value, text in ((0, "Non informée (aveugle)"), (1, "Informée (heuristique)")):
            ttk.Radiobutton(box, text=text, value=value, variable=self.informed_var,
                            command=self._fill_algorithms).pack(anchor="w")
        self.algo_box = ttk.Combobox(box, textvariable=self.algo_var, state="readonly", width=34)
        self.algo_box.pack(fill="x", pady=(8, 2))
        self.algo_box.bind("<<ComboboxSelected>>", lambda _e: self._algo_changed())
        self.algo_info = ttk.Label(box, text="", style="Muted.TLabel", wraplength=300)
        self.algo_info.pack(anchor="w")
        self.limit_row = ttk.Frame(box)
        ttk.Label(self.limit_row, text="Limite de profondeur").pack(side="left")
        ttk.Spinbox(self.limit_row, from_=0, to=900, width=6, textvariable=self.limit_var).pack(side="left", padx=8)
        row = ttk.Frame(box)
        row.pack(fill="x", pady=(10, 0))
        ttk.Button(row, text="▶  Lancer", style="Accent.TButton", command=self.run).pack(side="left")
        ttk.Button(row, text="Comparer tout", command=self.compare).pack(side="left", padx=6)

        run = ttk.LabelFrame(right, text="EXÉCUTION", padding=10)
        run.pack(fill="both", expand=True, padx=(10, 0), pady=(8, 0))
        ctrl = ttk.Frame(run)
        ctrl.pack(fill="x")
        self.btns = {}
        for key, text, cmd in (("first", "⏮", self.first), ("prev", "◀", self.prev), ("next", "▶", self.next),
                               ("last", "⏭", self.last), ("play", "⏵ Lecture", self.toggle_play)):
            self.btns[key] = ttk.Button(ctrl, text=text, command=cmd, state="disabled", width=3 if key != "play" else 9)
            self.btns[key].pack(side="left", padx=(0, 4))
        self.step_var = tk.StringVar(value="")
        ttk.Label(ctrl, textvariable=self.step_var, style="Muted.TLabel").pack(side="right")
        holder = ttk.Frame(run)
        holder.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(holder, wrap="word", width=38, height=14, state="disabled", relief="flat", padx=8, pady=6,
                           font=("TkDefaultFont", 9), highlightthickness=1, highlightbackground="#d8dce3")
        sb = ttk.Scrollbar(holder, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.log.tag_configure("title", font=("TkDefaultFont", 9, "bold"), spacing1=6)
        self.log.tag_configure("goal", foreground=OK, font=("TkDefaultFont", 9, "bold"), spacing1=6)
        self.log.tag_configure("meta", foreground=MUTED)
        self.log.tag_configure("sep", foreground="#7a2ea8", font=("TkDefaultFont", 9, "bold"), spacing1=8)
        self.log.tag_configure("now", background="#fff6cf")
        self.result_label = ttk.Label(run, text="Lancez une recherche.", style="Result.TLabel", padding=8, wraplength=300)
        self.result_label.pack(fill="x", pady=(8, 0))

    # --- état du graphe -----------------------------------------------------------
    def refresh(self, *, relayout: bool = False) -> None:
        g = self.graph
        self.canvas.set_graph(g, relayout=relayout)
        self.vertex_tree.delete(*self.vertex_tree.get_children())
        for v in g.vertices:
            h = g.heuristics.get(v)
            self.vertex_tree.insert("", "end", iid=f"v:{v}", values=(v, "?" if h is None else format_cost(h)))
        self.edge_tree.delete(*self.edge_tree.get_children())
        for u, v, c in g.edges():
            self.edge_tree.insert("", "end", iid=f"e:{u}\t{v}", values=(u, v, format_cost(c)))
        for box, var, value in ((self.start_box, self.start_var, g.start), (self.goal_box, self.goal_var, g.goal)):
            box.configure(values=g.vertices)
            var.set(value or "")
        self._heuristic_report()
        self._reset_run()

    def _heuristic_report(self) -> None:
        g = self.graph
        if not g.vertices or g.goal is None:
            self.h_report.configure(text="", foreground=MUTED)
        elif g.missing_heuristics():
            self.h_report.configure(text=f"h manquante : {', '.join(g.missing_heuristics())}", foreground=WARN)
        else:
            report = g.check_heuristic()
            if report.problems:
                self.h_report.configure(text="⚠ " + report.problems[0] + ("  (+ autres)" if len(report.problems) > 1 else ""),
                                        foreground=WARN)
            else:
                self.h_report.configure(text="✔ h admissible et consistante : A* optimal.", foreground=OK)

    def _states_changed(self) -> None:
        if self.start_var.get():
            self.graph.set_start(self.start_var.get())
        if self.goal_var.get():
            self.graph.set_goal(self.goal_var.get())
        self.refresh()

    @guarded
    def _set_start(self, v: str) -> None:
        self.graph.set_start(v)
        self.refresh()

    @guarded
    def _set_goal(self, v: str) -> None:
        self.graph.set_goal(v)
        self.refresh()

    # --- édition -----------------------------------------------------------------
    @guarded
    def add_vertex(self) -> None:
        raw = dialogs.ask_text(self, "Ajouter des sommets", "Nom(s) du/des sommet(s) (séparés par des virgules) :")
        if raw:
            for name in raw.split(","):
                if name.strip():
                    self.graph.add_vertex(name)
            self.refresh()

    @guarded
    def _canvas_add_vertex(self, rx: float, ry: float) -> None:
        name = dialogs.ask_text(self, "Nouveau sommet", "Nom du sommet :")
        if name:
            if self.graph.add_vertex(name):
                self.canvas.rel[name.strip()] = (rx, ry)
            self.refresh()

    @guarded
    def remove_vertex(self) -> None:
        selection = self.vertex_tree.selection()
        if selection:
            self._remove_named(selection[0][2:])

    @guarded
    def _remove_named(self, name: str) -> None:
        self.graph.remove_vertex(name)
        self.refresh()

    @guarded
    def add_edge(self, src: str = "", dst: str = "") -> None:
        answer = dialogs.ask_edge(self, self.graph.vertices, src, dst)
        if answer is None:
            return
        s, d, cost, both = answer
        self.graph.add_edge(s, d, cost, create_missing=True)
        if both:
            self.graph.add_edge(d, s, cost, create_missing=True)
        self.refresh()

    def _canvas_add_edge(self, src: str, dst: str) -> None:
        self.add_edge(src, dst)

    @guarded
    def remove_edge(self) -> None:
        selection = self.edge_tree.selection()
        if selection:
            u, v = selection[0][2:].split("\t")
            self.graph.remove_edge(u, v)
            self.refresh()

    @guarded
    def edit_edge_cost(self) -> None:
        selection = self.edge_tree.selection()
        if not selection:
            return
        u, v = selection[0][2:].split("\t")
        cost = dialogs.ask_number(self, f"Coût {u} → {v}", "Nouveau coût (≥ 0) :",
                                  format_cost(self.graph.successors(u) and dict(self.graph.successors(u))[v]))
        if cost is not None:
            self.graph.add_edge(u, v, cost)
            self.refresh()

    @guarded
    def edit_heuristic(self) -> None:
        selection = self.vertex_tree.selection()
        if not selection:
            return
        v = selection[0][2:]
        current = self.graph.heuristics.get(v)
        value = dialogs.ask_number(self, f"h({v})", f"Heuristique h({v}) ≥ 0 (coût restant estimé) :",
                                   "" if current is None else format_cost(current))
        if value is not None:
            self.graph.set_heuristic(v, value)
            self.refresh()

    @guarded
    def fill_heuristics(self) -> None:
        """Parcourt les sommets sans h ; Annuler interrompt la saisie."""
        for v in self.graph.missing_heuristics():
            value = dialogs.ask_number(self, f"h({v})", f"Heuristique h({v}) ≥ 0 :")
            if value is None:
                break
            self.graph.set_heuristic(v, value)
        self.refresh()

    # --- fichiers --------------------------------------------------------------------
    @guarded
    def new_graph(self) -> None:
        if not self.graph.vertices or dialogs.confirm(self, "Nouveau graphe", "Supprimer le graphe actuel ?"):
            self.graph = Graph()
            self.refresh(relayout=True)

    def load_sample(self) -> None:
        self.graph = romania_graph()
        self.refresh(relayout=True)

    @guarded
    def open_file(self) -> None:
        path = filedialog.askopenfilename(parent=self, title="Ouvrir un graphe",
                                          initialdir="data/graphs" if Path("data/graphs").is_dir() else ".",
                                          filetypes=[("Graphe JSON", "*.json"), ("Tous", "*.*")])
        if path:
            self.graph = load_graph(path)
            self.refresh(relayout=True)

    @guarded
    def save_file(self) -> None:
        path = filedialog.asksaveasfilename(parent=self, title="Enregistrer le graphe", defaultextension=".json",
                                            filetypes=[("Graphe JSON", "*.json")])
        if path:
            save_graph(self.graph, path)

    @guarded
    def export_png(self) -> None:
        path = filedialog.asksaveasfilename(parent=self, title="Exporter en image", defaultextension=".png",
                                            filetypes=[("Image PNG", "*.png")])
        if path:
            draw_graph(self.graph, self.result, save_to=path)

    @guarded
    def export_dot(self) -> None:
        path = filedialog.asksaveasfilename(parent=self, title="Exporter en Graphviz DOT", defaultextension=".dot",
                                            filetypes=[("Graphviz", "*.dot")])
        if path:
            Path(path).write_text(to_dot(self.graph, self.result), encoding="utf-8")

    # --- recherche ---------------------------------------------------------------------
    def _fill_algorithms(self) -> None:
        self._specs = algorithms_by_category(informed=bool(self.informed_var.get()))
        self.algo_box.configure(values=[s.label for s in self._specs])
        self.algo_var.set(self._specs[0].label)
        self._algo_changed()

    def _spec(self):
        return next(s for s in self._specs if s.label == self.algo_var.get())

    def _algo_changed(self) -> None:
        spec = self._spec()
        self.algo_info.configure(text=spec.summary)
        if "limit" in spec.params:
            self.limit_row.pack(fill="x", pady=(6, 0), after=self.algo_info)
        else:
            self.limit_row.pack_forget()
        self._reset_run()

    def _reset_run(self) -> None:
        self._stop()
        self.result = self.player = None
        self.step_var.set("")
        self._set_log([])
        self.result_label.configure(text="Lancez une recherche.", foreground=MUTED)
        for b in self.btns.values():
            b.configure(state="disabled")
        self.canvas.clear_state()

    @guarded
    def run(self) -> None:
        g, spec = self.graph, self._spec()
        if not g.vertices:
            raise GraphError("Le graphe est vide : ajoutez des sommets ou chargez l'exemple.")
        if g.start is None or g.goal is None:
            raise GraphError("Définissez l'état initial et l'état objectif (panneau « États »).")
        if spec.informed and g.missing_heuristics():
            if dialogs.confirm(self, "Heuristique manquante",
                               f"h(n) manque pour : {', '.join(g.missing_heuristics())}.\nLa saisir maintenant ?"):
                self.fill_heuristics()
            if g.missing_heuristics():
                return
        params = {"limit": int(self.limit_var.get())} if "limit" in spec.params else {}
        result = run_search(g, spec.key, **params)
        self._reset_run()
        self.result, self.player = result, Player(len(result.steps))
        self._render()

    def _set_log(self, steps) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        for i, step in enumerate(steps):
            last = i == len(steps) - 1
            start = self.log.index("end-1c")
            if step.action == "info":
                self.log.insert("end", f"{step.note}\n", "sep")
            else:
                self.log.insert("end", f"Étape {step.index} · {step_title(step)}\n",
                                "goal" if step.action == "goal" else "title")
                for line in step_details(step):
                    self.log.insert("end", f"   {line}\n", "meta" if line.startswith("Explorés") else ())
            if last:
                self.log.tag_add("now", start, "end-1c")
        self.log.configure(state="disabled")
        self.log.see("end")

    def _render(self) -> None:
        r, p = self.result, self.player
        if r is None or p is None:
            return
        step = r.steps[p.position]
        self._set_log(r.steps[: p.position + 1])
        self.step_var.set(f"Étape {p.position + 1} / {p.count}")
        final = p.at_end
        self.canvas.show_state(step.explored, step.frontier, step.current, r.path if final and r.found else ())
        if not final:
            self.result_label.configure(text="Exploration en cours…", foreground=MUTED)
        elif r.found:
            self.result_label.configure(
                text=f"✔ Chemin : {' → '.join(r.path)}\nCoût total : {r.cost_text}  ·  {len(r.path) - 1} arc(s)\n"
                     f"Développés : {r.expanded}  ·  Générés : {r.generated}", foreground=OK)
        else:
            self.result_label.configure(text=f"✘ Aucun chemin trouvé.\n{r.message}\nDéveloppés : {r.expanded}",
                                        foreground=ERR)
        busy = self._job is not None
        state = lambda ok: "normal" if ok else "disabled"  # noqa: E731
        self.btns["first"].configure(state=state(not p.at_start))
        self.btns["prev"].configure(state=state(not p.at_start))
        self.btns["next"].configure(state=state(not p.at_end))
        self.btns["last"].configure(state=state(not p.at_end))
        self.btns["play"].configure(state=state(not p.at_end or busy), text="⏸ Pause" if busy else "⏵ Lecture")

    def first(self) -> None:
        self._stop()
        if self.player:
            self.player.first()
            self._render()

    def prev(self) -> None:
        self._stop()
        if self.player and self.player.prev():
            self._render()

    def next(self) -> None:
        self._stop()
        if self.player and self.player.next():
            self._render()

    def last(self) -> None:
        self._stop()
        if self.player:
            self.player.last()
            self._render()

    def toggle_play(self) -> None:
        if self._job is not None:
            self._stop()
            self._render()
        elif self.player and not self.player.at_end:
            self._job = self.after(700, self._tick)
            self._render()

    def _tick(self) -> None:
        self._job = None
        if self.player and self.player.next():
            if not self.player.at_end:
                self._job = self.after(700, self._tick)
            self._render()

    def _stop(self) -> None:
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None

    # --- comparaison ----------------------------------------------------------------------
    @guarded
    def compare(self) -> None:
        g = self.graph
        if not g.vertices or g.start is None or g.goal is None:
            raise GraphError("Définissez le graphe, l'état initial et l'état objectif.")
        rows = []
        for spec in ALGORITHMS.values():
            if spec.informed and g.missing_heuristics():
                rows.append((spec.label.split(" — ")[0], "h manquante", "", "", ""))
                continue
            r = run_search(g, spec.key, **({"limit": len(g.vertices)} if "limit" in spec.params else {}))
            rows.append((spec.label.split(" — ")[0], "oui" if r.found else "non", r.cost_text, str(r.expanded),
                         " → ".join(r.path) if r.found else r.message))
        costs = [float(c) for _, ok, c, *_ in rows if ok == "oui"]
        best = min(costs) if costs else None
        win = tk.Toplevel(self)
        win.title("Comparaison des algorithmes")
        win.geometry("780x340")
        tree = ttk.Treeview(win, columns=("a", "f", "c", "e", "p"), show="headings", height=len(rows))
        for key, title, width in (("a", "Algorithme", 130), ("f", "Trouvé", 80), ("c", "Coût", 70),
                                  ("e", "Développés", 90), ("p", "Chemin", 380)):
            tree.heading(key, text=title)
            tree.column(key, width=width, anchor="w" if key in "ap" else "center")
        tree.tag_configure("best", background="#e3f4ea")
        for name, ok, cost, expanded, path in rows:
            is_best = ok == "oui" and best is not None and float(cost) == best
            tree.insert("", "end", values=(name, ok, cost, expanded, path + ("   ★ optimal" if is_best else "")),
                        tags=("best",) if is_best else ())
        tree.pack(fill="both", expand=True, padx=12, pady=(12, 4))
        ttk.Label(win, text="★ = meilleur coût obtenu", style="Muted.TLabel").pack(pady=(0, 10))
