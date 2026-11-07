"""Modèles du système expert : règles « SI conditions ALORS conclusion » et base de connaissances."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

from ..common.errors import KnowledgeBaseError


def normalize_fact(text: str) -> str:
    """Normalise un fait (espaces réduits, minuscules). Refuse le vide."""
    value = re.sub(r"\s+", " ", str(text).strip()).lower()
    if not value:
        raise KnowledgeBaseError("Un fait ne peut pas être vide.")
    return value


@dataclass(frozen=True)
class Rule:
    """Règle de production : toutes les conditions (ET) impliquent la conclusion."""

    name: str
    conditions: tuple[str, ...]
    conclusion: str

    @classmethod
    def create(cls, name: str, conditions: Iterable[str], conclusion: str) -> "Rule":
        name = name.strip()
        if not name or re.search(r"\s", name):
            raise KnowledgeBaseError("Le nom d'une règle est obligatoire et sans espace (ex. R1).")
        conds = tuple(dict.fromkeys(normalize_fact(c) for c in conditions))  # dédoublonne, garde l'ordre
        if not conds:
            raise KnowledgeBaseError("Une règle doit avoir au moins une condition.")
        concl = normalize_fact(conclusion)
        if concl in conds:
            raise KnowledgeBaseError(f"Règle tautologique : la conclusion « {concl} » figure dans ses conditions.")
        return cls(name, conds, concl)

    def __str__(self) -> str:
        return f"{self.name} : SI {' ET '.join(self.conditions)} ALORS {self.conclusion}"


_ARROW = re.compile(r"\s*(?:->|=>|\bALORS\b)\s*", re.IGNORECASE)
_AND = re.compile(r"\s*(?:,|&|\bET\b)\s*", re.IGNORECASE)


def parse_rule(text: str) -> tuple[list[str], str]:
    """Lit « SI a ET b ALORS c », « a, b -> c » ou « a & b => c »."""
    parts = _ARROW.split(text.strip(), maxsplit=1)
    if len(parts) != 2:
        raise KnowledgeBaseError("Format attendu : « SI a ET b ALORS c » ou « a, b -> c ».")
    left = re.sub(r"^\s*SI\b", "", parts[0], flags=re.IGNORECASE)
    conditions = [c.strip() for c in _AND.split(left) if c.strip()]
    return conditions, parts[1].strip()


class KnowledgeBase:
    """Base de faits (ensemble ordonné) + base de règles (liste ordonnée, noms uniques)."""

    def __init__(self, facts: Iterable[str] = (), rules: Iterable[Rule] = ()) -> None:
        self._facts: dict[str, None] = {}
        self._rules: list[Rule] = []
        for fact in facts:
            self.add_fact(fact)
        for rule in rules:
            self._insert(rule)

    # --- faits -------------------------------------------------------
    @property
    def facts(self) -> list[str]:
        return list(self._facts)

    def has_fact(self, fact: str) -> bool:
        return normalize_fact(fact) in self._facts

    def add_fact(self, fact: str) -> bool:
        """Ajoute un fait ; renvoie False s'il existait déjà."""
        value = normalize_fact(fact)
        if value in self._facts:
            return False
        self._facts[value] = None
        return True

    def remove_fact(self, fact: str) -> bool:
        return self._facts.pop(normalize_fact(fact), "absent") != "absent"

    # --- règles ------------------------------------------------------
    @property
    def rules(self) -> tuple[Rule, ...]:
        return tuple(self._rules)

    def get_rule(self, name: str) -> Rule:
        for rule in self._rules:
            if rule.name == name.strip():
                return rule
        raise KnowledgeBaseError(f"Règle inconnue : « {name} ».")

    def _insert(self, rule: Rule) -> Rule:
        if any(r.name == rule.name for r in self._rules):
            raise KnowledgeBaseError(f"Une règle nommée « {rule.name} » existe déjà.")
        self._rules.append(rule)
        return rule

    def _next_name(self) -> str:
        used = {r.name for r in self._rules}
        n = 1
        while f"R{n}" in used:
            n += 1
        return f"R{n}"

    def add_rule(self, conditions: Iterable[str], conclusion: str, name: str | None = None) -> Rule:
        return self._insert(Rule.create(name or self._next_name(), conditions, conclusion))

    def update_rule(self, name: str, conditions: Iterable[str], conclusion: str) -> Rule:
        old = self.get_rule(name)
        new = Rule.create(old.name, conditions, conclusion)
        self._rules[self._rules.index(old)] = new
        return new

    def remove_rule(self, name: str) -> Rule:
        rule = self.get_rule(name)
        self._rules.remove(rule)
        return rule

    # --- utilitaires -------------------------------------------------
    def symbols(self) -> list[str]:
        """Tous les faits mentionnés (faits, conditions, conclusions), triés."""
        found = set(self._facts)
        for rule in self._rules:
            found.update(rule.conditions)
            found.add(rule.conclusion)
        return sorted(found)

    def clear(self) -> None:
        self._facts.clear()
        self._rules.clear()

    def copy(self) -> "KnowledgeBase":
        return KnowledgeBase(self._facts, self._rules)

    # --- (dé)sérialisation ------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {
            "facts": self.facts,
            "rules": [{"name": r.name, "if": list(r.conditions), "then": r.conclusion} for r in self._rules],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeBase":
        try:
            facts = data.get("facts", [])
            raw_rules = data.get("rules", [])
            if not isinstance(facts, list) or not isinstance(raw_rules, list):
                raise TypeError
            kb = cls(facts)
            for item in raw_rules:
                kb._insert(Rule.create(str(item["name"]), item["if"], item["then"]))
        except (KeyError, TypeError, AttributeError):
            raise KnowledgeBaseError(
                "Base de connaissances invalide : attendu {\"facts\": [...], "
                "\"rules\": [{\"name\", \"if\": [...], \"then\"}]}."
            ) from None
        return kb
