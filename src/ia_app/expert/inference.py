"""Types communs aux deux moteurs d'inférence : trace pas à pas + résultat."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TraceEvent:
    """Une étape du raisonnement.

    kind : "info" | "cycle" | "fire" | "skip" | "goal" | "known" | "try" | "subgoal"
           | "proved" | "failed" | "cycle-cut" | "result"
    depth : niveau d'imbrication (chaînage arrière) pour l'indentation.
    """

    kind: str
    message: str
    depth: int = 0


@dataclass
class InferenceResult:
    method: str                      # "forward" | "backward"
    goal: str
    success: bool
    trace: list[TraceEvent] = field(default_factory=list)
    derived_facts: list[str] = field(default_factory=list)   # faits nouvellement déduits (ordre)
    rules_used: list[str] = field(default_factory=list)      # règles ayant contribué (ordre)
