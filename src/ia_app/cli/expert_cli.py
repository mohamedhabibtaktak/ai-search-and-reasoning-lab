"""Module 1 — Systèmes experts (interface en ligne de commande)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..common.errors import KnowledgeBaseError
from ..expert import (InferenceResult, KnowledgeBase, backward_chaining, forward_chaining,
                      normalize_fact, parse_rule)
from ..expert.samples import animal_kb
from ..expert.storage import load_kb, save_kb
from .console import Console
from .menu import run_menu

METHODS = {"forward": ("Chaînage avant (forward chaining)", forward_chaining),
           "backward": ("Chaînage arrière (backward chaining)", backward_chaining)}
DEFAULT_PATH = "data/expert/ma_base.json"


@dataclass
class ExpertSession:
    kb: KnowledgeBase
    goal: str | None = None
    method: str = "forward"
    step_by_step: bool = True


def _status(s: ExpertSession) -> str:
    mode = "pas à pas" if s.step_by_step else "direct"
    return (f"Objectif : {s.goal or '— (non défini)'}  |  Méthode : {METHODS[s.method][0]}  |  Exécution : {mode}"
            f"\nBase : {len(s.kb.facts)} fait(s), {len(s.kb.rules)} règle(s)")


# --- 1. présentation ----------------------------------------------------
def show_base(console: Console, s: ExpertSession) -> None:
    console.rule("Base de faits")
    for fact in s.kb.facts or ["(aucun fait)"]:
        console.say(f"  • {fact}")
    console.rule("Base de règles")
    for rule in s.kb.rules or ["(aucune règle)"]:
        console.say(f"  {rule}")


# --- 2. objectif -----------------------------------------------------------
def choose_goal(console: Console, s: ExpertSession) -> None:
    symbols = s.kb.symbols()
    if symbols:
        console.say("Faits connus de la base : " + ", ".join(symbols), "dim")
    raw = console.ask_required("Fait à démontrer (nom, ou numéro dans la liste ci-dessus)", s.goal)
    s.goal = symbols[int(raw) - 1] if raw.isdigit() and 1 <= int(raw) <= len(symbols) else normalize_fact(raw)
    if s.kb.has_fact(s.goal):
        console.ok(f"« {s.goal} » est déjà présent dans la base de faits (rien à démontrer).")
    else:
        concluders = [r.name for r in s.kb.rules if r.conclusion == s.goal]
        console.say(f"« {s.goal} » n'est pas dans la base de faits : à démontrer.")
        if not concluders:
            console.warn("Aucune règle ne conclut ce fait : il ne pourra pas être démontré.")


# --- 3. méthode ------------------------------------------------------------
def choose_method(console: Console, s: ExpertSession) -> None:
    keys = list(METHODS)
    index = console.pick("Méthode de chaînage :", [METHODS[k][0] for k in keys])
    if index is not None:
        s.method = keys[index]
        console.ok(f"Méthode : {METHODS[s.method][0]}")


def toggle_mode(console: Console, s: ExpertSession) -> None:
    s.step_by_step = not s.step_by_step
    console.ok("Exécution " + ("pas à pas (Entrée pour avancer)." if s.step_by_step else "directe."))


# --- 4. exécution interactive ---------------------------------------------
_ICONS = {"fire": "▶", "goal": "★", "proved": "✔", "known": "✔", "failed": "✘", "cycle-cut": "↺",
          "cycle": "◆", "subgoal": "?", "try": "→", "skip": "·", "info": "i"}
_STYLE = {"goal": "ok", "proved": "ok", "known": "ok", "failed": "err", "cycle-cut": "warn", "fire": "hot"}


def run_inference(console: Console, s: ExpertSession) -> None:
    if not s.goal:
        console.warn("Aucun objectif défini : choisissez-en un.")
        choose_goal(console, s)
    label, engine = METHODS[s.method]
    console.header(f"{label} — objectif : {s.goal}")
    result = engine(s.kb, s.goal)
    stepping = s.step_by_step
    for number, event in enumerate(result.trace, 1):
        indent = "  " * event.depth
        console.say(f"{number:>3}. {indent}{_ICONS.get(event.kind, ' ')} {event.message}", _STYLE.get(event.kind))
        if stepping and number < len(result.trace):
            stepping = console.pause()
    print_conclusion(console, result)


def print_conclusion(console: Console, r: InferenceResult) -> None:
    console.rule("Conclusion")
    if r.success:
        console.ok(f"Objectif « {r.goal} » démontré.")
        if r.rules_used:
            console.say("  Règles utilisées (dans l'ordre) : " + " → ".join(r.rules_used))
        if r.derived_facts:
            console.say("  Faits déduits : " + ", ".join(r.derived_facts))
    else:
        console.error(f"Objectif « {r.goal} » NON démontrable avec cette base.")


# --- 5. personnalisation ---------------------------------------------------
def add_fact(console: Console, s: ExpertSession) -> None:
    for fact in console.ask_required("Fait(s) à ajouter (séparés par des virgules)").split(","):
        if fact.strip():
            if s.kb.add_fact(fact):
                console.ok(f"Ajouté : {normalize_fact(fact)}")
            else:
                console.warn(f"Déjà présent : {normalize_fact(fact)}")


def remove_fact(console: Console, s: ExpertSession) -> None:
    fact = console.ask_required("Fait à supprimer")
    if s.kb.remove_fact(fact):
        console.ok("Fait supprimé.")
    else:
        console.warn("Ce fait n'existe pas.")


def _read_rule(console: Console) -> tuple[list[str], str]:
    console.say("Format : « SI a ET b ALORS c »  ou  « a, b -> c »", "dim")
    return parse_rule(console.ask_required("Règle"))


def add_rule(console: Console, s: ExpertSession) -> None:
    conditions, conclusion = _read_rule(console)
    console.ok(f"Règle ajoutée : {s.kb.add_rule(conditions, conclusion)}")


def edit_rule(console: Console, s: ExpertSession) -> None:
    name = console.ask_required("Nom de la règle à modifier (ex. R3)")
    console.say(f"Actuelle : {s.kb.get_rule(name)}", "dim")
    conditions, conclusion = _read_rule(console)
    console.ok(f"Règle modifiée : {s.kb.update_rule(name, conditions, conclusion)}")


def remove_rule(console: Console, s: ExpertSession) -> None:
    console.ok(f"Supprimée : {s.kb.remove_rule(console.ask_required('Nom de la règle à supprimer'))}")


def customize(console: Console, s: ExpertSession) -> None:
    run_menu(console, "Personnaliser la base", [
        ("Ajouter des faits", lambda: add_fact(console, s)),
        ("Supprimer un fait", lambda: remove_fact(console, s)),
        ("Ajouter une règle", lambda: add_rule(console, s)),
        ("Modifier une règle", lambda: edit_rule(console, s)),
        ("Supprimer une règle", lambda: remove_rule(console, s)),
        ("Afficher la base", lambda: show_base(console, s)),
        ("Vider la base", lambda: _clear(console, s)),
    ], status=lambda: _status(s))


def _clear(console: Console, s: ExpertSession) -> None:
    if console.confirm("Supprimer tous les faits et toutes les règles ?"):
        s.kb.clear()
        s.goal = None
        console.ok("Base vidée.")


# --- persistance -----------------------------------------------------------
def save(console: Console, s: ExpertSession) -> None:
    path = console.ask("Fichier de sauvegarde", DEFAULT_PATH)
    console.ok(f"Base enregistrée dans {save_kb(s.kb, path)}")


def load(console: Console, s: ExpertSession) -> None:
    path = console.ask("Fichier à charger", DEFAULT_PATH)
    if not Path(path).exists():
        raise KnowledgeBaseError(f"Fichier introuvable : « {path} ».")
    s.kb = load_kb(path)
    s.goal = None
    console.ok(f"Base chargée : {len(s.kb.facts)} fait(s), {len(s.kb.rules)} règle(s).")


def load_sample(console: Console, s: ExpertSession) -> None:
    s.kb, s.goal = animal_kb(), "guepard"
    console.ok("Exemple chargé (identification d'animaux). Objectif proposé : guepard.")


def expert_menu(console: Console, session: ExpertSession | None = None) -> None:
    s = session or ExpertSession(animal_kb(), goal="guepard")
    run_menu(console, "SYSTÈMES EXPERTS", [
        ("Afficher la base de faits et de règles", lambda: show_base(console, s)),
        ("Choisir l'objectif à démontrer", lambda: choose_goal(console, s)),
        ("Choisir la méthode (avant / arrière)", lambda: choose_method(console, s)),
        ("Lancer le raisonnement", lambda: run_inference(console, s)),
        ("Basculer pas à pas / direct", lambda: toggle_mode(console, s)),
        ("Personnaliser faits et règles", lambda: customize(console, s)),
        ("Sauvegarder la base (JSON)", lambda: save(console, s)),
        ("Charger une base (JSON)", lambda: load(console, s)),
        ("Charger l'exemple « animaux »", lambda: load_sample(console, s)),
    ], back="Retour au menu principal", status=lambda: _status(s))
