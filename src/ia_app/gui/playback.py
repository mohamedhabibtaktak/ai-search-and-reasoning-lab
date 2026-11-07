"""Lecteur d'étapes (précédent / suivant / début / fin) indépendant de Tk, donc testable."""
from __future__ import annotations


class Player:
    def __init__(self, count: int) -> None:
        self.count = max(count, 0)
        self.position = 0          # index de l'étape courante (0-based)

    @property
    def at_start(self) -> bool:
        return self.position <= 0

    @property
    def at_end(self) -> bool:
        return self.position >= self.count - 1

    def next(self) -> bool:
        if self.at_end:
            return False
        self.position += 1
        return True

    def prev(self) -> bool:
        if self.at_start:
            return False
        self.position -= 1
        return True

    def first(self) -> None:
        self.position = 0

    def last(self) -> None:
        self.position = max(self.count - 1, 0)
