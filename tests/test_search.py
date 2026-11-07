import math
import random

import pytest

from ia_app.common.errors import GraphError, MissingHeuristicError
from ia_app.search import ALGORITHMS, Graph, run_search
from ia_app.search.samples import romania_graph
from ia_app.search.storage import load_graph, save_graph

OPTIMAL = ["Arad", "Sibiu", "Rimnicu", "Pitesti", "Bucharest"]
SUBOPTIMAL = ["Arad", "Sibiu", "Fagaras", "Bucharest"]


@pytest.fixture
def romania():
    return romania_graph()


def params(key):
    return {"limit": 6} if key == "dls" else {}


# --- graphe ---------------------------------------------------------------
def test_graph_validation():
    g = Graph()
    g.add_vertex("A"); g.add_vertex("B")
    with pytest.raises(GraphError):
        g.add_edge("A", "B", -1)
    with pytest.raises(GraphError):
        g.add_edge("A", "A", 1)
    with pytest.raises(GraphError):
        g.add_edge("A", "Z", 1)
    with pytest.raises(GraphError):
        g.add_edge("A", "B", float("nan"))
    with pytest.raises(GraphError):
        g.add_vertex("  ")
    with pytest.raises(GraphError):
        g.set_heuristic("A", -3)


def test_remove_vertex_cleans_edges_and_markers():
    g = romania_graph()
    g.remove_vertex("Sibiu")
    assert all("Sibiu" not in (u, v) for u, v, _ in g.edges())
    g.remove_vertex("Arad")
    assert g.start is None and "Arad" not in g.heuristics


def test_heuristic_report(romania):
    assert romania.check_heuristic().admissible and romania.check_heuristic().consistent
    romania.set_heuristic("Arad", 999)
    report = romania.check_heuristic()
    assert not report.admissible and not report.consistent
    romania.set_heuristic("Bucharest", 5)
    assert not romania.check_heuristic().goal_is_zero


def test_graph_roundtrip(tmp_path, romania):
    path = save_graph(romania, tmp_path / "g.json")
    assert load_graph(path).to_dict() == romania.to_dict()


# --- résultats de référence (Russell & Norvig) -----------------------------------
@pytest.mark.parametrize("key,path,cost", [
    ("bfs", SUBOPTIMAL, 450), ("dfs", SUBOPTIMAL, 450), ("ids", SUBOPTIMAL, 450),
    ("ucs", OPTIMAL, 418), ("greedy", SUBOPTIMAL, 450), ("astar", OPTIMAL, 418),
    ("idastar", OPTIMAL, 418), ("hill", SUBOPTIMAL, 450),
])
def test_romania_reference(romania, key, path, cost):
    r = run_search(romania, key)
    assert r.found and r.path == path and r.cost == cost


def test_astar_expansion_order(romania):
    r = run_search(romania, "astar")
    expanded = [s.current for s in r.steps if s.action in ("expand", "goal")]
    assert expanded == ["Arad", "Sibiu", "Rimnicu", "Fagaras", "Pitesti", "Bucharest"]


def test_dls_cutoff_then_success(romania):
    cut = run_search(romania, "dls", limit=2)
    assert not cut.found and "limite" in cut.message
    assert run_search(romania, "dls", limit=3).found


def test_invalid_dls_limit(romania):
    with pytest.raises(GraphError):
        run_search(romania, "dls", limit=-1)


# --- cas particuliers -------------------------------------------------------------
def line_graph():
    g = Graph()
    g.add_edge("A", "B", 1, create_missing=True)
    g.add_edge("B", "C", 1, create_missing=True)
    g.add_vertex("Z")
    for v in g.vertices:
        g.set_heuristic(v, 0)
    return g


@pytest.mark.parametrize("key", list(ALGORITHMS))
def test_no_path(key):
    g = line_graph()
    g.set_start("A"); g.set_goal("Z")
    r = run_search(g, key, **params(key))
    assert not r.found and r.path == [] and r.cost is None
    assert r.message.lower().startswith(("aucun", "échec"))


@pytest.mark.parametrize("key", list(ALGORITHMS))
def test_start_equals_goal(key):
    g = line_graph()
    g.set_start("A"); g.set_goal("A")
    r = run_search(g, key, **params(key))
    assert r.found and r.path == ["A"] and r.cost == 0


@pytest.mark.parametrize("key", list(ALGORITHMS))
def test_cycles_terminate(key):
    g = Graph()
    for a, b in [("A", "B"), ("B", "C"), ("C", "A"), ("C", "G")]:
        g.add_edge(a, b, 1, create_missing=True)
    for v, h in {"A": 3, "B": 2, "C": 1, "G": 0}.items():
        g.set_heuristic(v, h)
    g.set_start("A"); g.set_goal("G")
    assert run_search(g, key, **params(key)).path == ["A", "B", "C", "G"]


