"""Chaînage arrière : on part du but et on cherche à le démontrer à partir des faits (DFS sur les règles)."""
from __future__ import annotations

from .inference import InferenceResult, TraceEvent
from .models import KnowledgeBase, normalize_fact


class _Prover:
    def __init__(self, kb: KnowledgeBase, result: InferenceResult) -> None:
        self.kb = kb
        self.facts = set(kb.facts)
        self.result = result
        self.proven: set[str] = set()      # buts démontrés (mémoïsation)
        self.failed: set[str] = set()      # buts non démontrables (mémoïsation sûre)
        self.stack: list[str] = []         # buts en cours : détection de cycles
        self.cycle_cuts = 0                # nb de coupes dues à un cycle

    def log(self, kind: str, message: str, depth: int) -> None:
        self.result.trace.append(TraceEvent(kind, message, depth))

    def prove(self, goal: str, depth: int = 0) -> bool:
        if goal in self.facts or goal in self.proven:
            self.log("known", f"« {goal} » est connu ✔", depth)
            return True
        if goal in self.failed:
            self.log("failed", f"« {goal} » : déjà échoué plus tôt ✘", depth)
            return False
        if goal in self.stack:
            self.cycle_cuts += 1
            self.log("cycle-cut", f"« {goal} » est déjà en cours de démonstration : cycle coupé ✘", depth)
            return False

        candidates = [r for r in self.kb.rules if r.conclusion == goal]
        self.log("subgoal", f"But : démontrer « {goal} »", depth)
        if not candidates:
            self.failed.add(goal)
            self.log("failed", f"Aucune règle ne conclut « {goal} » et ce n'est pas un fait ✘", depth)
            return False

        cuts_before = self.cycle_cuts
        self.stack.append(goal)
        try:
            for rule in candidates:
                self.log("try", f"Essai de {rule}", depth + 1)
                if all(self.prove(cond, depth + 2) for cond in rule.conditions):
                    self.proven.add(goal)
                    self.result.rules_used.append(rule.name)
                    self.result.derived_facts.append(goal)
                    self.log("proved", f"{rule.name} appliquée ⇒ « {goal} » démontré ✔", depth + 1)
                    return True
                self.log("failed", f"{rule.name} échoue (une condition n'est pas démontrable)", depth + 1)
        finally:
            self.stack.pop()
        # Un échec causé par un cycle dépend du contexte : on ne le mémorise pas.
        if self.cycle_cuts == cuts_before:
            self.failed.add(goal)
        self.log("failed", f"« {goal} » non démontrable ✘", depth)
        return False


def backward_chaining(kb: KnowledgeBase, goal: str) -> InferenceResult:
    goal = normalize_fact(goal)
    result = InferenceResult("backward", goal, False)
    result.success = _Prover(kb, result).prove(goal)
    return result
