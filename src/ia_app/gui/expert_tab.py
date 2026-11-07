"""Onglet « Systèmes experts »."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from ..expert import KnowledgeBase, backward_chaining, forward_chaining, parse_rule
from ..expert.inference import InferenceResult
from ..expert.models import normalize_fact
from ..expert.samples import animal_kb
from ..expert.storage import load_kb, save_kb
from . import dialogs
from .dialogs import guarded
from .playback import Player
from .theme import ERR, INK, MUTED, OK, WARN

_ICONS = {"fire": "▶", "goal": "★", "proved": "✔", "known": "✔", "failed": "✘", "cycle-cut": "↺",
          "cycle": "◆", "subgoal": "?", "try": "→", "skip": "·", "info": "i"}
_TAGS = {"fire": {"foreground": "#7a2ea8", "font": ("TkFixedFont", 10, "bold")},
         "goal": {"foreground": OK, "font": ("TkFixedFont", 10, "bold")},
         "proved": {"foreground": OK}, "known": {"foreground": OK},
         "failed": {"foreground": ERR}, "cycle-cut": {"foreground": WARN},
         "cycle": {"foreground": MUTED, "font": ("TkFixedFont", 10, "bold")}, "skip": {"foreground": MUTED}}
METHODS = {"forward": ("Chaînage avant", forward_chaining), "backward": ("Chaînage arrière", backward_chaining)}


class ExpertTab(ttk.Frame):
    def __init__(self, master, kb: KnowledgeBase | None = None) -> None:
        super().__init__(master, padding=10)
        self.kb = kb or animal_kb()
        self.result: InferenceResult | None = None
        self.player: Player | None = None
        self._job: str | None = None
        self.goal_var = tk.StringVar(value="guepard")
        self.method_var = tk.StringVar(value="forward")
        self._build()
        self.refresh()

    # --- construction ------------------------------------------------------
    def _build(self) -> None:
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 8))
        for text, cmd in (("Exemple « animaux »", self.load_sample), ("Ouvrir…", self.open_file),
                          ("Enregistrer…", self.save_file), ("Vider", self.clear)):
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=(0, 6))
        panes = ttk.PanedWindow(self, orient="horizontal")
        panes.pack(fill="both", expand=True)
        left, right = ttk.Frame(panes), ttk.Frame(panes)
        panes.add(left, weight=3)
        panes.add(right, weight=3)

        facts = ttk.LabelFrame(left, text="BASE DE FAITS", padding=8)
        facts.pack(fill="x")
        holder = ttk.Frame(facts)
        holder.pack(fill="x")
        self.facts_list = tk.Listbox(holder, height=7, activestyle="none", relief="flat", highlightthickness=1,
                                     highlightbackground="#d8dce3", selectbackground="#dbe6fa", selectforeground=INK)
        sb = ttk.Scrollbar(holder, command=self.facts_list.yview)
        self.facts_list.configure(yscrollcommand=sb.set)
        self.facts_list.pack(side="left", fill="x", expand=True)
        sb.pack(side="right", fill="y")
        row = ttk.Frame(facts)
        row.pack(fill="x", pady=(6, 0))
        ttk.Button(row, text="Ajouter", command=self.add_fact).pack(side="left")
        ttk.Button(row, text="Supprimer", command=self.remove_fact).pack(side="left", padx=6)

        rules = ttk.LabelFrame(left, text="BASE DE RÈGLES  (SI … ALORS …)", padding=8)
        rules.pack(fill="both", expand=True, pady=(8, 0))
        holder = ttk.Frame(rules)
        holder.pack(fill="both", expand=True)
        self.rules_tree = ttk.Treeview(holder, columns=("name", "rule"), show="headings", height=10,
                                       selectmode="browse")
        self.rules_tree.heading("name", text="Règle")
        self.rules_tree.heading("rule", text="Définition")
        self.rules_tree.column("name", width=48, stretch=False)
        self.rules_tree.column("rule", width=320)
        sb = ttk.Scrollbar(holder, command=self.rules_tree.yview)
        self.rules_tree.configure(yscrollcommand=sb.set)
        self.rules_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.rules_tree.bind("<Double-Button-1>", lambda _e: self.edit_rule())
        row = ttk.Frame(rules)
        row.pack(fill="x", pady=(6, 0))
        ttk.Button(row, text="Ajouter", command=self.add_rule).pack(side="left")
        ttk.Button(row, text="Modifier", command=self.edit_rule).pack(side="left", padx=6)
        ttk.Button(row, text="Supprimer", command=self.remove_rule).pack(side="left")

        box = ttk.LabelFrame(right, text="RAISONNEMENT", padding=10)
        box.pack(fill="both", expand=True, padx=(10, 0))
        row = ttk.Frame(box)
        row.pack(fill="x")
        ttk.Label(row, text="Objectif à démontrer").pack(side="left")
        self.goal_box = ttk.Combobox(row, textvariable=self.goal_var, width=26)
        self.goal_box.pack(side="left", padx=8)
        self.goal_box.bind("<<ComboboxSelected>>", lambda _e: self._goal_changed())
        self.goal_box.bind("<KeyRelease>", lambda _e: self._goal_changed())
        self.goal_status = ttk.Label(box, text="", style="Muted.TLabel")
        self.goal_status.pack(anchor="w", pady=(4, 8))
        row = ttk.Frame(box)
        row.pack(fill="x")
        ttk.Label(row, text="Méthode").pack(side="left")
        for key, (label, _) in METHODS.items():
            ttk.Radiobutton(row, text=label, value=key, variable=self.method_var,
                            command=self._reset_run).pack(side="left", padx=(12, 0))
        ctrl = ttk.Frame(box)
        ctrl.pack(fill="x", pady=10)
        ttk.Button(ctrl, text="▶  Lancer", style="Accent.TButton", command=self.run).pack(side="left")
        self.btn_prev = ttk.Button(ctrl, text="◀ Précédent", command=self.prev, state="disabled")
        self.btn_next = ttk.Button(ctrl, text="Suivant ▶", command=self.next, state="disabled")
        self.btn_all = ttk.Button(ctrl, text="Tout afficher", command=self.show_all, state="disabled")
        self.btn_play = ttk.Button(ctrl, text="⏵ Lecture", command=self.toggle_play, state="disabled")
        for b in (self.btn_prev, self.btn_next, self.btn_all, self.btn_play):
            b.pack(side="left", padx=(6, 0))
        self.step_var = tk.StringVar(value="")
        ttk.Label(ctrl, textvariable=self.step_var, style="Muted.TLabel").pack(side="right")
        holder = ttk.Frame(box)
        holder.pack(fill="both", expand=True)
        self.trace = tk.Text(holder, wrap="word", height=14, state="disabled", relief="flat", padx=8, pady=6,
                             font=("TkFixedFont", 10), highlightthickness=1, highlightbackground="#d8dce3")
        sb = ttk.Scrollbar(holder, command=self.trace.yview)
        self.trace.configure(yscrollcommand=sb.set)
        self.trace.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        for kind, opts in _TAGS.items():
            self.trace.tag_configure(kind, **opts)
        self.trace.tag_configure("now", background="#fff6cf")
        self.derived_var = tk.StringVar(value="")
        ttk.Label(box, textvariable=self.derived_var, style="Muted.TLabel", wraplength=520).pack(anchor="w", pady=(8, 0))
        self.conclusion = ttk.Label(box, text="", style="Result.TLabel", padding=8, wraplength=520)
        self.conclusion.pack(fill="x", pady=(8, 0))

    # --- base ------------------------------------------------------------------
    def refresh(self) -> None:
        self.facts_list.delete(0, "end")
        for fact in self.kb.facts:
            self.facts_list.insert("end", fact)
        self.rules_tree.delete(*self.rules_tree.get_children())
        for rule in self.kb.rules:
            text = f"SI {' ET '.join(rule.conditions)} ALORS {rule.conclusion}"
            self.rules_tree.insert("", "end", iid=rule.name, values=(rule.name, text))
        self.goal_box.configure(values=self.kb.symbols())
        self._reset_run()
        self._goal_changed()

    def _goal_changed(self) -> None:
        goal = self.goal_var.get().strip()
        if not goal:
            self.goal_status.configure(text="Choisissez un objectif.", foreground=MUTED)
            return
        goal = normalize_fact(goal)
        if self.kb.has_fact(goal):
            self.goal_status.configure(text="✔ Déjà présent dans la base de faits — rien à démontrer.", foreground=OK)
        elif any(r.conclusion == goal for r in self.kb.rules):
            self.goal_status.configure(text="À démontrer : absent de la base de faits.", foreground=INK)
        else:
            self.goal_status.configure(text="⚠ Absent des faits et aucune règle ne le conclut.", foreground=WARN)
        if self.result is not None and self.result.goal != goal:
            self._reset_run()

    @guarded
    def add_fact(self) -> None:
        raw = dialogs.ask_text(self, "Ajouter des faits", "Fait(s) à ajouter (séparés par des virgules) :")
        if raw:
            for fact in raw.split(","):
                if fact.strip():
                    self.kb.add_fact(fact)
            self.refresh()

    @guarded
    def remove_fact(self) -> None:
        for index in reversed(self.facts_list.curselection()):
            self.kb.remove_fact(self.facts_list.get(index))
        self.refresh()

    def _selected_rule(self) -> str | None:
        selection = self.rules_tree.selection()
        return selection[0] if selection else None

    @guarded
    def add_rule(self) -> None:
        raw = dialogs.ask_text(self, "Nouvelle règle", "SI a ET b ALORS c   (ou : a, b -> c)")
        if raw:
            conditions, conclusion = parse_rule(raw)
            self.kb.add_rule(conditions, conclusion)
            self.refresh()

    @guarded
    def edit_rule(self) -> None:
        name = self._selected_rule()
        if name is None:
            return
        rule = self.kb.get_rule(name)
        current = f"SI {' ET '.join(rule.conditions)} ALORS {rule.conclusion}"
        raw = dialogs.ask_text(self, f"Modifier {name}", "SI a ET b ALORS c", current)
        if raw:
            conditions, conclusion = parse_rule(raw)
            self.kb.update_rule(name, conditions, conclusion)
            self.refresh()

    @guarded
    def remove_rule(self) -> None:
        name = self._selected_rule()
        if name:
            self.kb.remove_rule(name)
            self.refresh()

    @guarded
    def clear(self) -> None:
        if dialogs.confirm(self, "Vider la base", "Supprimer tous les faits et toutes les règles ?"):
            self.kb.clear()
            self.goal_var.set("")
            self.refresh()

    def load_sample(self) -> None:
        self.kb = animal_kb()
        self.goal_var.set("guepard")
        self.refresh()

    @guarded
    def open_file(self) -> None:
        path = filedialog.askopenfilename(parent=self, title="Ouvrir une base de connaissances",
                                          initialdir="data/expert" if Path("data/expert").is_dir() else ".",
                                          filetypes=[("Base JSON", "*.json"), ("Tous", "*.*")])
        if path:
            self.kb = load_kb(path)
            self.refresh()

    @guarded
    def save_file(self) -> None:
        path = filedialog.asksaveasfilename(parent=self, title="Enregistrer la base", defaultextension=".json",
                                            filetypes=[("Base JSON", "*.json")])
        if path:
            save_kb(self.kb, path)

    # --- raisonnement ------------------------------------------------------------
    def _reset_run(self) -> None:
        self._stop()
        self.result = self.player = None
        self.step_var.set("")
        self.derived_var.set("")
        self.conclusion.configure(text="", foreground=INK)
        self._set_text("")
        for b in (self.btn_prev, self.btn_next, self.btn_all, self.btn_play):
            b.configure(state="disabled")

    @guarded
    def run(self) -> None:
        goal = self.goal_var.get().strip()
        if not goal:
            raise ValueError("Choisissez d'abord l'objectif à démontrer.")
        self._reset_run()
        self.result = METHODS[self.method_var.get()][1](self.kb, goal)
        self.player = Player(len(self.result.trace))
        self._render()

    def _set_text(self, content: str) -> None:
        self.trace.configure(state="normal")
        self.trace.delete("1.0", "end")
        if content:
            self.trace.insert("end", content)
        self.trace.configure(state="disabled")

    def _render(self) -> None:
        r, p = self.result, self.player
        if r is None or p is None:
            return
        self.trace.configure(state="normal")
        self.trace.delete("1.0", "end")
        shown = r.trace[: p.position + 1]
        for number, event in enumerate(shown, 1):
            tags = (event.kind,) + (("now",) if number == len(shown) else ())
            line = f"{number:>3}. {'   ' * event.depth}{_ICONS.get(event.kind, ' ')} {event.message}\n"
            self.trace.insert("end", line, tags)
        self.trace.configure(state="disabled")
        self.trace.see("end")
        self.step_var.set(f"Étape {p.position + 1} / {p.count}")
        produced = sum(1 for e in shown if e.kind in ("fire", "proved"))
        self.derived_var.set("Faits déduits : " + (", ".join(r.derived_facts[:produced]) or "—"))
        if p.at_end:
            if r.success:
                chain = " → ".join(r.rules_used) if r.rules_used else "aucune règle nécessaire"
                self.conclusion.configure(text=f"✔ Objectif « {r.goal} » démontré.   Règles : {chain}", foreground=OK)
            else:
                self.conclusion.configure(text=f"✘ Objectif « {r.goal} » NON démontrable avec cette base.",
                                          foreground=ERR)
        else:
            self.conclusion.configure(text="", foreground=INK)
        busy = self._job is not None
        self.btn_prev.configure(state="normal" if not p.at_start else "disabled")
        self.btn_next.configure(state="normal" if not p.at_end else "disabled")
        self.btn_all.configure(state="normal" if not p.at_end else "disabled")
        self.btn_play.configure(state="normal" if (not p.at_end or busy) else "disabled",
                                text="⏸ Pause" if busy else "⏵ Lecture")

    def next(self) -> None:
        self._stop()
        if self.player and self.player.next():
            self._render()

    def prev(self) -> None:
        self._stop()
        if self.player and self.player.prev():
            self._render()

    def show_all(self) -> None:
        self._stop()
        if self.player:
            self.player.last()
            self._render()

    def toggle_play(self) -> None:
        if self._job is not None:
            self._stop()
            self._render()
        elif self.player and not self.player.at_end:
            self._job = self.after(650, self._tick)
            self._render()

    def _tick(self) -> None:
        self._job = None
        if self.player and self.player.next():
            if not self.player.at_end:
                self._job = self.after(650, self._tick)
            self._render()

    def _stop(self) -> None:
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None
