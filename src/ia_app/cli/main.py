"""Point d'entrée : menu principal (Systèmes experts / Algorithmes de recherche / Quitter)."""
from __future__ import annotations

import argparse
from typing import Sequence

from .. import __version__
from .console import Console, UserAbort
from .expert_cli import ExpertSession, expert_menu
from .menu import run_menu
from .search_cli import SearchSession, search_menu
from ..expert.samples import animal_kb


def _quit() -> bool:
    return True


def main(argv: Sequence[str] | None = None, console: Console | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ia-app", description="IA & ML — Assignment 1 (II2)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--no-color", action="store_true", help="désactive les couleurs")
    parser.add_argument("--gui", action="store_true", help="lance l'interface graphique (Tkinter)")
    args = parser.parse_args(argv)
    if args.gui:
        try:
            from ..gui.app import launch
        except ImportError:
            print("Tkinter est introuvable. Linux : sudo apt install python3-tk · sinon utilisez le mode console.")
            return 1
        return launch()
    console = console or Console(color=False if args.no_color else None)

    # Les sessions vivent pendant toute l'exécution : revenir au menu ne perd rien.
    expert = ExpertSession(animal_kb(), goal="guepard")
    search = SearchSession()
    try:
        console.say("IA & Machine Learning — Systèmes experts et algorithmes de recherche", "bold")
        run_menu(console, "MENU PRINCIPAL", [
            ("Systèmes experts", lambda: expert_menu(console, expert)),
            ("Algorithmes de recherche", lambda: search_menu(console, search)),
            ("Quitter", _quit),
        ], back=None)
    except UserAbort:
        console.say("\nAu revoir.")
        return 0
    console.say("Au revoir.")
    return 0
