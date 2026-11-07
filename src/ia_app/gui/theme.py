"""Palette et styles ttk : sobre, une seule couleur d'accent (réservée à l'action principale)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

BG, PANEL, INK, MUTED, LINE = "#f4f5f7", "#ffffff", "#1d2430", "#667085", "#d8dce3"
ACCENT, ACCENT_DARK = "#1f5fbf", "#174a96"
OK, ERR, WARN = "#1f8a4c", "#c92a2a", "#b25e00"


def apply_theme(root: tk.Tk) -> None:
    root.configure(background=BG)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=BG, foreground=INK, bordercolor=LINE, focuscolor=BG)
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=INK)
    style.configure("Muted.TLabel", foreground=MUTED)
    style.configure("Title.TLabel", font=("TkDefaultFont", 11, "bold"))
    style.configure("TLabelframe", background=BG, bordercolor=LINE)
    style.configure("TLabelframe.Label", background=BG, foreground=MUTED, font=("TkDefaultFont", 9, "bold"))
    style.configure("TButton", padding=(10, 5), background=PANEL, bordercolor=LINE)
    style.map("TButton", background=[("active", "#eaeef5"), ("disabled", BG)],
              foreground=[("disabled", "#a0a7b4")])
    style.configure("Accent.TButton", background=ACCENT, foreground="white", bordercolor=ACCENT_DARK)
    style.map("Accent.TButton", background=[("active", ACCENT_DARK), ("disabled", "#9db7e3")],
              foreground=[("disabled", "white")])
    style.configure("Treeview", background=PANEL, fieldbackground=PANEL, rowheight=24, bordercolor=LINE)
    style.configure("Treeview.Heading", background="#eaecf0", font=("TkDefaultFont", 9, "bold"))
    style.map("Treeview", background=[("selected", "#dbe6fa")], foreground=[("selected", INK)])
    style.configure("TNotebook", background=BG, bordercolor=LINE)
    style.configure("TNotebook.Tab", padding=(18, 8), background="#e6e9ef")
    style.map("TNotebook.Tab", background=[("selected", PANEL)])
    style.configure("TRadiobutton", background=BG)
    style.configure("TCheckbutton", background=BG)
    style.configure("Result.TLabel", font=("TkDefaultFont", 10, "bold"), background=PANEL)