@pytest.mark.parametrize("key", [k for k in ALGORITHMS if k != "hill"])
def test_zero_cost_edges(key):
    g = Graph()
    for a, b in [("A", "B"), ("B", "A"), ("B", "G")]:
        g.add_edge(a, b, 0, create_missing=True)
    for v in g.vertices:
        g.set_heuristic(v, 0)
    g.set_start("A"); g.set_goal("G")
    r = run_search(g, key, **params(key))
    assert r.found and r.cost == 0


def test_hill_climbing_plateau_is_reported_not_looped():
    g = line_graph()          # h = 0 partout : plateau
    g.set_start("A"); g.set_goal("C")
    r = run_search(g, "hill")
    assert not r.found and "plateau" in r.message


def test_hill_climbing_stuck_in_local_minimum():
    g = Graph()
    g.add_edge("S", "A", 1, create_missing=True)
    g.add_edge("S", "B", 1, create_missing=True)
    g.add_edge("B", "G", 1, create_missing=True)
    for v, h in {"S": 6, "A": 1, "B": 5, "G": 0}.items():
        g.set_heuristic(v, h)
    g.set_start("S"); g.set_goal("G")
    hill, astar = run_search(g, "hill"), run_search(g, "astar")
    assert not hill.found and "minimum local" in hill.message or "impasse" in hill.message
    assert astar.found and astar.path == ["S", "B", "G"]


def test_greedy_not_optimal_but_astar_is():
    g = Graph()
    for a, b, c in [("S", "A", 1), ("A", "G", 10), ("S", "B", 2), ("B", "G", 2)]:
        g.add_edge(a, b, c, create_missing=True)
    for v, h in {"S": 3, "A": 1, "B": 2, "G": 0}.items():
        g.set_heuristic(v, h)
    g.set_start("S"); g.set_goal("G")
    assert run_search(g, "greedy").cost == 11
    assert run_search(g, "astar").cost == 4


def test_informed_requires_heuristics(romania):
    romania.remove_vertex("Zerind")
    romania.add_vertex("Zerind")
    with pytest.raises(MissingHeuristicError):
        run_search(romania, "astar")
    assert run_search(romania, "ucs").found  # non informé : pas besoin de h


def test_start_goal_required():
    g = Graph()
    g.add_vertex("A")
    with pytest.raises(GraphError):
        run_search(g, "bfs")


def test_steps_are_consistent(romania):
    r = run_search(romania, "ucs")
    assert [s.index for s in r.steps] == list(range(1, len(r.steps) + 1))
    assert r.steps[0].action == "init" and r.steps[-1].action == "goal"
    assert r.expanded == len(r.steps[-1].explored)


# --- propriétés sur graphes aléatoires -------------------------------------------------
def random_graph(rng: random.Random) -> Graph:
    g = Graph()
    n = rng.randint(2, 8)
    names = [f"N{i}" for i in range(n)]
    for v in names:
        g.add_vertex(v)
    for u in names:
        for v in names:
            if u != v and rng.random() < 0.35:
                g.add_edge(u, v, rng.randint(1, 9))
    g.set_start(names[0]); g.set_goal(names[-1])
    true = g.true_costs_to(names[-1])
    for v in names:  # heuristique admissible mais volontairement non consistante
        g.set_heuristic(v, rng.random() * true.get(v, 0.0))
    return g


def hops(path):
    return len(path) - 1


def test_random_graphs_properties():
    rng = random.Random(2026)
    for _ in range(250):
        g = random_graph(rng)
        results = {k: run_search(g, k, **({"limit": len(g.vertices)} if k == "dls" else {})) for k in ALGORITHMS}
        reachable = g.goal in g.true_costs_to(g.goal) and g.start in g.true_costs_to(g.goal)
        for key in ("bfs", "dfs", "ids", "ucs", "greedy", "astar", "idastar"):
            assert results[key].found == reachable, key           # complétude sur graphe fini
        assert results["dls"].found == reachable
        for r in results.values():
            if r.found:                                           # chemin valide
                assert r.path[0] == g.start and r.path[-1] == g.goal
                assert math.isclose(r.cost, g.path_cost(r.path))
        if reachable:
            best = g.true_costs_to(g.goal)[g.start]
            for key in ("ucs", "astar", "idastar"):               # optimalité en coût
                assert math.isclose(results[key].cost, best), key
            assert hops(results["bfs"].path) == hops(results["ids"].path)   # optimalité en arcs
            assert all(hops(results["bfs"].path) <= hops(r.path) for r in results.values() if r.found)
