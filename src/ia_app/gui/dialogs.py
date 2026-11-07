"""Boîtes de dialogue + garde-fou d'erreurs. Fonctions isolées pour pouvoir être remplacées dans les tests."""
from __future__ import annotations

import tkinter as tk
from functools import wraps
from tkinter import messagebox, simpledialog, ttk

from ..common.errors import AppError, GraphError


def guarded(method):
    """Affiche toute erreur métier dans une boîte de dialogue au lieu de planter."""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except (AppError, ValueError) as exc:
            messagebox.showerror("Erreur", str(exc), parent=self)
            return None
    return wrapper


def ask_text(parent, title: str, prompt: str, initial: str = "") -> str | None:
    value = simpledialog.askstring(title, prompt, initialvalue=initial, parent=parent)
    return value.strip() if value and value.strip() else None


def ask_number(parent, title: str, prompt: str, initial: str = "") -> float | None:
    raw = ask_text(parent, title, prompt, initial)
    if raw is None:
        return None
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        raise GraphError(f"« {raw} » n'est pas un nombre.") from None


def confirm(parent, title: str, message: str) -> bool:
    return messagebox.askyesno(title, message, parent=parent)


class _EdgeDialog(tk.Toplevel):
    def __init__(self, parent, vertices: list[str], src: str, dst: str, cost: str) -> None:
        super().__init__(parent)
        self.title("Ajouter un arc orienté")
        self.transient(parent.winfo_toplevel())
        self.resizable(False, False)
        self.result: tuple[str, str, str, bool] | None = None
        body = ttk.Frame(self, padding=16)
        body.pack(fill="both", expand=True)
        self._src, self._dst = tk.StringVar(value=src), tk.StringVar(value=dst)
        self._cost, self._both = tk.StringVar(value=cost), tk.BooleanVar(value=False)
        for row, (label, var) in enumerate((("De", self._src), ("Vers", self._dst))):
            ttk.Label(body, text=label).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Combobox(body, textvariable=var, values=vertices, width=22).grid(row=row, column=1, pady=4, padx=(10, 0))
        ttk.Label(body, text="Coût").grid(row=2, column=0, sticky="w", pady=4)
        entry = ttk.Entry(body, textvariable=self._cost, width=24)
        entry.grid(row=2, column=1, pady=4, padx=(10, 0))
        ttk.Checkbutton(body, text="Ajouter aussi l'arc inverse (même coût)", variable=self._both).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(6, 10))
        buttons = ttk.Frame(body)
        buttons.grid(row=4, column=0, columnspan=2, sticky="e")
        ttk.Button(buttons, text="Annuler", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="Ajouter", style="Accent.TButton", command=self._ok).pack(side="right", padx=8)
        self.bind("<Return>", lambda _e: self._ok())
        self.bind("<Escape>", lambda _e: self.destroy())
        entry.focus_set()
        self.grab_set()

    def _ok(self) -> None:
        self.result = (self._src.get(), self._dst.get(), self._cost.get(), self._both.get())
        self.destroy()


def ask_edge(parent, vertices: list[str], src: str = "", dst: str = "", cost: str = ""):
    """Renvoie (src, dst, coût en float, arc_inverse) ou None si annulé."""
    dialog = _EdgeDialog(parent, vertices, src, dst, cost)
    parent.wait_window(dialog)
    if dialog.result is None:
        return None
    s, d, c, both = dialog.result
    try:
        value = float(c.replace(",", "."))
    except ValueError:
        raise GraphError(f"Le coût « {c} » n'est pas un nombre.") from None
    return s, d, value, both
