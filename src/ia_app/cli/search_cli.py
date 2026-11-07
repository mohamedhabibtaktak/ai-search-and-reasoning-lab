"""Module 2 — Algorithmes de recherche (interface en ligne de commande)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..common.errors import GraphError, MissingHeuristicError
from ..search import ALGORITHMS, Graph, algorithms_by_category, run_search
from ..search.algorithms import AlgorithmSpec, SearchResult
from ..search.formatting import step_title
from ..search.graph import format_cost
from ..search.samples import romania_graph
from ..search.storage import load_graph, save_graph
from ..search.viz import draw_graph, render_frames, to_dot
from .console import Console
from .menu import run_menu

DEFAULT_PATH = "data/graphs/mon_graphe.json"


@dataclass
class SearchSession:
    graph: Graph = field(default_factory=Graph)
    last_result: SearchResult | None = None
    step_by_step: bool = True


def _status(s: SearchSession) -> str:
    g = s.graph
    return (f"Graphe : {len(g.vertices)} sommet(s), {len(g.edges())} arc(s)  |  "
            f"initial : {g.start or '—'}  |  objectif : {g.goal or '—'}")


# --- affichage du graphe ---------------------------------------------------
def show_graph(console: Console, s: SearchSession) -> None:
    g = s.graph
    if not g.vertices:
        console.warn("Le graphe est vide : construisez-le ou chargez l'exemple.")
        return
    console.rule("Graphe orienté pondéré")
    width = max(len(v) for v in g.vertices)
    for v in g.vertices:
        marks = ("▶" if v == g.start else " ") + ("★" if v == g.goal else " ")
        h = f"h={format_cost(g.heuristics[v])}" if v in g.heuristics else "h=?"
        succ = ", ".join(f"{n}({format_cost(c)})" for n, c in g.successors(v)) or "∅"
        console.say(f" {marks} {v:<{width}}  {h:<8} → {succ}")
    console.say("  ▶ état initial   ★ état objectif   h(n) : heuristique   voisin(coût)", "dim")


# --- construction ----------------------------------------------------------
def add_vertices(console: Console, s: SearchSession) -> None:
    for name in console.ask_required("Sommet(s) à créer (séparés par des virgules)").split(","):
        if name.strip():
            if s.graph.add_vertex(name):
                console.ok(f"Sommet créé : {name.strip()}")
            else:
                console.warn(f"Existe déjà : {name.strip()}")


def add_edge(console: Console, s: SearchSession) -> None:
    src = console.ask_required("Sommet de départ")
    dst = console.ask_required("Sommet d'arrivée")
    cost = console.ask_float("Coût de l'arc", minimum=0)
    missing = [v for v in (src, dst) if not s.graph.has_vertex(v)]
    if missing and not console.confirm(f"Créer le(s) sommet(s) inconnu(s) : {', '.join(missing)} ?", True):
        return
    both = console.confirm("Ajouter aussi l'arc inverse (même coût) ?", False)
    s.graph.add_edge(src, dst, cost, create_missing=True)
    if both:
        s.graph.add_edge(dst, src, cost, create_missing=True)
    console.ok(f"Arc ajouté : {src.strip()} → {dst.strip()} (coût {format_cost(cost)})" + (" et son inverse." if both else "."))


def remove_vertex(console: Console, s: SearchSession) -> None:
    s.graph.remove_vertex(console.ask_required("Sommet à supprimer"))
    console.ok("Sommet supprimé (ainsi que ses arcs).")


def remove_edge(console: Console, s: SearchSession) -> None:
    s.graph.remove_edge(console.ask_required("Départ"), console.ask_required("Arrivée"))
    console.ok("Arc supprimé.")


def set_start_goal(console: Console, s: SearchSession) -> None:
    s.graph.set_start(console.ask_required("État initial", s.graph.start))
    s.graph.set_goal(console.ask_required("État objectif", s.graph.goal))
    console.ok(f"Initial : {s.graph.start}  →  Objectif : {s.graph.goal}")


def set_heuristics(console: Console, s: SearchSession, only_missing: bool = False) -> None:
    targets = s.graph.missing_heuristics() if only_missing else s.graph.vertices
    if not targets:
        console.ok("Tous les sommets ont déjà une heuristique.")
        return
    console.say("h(n) = estimation du coût restant jusqu'à l'objectif (≥ 0). Entrée = conserver.", "dim")
    for v in targets:
        current = s.graph.heuristics.get(v)
        raw = console.ask(f"h({v})", None if current is None else format_cost(current))
        if raw:
            s.graph.set_heuristic(v, float(raw.replace(",", ".")) if _is_number(raw) else _bad(raw))
    report_heuristic(console, s)


def _is_number(raw: str) -> bool:
    try:
        float(raw.replace(",", "."))
        return True
    except ValueError:
        return False


def _bad(raw: str) -> float:
    raise GraphError(f"« {raw} » n'est pas un nombre.")


def report_heuristic(console: Console, s: SearchSession) -> None:
    if s.graph.goal is None or s.graph.missing_heuristics():
        return
    report = s.graph.check_heuristic()
    if not report.problems:
        console.ok("Heuristique admissible et consistante : A* sera optimal.")
    for problem in report.problems[:6]:
        console.warn(problem)
    if not report.admissible:
        console.say("  → A* / IDA* ne garantissent plus l'optimalité.", "dim")


def build_menu(console: Console, s: SearchSession) -> None:
    run_menu(console, "CONSTRUIRE LE GRAPHE", [
        ("Créer des sommets", lambda: add_vertices(console, s)),
        ("Ajouter un arc orienté pondéré", lambda: add_edge(console, s)),
        ("Définir état initial et état objectif", lambda: set_start_goal(console, s)),
        ("Définir les heuristiques h(n)", lambda: set_heuristics(console, s)),
        ("Supprimer un sommet", lambda: remove_vertex(console, s)),
        ("Supprimer un arc", lambda: remove_edge(console, s)),
        ("Afficher le graphe", lambda: show_graph(console, s)),
        ("Vider le graphe", lambda: _clear(console, s)),
    ], status=lambda: _status(s))


def _clear(console: Console, s: SearchSession) -> None:
    if console.confirm("Supprimer tout le graphe ?"):
        s.graph.clear()
        s.last_result = None
        console.ok("Graphe vidé.")


# --- persistance & visualisation ------------------------------------------
def save(console: Console, s: SearchSession) -> None:
    console.ok(f"Graphe enregistré dans {save_graph(s.graph, console.ask('Fichier', DEFAULT_PATH))}")


def load(console: Console, s: SearchSession) -> None:
    path = console.ask("Fichier à charger", DEFAULT_PATH)
    if not Path(path).exists():
        raise GraphError(f"Fichier introuvable : « {path} ».")
    s.graph, s.last_result = load_graph(path), None
    console.ok(f"Graphe chargé : {len(s.graph.vertices)} sommets, {len(s.graph.edges())} arcs.")


def load_sample(console: Console, s: SearchSession) -> None:
    s.graph, s.last_result = romania_graph(), None
    console.ok("Exemple chargé : carte de Roumanie, Arad → Bucharest (heuristique = distance à vol d'oiseau).")


def visualize(console: Console, s: SearchSession) -> None:
    if not s.graph.vertices:
        raise GraphError("Le graphe est vide.")
    options = ["Fenêtre graphique (matplotlib)", "Enregistrer une image PNG", "Exporter en Graphviz DOT"]
    if s.last_result:
        options.append("Image PNG de chaque étape de la dernière recherche (pour la démo)")
    choice = console.pick("Visualisation :", options)
    result = s.last_result
    if choice == 0:
        draw_graph(s.graph, result, show=True)
    elif choice == 1:
        console.ok(f"Image enregistrée : {draw_graph(s.graph, result, save_to=console.ask('Fichier', 'out/graphe.png'))}")
    elif choice == 2:
        path = Path(console.ask("Fichier", "out/graphe.dot"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(to_dot(s.graph, result), encoding="utf-8")
        console.ok(f"DOT enregistré : {path}   (dot -Tpng {path} -o graphe.png)")
    elif choice == 3 and result:
        frames = render_frames(s.graph, result, console.ask("Dossier", "out/frames"))
        console.ok(f"{len(frames)} images générées.")


# --- recherche -------------------------------------------------------------
def choose_algorithm(console: Console) -> AlgorithmSpec | None:
    category = console.pick("Type de recherche :", [
        "Non informée (aveugle) — sans heuristique", "Informée (heuristique) — guidée par h(n)"])
    if category is None:
        return None
    specs = algorithms_by_category(informed=bool(category))
    index = console.pick("Algorithme :", [f"{sp.label}  ({sp.summary})" for sp in specs])
    return None if index is None else specs[index]


def ensure_ready(console: Console, s: SearchSession, spec: AlgorithmSpec) -> None:
    g = s.graph
    if not g.vertices:
        raise GraphError("Le graphe est vide : construisez-le ou chargez l'exemple.")
    if g.start is None or g.goal is None:
        console.warn("État initial / objectif non définis.")
        set_start_goal(console, s)
    if spec.informed and g.missing_heuristics():
        console.warn("Heuristique manquante pour : " + ", ".join(g.missing_heuristics()))
        if not console.confirm("La saisir maintenant ?", True):
            raise MissingHeuristicError("Algorithme informé impossible sans heuristique complète.")
        set_heuristics(console, s, only_missing=True)


def run_algorithm(console: Console, s: SearchSession) -> None:
    spec = choose_algorithm(console)
    if spec is None:
        return
    ensure_ready(console, s, spec)
    params = {}
    if "limit" in spec.params:
        params["limit"] = console.ask_int("Limite de profondeur", 0, 900, default=3)
    result = run_search(s.graph, spec.key, **params)
    s.last_result = result
    display_result(console, s.graph, result, step_by_step=s.step_by_step)
    if console.confirm("Voir le graphe avec le chemin (image PNG dans out/) ?", False):
        console.ok(f"Image : {draw_graph(s.graph, result, save_to='out/resultat.png')}")


def display_result(console: Console, graph: Graph, result: SearchResult, *, step_by_step: bool) -> None:
    console.header(result.algorithm)
    console.say(f"État initial : {graph.start}   →   État objectif : {graph.goal}")
    stepping = step_by_step
    for step in result.steps:
        title = step_title(step)
        if step.action == "info":
            console.say(f"\n{step.note}", "bold")
        else:
            console.say(f"\nÉtape {step.index} · {title}", "ok" if step.action == "goal" else "bold")
            if step.note:
                console.say(f"   {step.note}")
            if step.frontier_labels or step.action in ("init", "expand", "goal"):
                console.say(f"   Frontière : {', '.join(step.frontier_labels) or '∅'}")
            if step.explored:
                console.say(f"   Explorés  : {', '.join(step.explored)}", "dim")
        if stepping and step is not result.steps[-1]:
            stepping = console.pause()
    summarize(console, result)


def summarize(console: Console, r: SearchResult) -> None:
    console.rule("Résultat")
    if r.found:
        console.ok("Chemin trouvé : " + " → ".join(r.path))
        console.say(f"   Coût total : {r.cost_text}   |   arcs : {len(r.path) - 1}")
    else:
        console.error(f"{r.message}")
    console.say(f"   Sommets développés : {r.expanded}   |   générés : {r.generated}   |   étapes : {len(r.steps)}", "dim")


def compare_all(console: Console, s: SearchSession) -> None:
    g = s.graph
    if not g.vertices or g.start is None or g.goal is None:
        raise GraphError("Définissez le graphe, l'état initial et l'état objectif.")
    limit = console.ask_int("Limite de profondeur pour DLS", 0, 900, default=len(g.vertices))
    rows = []
    for spec in ALGORITHMS.values():
        if spec.informed and g.missing_heuristics():
            rows.append((spec.label.split(" — ")[0], "heuristique manquante", "", "", ""))
            continue
        r = run_search(g, spec.key, **({"limit": limit} if "limit" in spec.params else {}))
        rows.append((spec.label.split(" — ")[0], "oui" if r.found else "non", r.cost_text, str(r.expanded),
                     " → ".join(r.path) if r.found else r.message))
    costs = [float(c) for _, ok, c, *_ in rows if ok == "oui" and c not in ("", "—")]
    best = min(costs) if costs else None
    console.header("COMPARAISON DES ALGORITHMES")
    console.say(f"{'Algorithme':<14}{'Trouvé':<9}{'Coût':<7}{'Dév.':<6}Chemin", "bold")
    for name, ok, cost, expanded, path in rows:
        mark = "  ★ optimal" if ok == "oui" and best is not None and float(cost) == best else ""
        console.say(f"{name:<14}{ok:<9}{cost:<7}{expanded:<6}{path}{mark}")
    console.say("★ = meilleur coût obtenu · Dév. = sommets développés", "dim")


def toggle_mode(console: Console, s: SearchSession) -> None:
    s.step_by_step = not s.step_by_step
    console.ok("Exécution " + ("pas à pas (Entrée pour avancer)." if s.step_by_step else "directe."))


def search_menu(console: Console, session: SearchSession | None = None) -> None:
    s = session or SearchSession()
    run_menu(console, "ALGORITHMES DE RECHERCHE", [
        ("Afficher le graphe", lambda: show_graph(console, s)),
        ("Construire / modifier le graphe", lambda: build_menu(console, s)),
        ("Lancer une recherche", lambda: run_algorithm(console, s)),
        ("Comparer tous les algorithmes", lambda: compare_all(console, s)),
        ("Visualiser (fenêtre, PNG, DOT)", lambda: visualize(console, s)),
        ("Sauvegarder le graphe (JSON)", lambda: save(console, s)),
        ("Charger un graphe (JSON)", lambda: load(console, s)),
        ("Charger l'exemple « Roumanie »", lambda: load_sample(console, s)),
        ("Basculer pas à pas / direct", lambda: toggle_mode(console, s)),
    ], back="Retour au menu principal", status=lambda: _status(s))
