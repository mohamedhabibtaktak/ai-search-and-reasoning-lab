"""Moteur de menu générique : une erreur métier affiche un message, jamais une trace Python."""
from __future__ import annotations

from typing import Callable, Sequence

from ..common.errors import AppError
from .console import Console

Action = Callable[[], "bool | None"]


def run_menu(console: Console, title: str, entries: Sequence[tuple[str, Action]], *,
             back: str | None = "Retour", status: Callable[[], str] | None = None) -> None:
    """Boucle de menu. Une action qui renvoie True ferme le menu (ex. « Quitter »)."""
    while True:
        console.header(title)
        if status:
            console.say(status(), "dim")
        index = console.pick("", [label for label, _ in entries], back=back)
        if index is None:
            return
        try:
            if entries[index][1]():
                return
        except AppError as exc:
            console.error(str(exc))
