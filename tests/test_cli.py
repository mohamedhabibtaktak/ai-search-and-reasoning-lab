import io

from ia_app.cli.console import Console
from ia_app.cli.main import main


def run(inputs, **kw):
    feed = iter(inputs)
    out = io.StringIO()
    code = main(["--no-color"], Console(input_fn=lambda _p: next(feed), output=out, color=False))
    return code, out.getvalue()


def test_quit_immediately():
    code, out = run(["3"])
    assert code == 0 and "MENU PRINCIPAL" in out and "Systèmes experts" in out and "Algorithmes de recherche" in out


def test_expert_forward_direct_mode():
    # 1 experts → 5 mode direct → 4 lancer → 0 retour → 3 quitter
    code, out = run(["1", "5", "4", "0", "3"])
    assert "Objectif « guepard » démontré" in out and "R1 → R5 → R9" in out


def test_expert_backward_and_goal_already_known():
    code, out = run(["1", "5", "2", "poils", "3", "2", "4", "0", "3"])
    assert "déjà présent dans la base de faits" in out and "Chaînage arrière" in out


def test_expert_add_rule_and_error_message_not_traceback():
    code, out = run(["1", "6", "3", "pas de fleche", "3", "a, b -> a", "0", "0", "3"])
    assert "Format attendu" in out and "tautologique" in out and "Traceback" not in out


def test_search_astar_on_sample():
    # 2 recherche → 8 exemple → 9 mode direct → 3 lancer → 2 informée → 2 A* → n (pas d'image) → 0 → 3
    code, out = run(["2", "8", "9", "3", "2", "2", "n", "0", "3"])
    assert "Chemin trouvé : Arad → Sibiu → Rimnicu → Pitesti → Bucharest" in out
    assert "Coût total : 418" in out


def test_search_no_path_is_reported_clearly():
    # Construit A→B, initial=B, objectif=A (inatteignable), mode direct, BFS, pas d'image.
    inputs = ["2", "2", "1", "A,B", "2", "A", "B", "1", "n", "3", "B", "A", "0",
              "9", "3", "1", "1", "n", "0", "3"]
    code, out = run(inputs)
    assert "Aucun chemin trouvé" in out


def test_invalid_numbers_are_retried():
    code, out = run(["x", "9", "3"])
    assert "Entrez un nombre entier" in out and "Valeur attendue" in out and code == 0


def test_eof_exits_cleanly():
    def eof(_prompt):
        raise EOFError
    out = io.StringIO()
    assert main(["--no-color"], Console(input_fn=eof, output=out, color=False)) == 0
    assert "Au revoir" in out.getvalue()


def test_compare_all(tmp_path):
    code, out = run(["2", "8", "4", "13", "0", "3"])
    assert "COMPARAISON" in out and "optimal" in out
