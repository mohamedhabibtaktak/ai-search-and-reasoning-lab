"""Chaînage avant : on part des faits et on déclenche les règles jusqu'au but ou au point fixe."""
from __future__ import annotations

from .inference import InferenceResult, TraceEvent
from .models import KnowledgeBase, normalize_fact


def forward_chaining(kb: KnowledgeBase, goal: str) -> InferenceResult:
    """Résolution de conflit : première règle applicable dans l'ordre de la base.

    La base de connaissances d'origine n'est jamais modifiée (travail sur une copie des faits).
    """
    goal = normalize_fact(goal)
    facts = list(kb.facts)
    known = set(facts)
    result = InferenceResult("forward", goal, False)
    trace = result.trace

    trace.append(TraceEvent("info", f"Faits initiaux : {', '.join(facts) or '(aucun)'}"))
    if goal in known:
        trace.append(TraceEvent("goal", f"L'objectif « {goal} » est déjà dans la base de faits."))
        result.success = True
        return result

    fired: set[str] = set()
    cycle = 0
    while True:
        cycle += 1
        applicable = [
            r for r in kb.rules
            if r.name not in fired and all(c in known for c in r.conditions)
        ]
        names = ", ".join(r.name for r in applicable) or "aucune"
        trace.append(TraceEvent("cycle", f"Cycle {cycle} — règles applicables : {names}"))
        if not applicable:
            trace.append(TraceEvent("failed", "Point fixe atteint : plus aucune règle applicable."))
            break
        rule = applicable[0]
        fired.add(rule.name)
        if rule.conclusion in known:
            trace.append(TraceEvent("skip", f"{rule} — conclusion déjà connue, règle ignorée."))
            continue
        known.add(rule.conclusion)
        result.derived_facts.append(rule.conclusion)
        result.rules_used.append(rule.name)
        trace.append(TraceEvent("fire", f"Déclenche {rule}  ⇒  nouveau fait : « {rule.conclusion} »"))
        if rule.conclusion == goal:
            trace.append(TraceEvent("goal", f"Objectif « {goal} » atteint."))
            result.success = True
            break
    return result
