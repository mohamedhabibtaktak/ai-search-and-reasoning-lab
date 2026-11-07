"""Libellés des étapes de recherche, partagés par le CLI et la GUI."""
from __future__ import annotations

from .algorithms.base import Step

_TITLES = {"init": "Initialisation", "goal": "But atteint : {c}", "stop": "Arrêt",
           "cutoff": "Coupure en {c}", "skip": "Ignoré : {c}"}


def step_title(step: Step) -> str:
    """Titre court d'une étape (vide pour les séparateurs « info »)."""
    if step.action == "info":
        return ""
    return _TITLES.get(step.action, "Développement de {c}").format(c=step.current)


def step_details(step: Step) -> list[str]:
    """Lignes de détail : note, frontière, explorés."""
    lines = [step.note] if step.note else []
    if step.frontier_labels or step.action in ("init", "expand", "goal"):
        lines.append("Frontière : " + (", ".join(step.frontier_labels) or "∅"))
    if step.explored:
        lines.append("Explorés : " + ", ".join(step.explored))
    return lines
