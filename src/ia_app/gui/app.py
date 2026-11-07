"""Fenêtre principale : menu Module (Systèmes experts / Algorithmes de recherche / Quitter) + deux onglets."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .. import __version__
from .expert_tab import ExpertTab
from .search_tab import SearchTab
from .theme import apply_theme


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("IA & Machine Learning — Systèmes experts et algorithmes de recherche")
        self.geometry("1360x820")
        self.minsize(1120, 700)
        apply_theme(self)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.expert = ExpertTab(self.notebook)
        self.search = SearchTab(self.notebook)
        self.notebook.add(self.expert, text="Systèmes experts")
        self.notebook.add(self.search, text="Algorithmes de recherche")
        self._build_menu()

    def _build_menu(self) -> None:
        bar = tk.Menu(self)
        module = tk.Menu(bar, tearoff=0)
        module.add_command(label="Systèmes experts", accelerator="Ctrl+1", command=lambda: self.notebook.select(0))
        module.add_command(label="Algorithmes de recherche", accelerator="Ctrl+2", command=lambda: self.notebook.select(1))
        module.add_separator()
        module.add_command(label="Quitter", accelerator="Ctrl+Q", command=self.destroy)
        bar.add_cascade(label="Module", menu=module)
        help_menu = tk.Menu(bar, tearoff=0)
        help_menu.add_command(label="À propos", command=lambda: messagebox.showinfo(
            "À propos", f"IA & ML — Assignment 1 (II2)\nVersion {__version__}\n\nSystèmes experts · Algorithmes de recherche",
            parent=self))
        bar.add_cascade(label="Aide", menu=help_menu)
        self.configure(menu=bar)
        self.bind_all("<Control-Key-1>", lambda _e: self.notebook.select(0))
        self.bind_all("<Control-Key-2>", lambda _e: self.notebook.select(1))
        self.bind_all("<Control-q>", lambda _e: self.destroy())


def launch() -> int:
    """Ouvre la GUI. Renvoie 1 (avec un message clair) s'il n'y a pas d'écran disponible."""
    try:
        app = App()
    except tk.TclError as exc:
        print(f"Interface graphique indisponible ({exc}).\nUtilisez le mode console : python run.py")
        return 1
    app.mainloop()
    return 0
