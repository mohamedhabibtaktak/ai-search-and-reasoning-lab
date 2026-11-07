"""Entrées/sorties du terminal, isolées pour être testables (entrées injectables, couleurs optionnelles)."""
from __future__ import annotations

import os
import sys
from typing import Callable, Sequence, TextIO

_STYLES = {"title": "1;36", "ok": "32", "warn": "33", "err": "31", "dim": "90", "bold": "1", "hot": "1;35"}
WIDTH = 72


class UserAbort(Exception):
    """Fin de saisie (Ctrl-D / Ctrl-C) : on quitte proprement."""


class Console:
    def __init__(self, input_fn: Callable[[str], str] | None = None, output: TextIO | None = None,
                 color: bool | None = None) -> None:
        self._input = input_fn or input
        self._out = output or sys.stdout
        if color is None:
            color = output is None and sys.stdout.isatty() and "NO_COLOR" not in os.environ
        self.color = color

    # --- sortie ------------------------------------------------------
    def paint(self, text: str, style: str | None) -> str:
        return f"\033[{_STYLES[style]}m{text}\033[0m" if self.color and style else text

    def say(self, text: str = "", style: str | None = None) -> None:
        print(self.paint(text, style), file=self._out)

    def ok(self, text: str) -> None:
        self.say(f"✔ {text}", "ok")

    def warn(self, text: str) -> None:
        self.say(f"⚠ {text}", "warn")

    def error(self, text: str) -> None:
        self.say(f"✘ {text}", "err")

    def header(self, title: str) -> None:
        self.say()
        self.say("═" * WIDTH, "title")
        self.say(f"  {title}", "title")
        self.say("═" * WIDTH, "title")

    def rule(self, title: str = "") -> None:
        self.say(f"── {title} " + "─" * max(WIDTH - len(title) - 4, 2) if title else "─" * WIDTH, "dim")

    # --- entrée ------------------------------------------------------
    def ask(self, prompt: str, default: str | None = None) -> str:
        suffix = f" [{default}]" if default else ""
        try:
            raw = self._input(f"{prompt}{suffix} › ").strip()
        except (EOFError, KeyboardInterrupt):
            raise UserAbort from None
        return raw or (default or "")

    def ask_required(self, prompt: str, default: str | None = None) -> str:
        while True:
            value = self.ask(prompt, default)
            if value:
                return value
            self.warn("Une valeur est requise.")

    def ask_float(self, prompt: str, default: float | None = None, minimum: float | None = None) -> float:
        while True:
            raw = self.ask(prompt, None if default is None else f"{default:g}").replace(",", ".")
            try:
                value = float(raw)
            except ValueError:
                self.warn("Entrez un nombre (ex. 12 ou 2.5).")
                continue
            if value != value or value in (float("inf"), float("-inf")):
                self.warn("Entrez un nombre fini.")
            elif minimum is not None and value < minimum:
                self.warn(f"La valeur doit être ≥ {minimum:g}.")
            else:
                return value

    def ask_int(self, prompt: str, minimum: int, maximum: int | None = None, default: int | None = None) -> int:
        while True:
            raw = self.ask(prompt, None if default is None else str(default))
            try:
                value = int(raw)
            except ValueError:
                self.warn("Entrez un nombre entier.")
                continue
            if value < minimum or (maximum is not None and value > maximum):
                self.warn(f"Valeur attendue entre {minimum} et {maximum if maximum is not None else '∞'}.")
            else:
                return value

    def confirm(self, prompt: str, default: bool = False) -> bool:
        hint = "O/n" if default else "o/N"
        while True:
            raw = self.ask(f"{prompt} ({hint})").lower()
            if not raw:
                return default
            if raw in ("o", "oui", "y", "yes"):
                return True
            if raw in ("n", "non", "no"):
                return False
            self.warn("Répondez par o (oui) ou n (non).")

    def pick(self, title: str, options: Sequence[str], *, back: str | None = "Retour") -> int | None:
        """Affiche une liste numérotée ; renvoie l'index (0-based) ou None pour « retour »."""
        self.say(title, "bold")
        for i, label in enumerate(options, 1):
            self.say(f"  {i}. {label}")
        if back:
            self.say(f"  0. {back}", "dim")
        low = 0 if back else 1
        while True:
            choice = self.ask_int("Votre choix", low, len(options))
            return None if choice == 0 else choice - 1

    def pause(self, prompt: str = "Entrée = étape suivante · a = tout afficher") -> bool:
        """Renvoie False si l'utilisateur demande l'affichage direct (« a »)."""
        return self.ask(self.paint(prompt, "dim")).lower() not in ("a", "q")
