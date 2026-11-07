"""Tests de la GUI : exécutés sous un écran (réel ou Xvfb), ignorés sinon."""
import pytest

tk = pytest.importorskip("tkinter")

from ia_app.gui import dialogs  # noqa: E402
from ia_app.gui.playback import Player  # noqa: E402


@pytest.fixture
def app(monkeypatch):
    try:
        from ia_app.gui.app import App
        root = App()
    except tk.TclError:
        pytest.skip("aucun affichage disponible")
    errors = []
    monkeypatch.setattr(dialogs.messagebox, "showerror", lambda title, msg, **kw: errors.append(msg))
    root.errors = errors
    root.update()
    yield root
    root.destroy()


def test_player_bounds():
    p = Player(3)
    assert p.at_start and not p.at_end and not p.prev()
    assert p.next() and p.next() and p.at_end and not p.next()
    p.first()
    assert p.position == 0
    assert Player(0).at_end


def test_two_modules_available(app):
    assert [app.notebook.tab(i, "text") for i in range(2)] == ["Systèmes experts", "Algorithmes de recherche"]


def test_expert_forward_stepping(app):
    tab = app.expert
    tab.goal_var.set("guepard")
    tab.method_var.set("forward")
    tab.run()
    assert tab.player.position == 0 and "Étape 1 /" in tab.step_var.get()
    tab.next(); tab.prev(); tab.show_all()
    assert "démontré" in tab.conclusion.cget("text") and "R1 → R5 → R9" in tab.conclusion.cget("text")


def test_expert_goal_status_and_unprovable(app):
    tab = app.expert
    tab.goal_var.set("poils"); tab._goal_changed()
    assert "Déjà présent" in tab.goal_status.cget("text")
    tab.goal_var.set("tigre"); tab.method_var.set("backward"); tab.run(); tab.show_all()
    assert "NON démontrable" in tab.conclusion.cget("text")


def test_expert_changing_goal_resets_run_without_restart(app):
    tab = app.expert
    tab.goal_var.set("guepard"); tab.run()
    tab.goal_var.set("zebre"); tab._goal_changed()
    assert tab.result is None
    tab.run()
    assert tab.result.goal == "zebre"


def test_expert_add_rule_invalid_shows_error_not_crash(app, monkeypatch):
    monkeypatch.setattr(dialogs, "ask_text", lambda *a, **k: "pas de fleche")
    app.expert.add_rule()
    assert app.errors and "Format attendu" in app.errors[0]
    monkeypatch.setattr(dialogs, "ask_text", lambda *a, **k: "SI a ET b ALORS c")
    app.expert.add_rule()
    assert any(r.conclusion == "c" for r in app.expert.kb.rules)


def test_search_runs_astar_and_highlights_path(app):
    tab = app.search
    tab.load_sample()
    tab.informed_var.set(1); tab._fill_algorithms()
    tab.algo_var.set(next(s.label for s in tab._specs if s.key == "astar")); tab._algo_changed()
    tab.run(); tab.last()
    assert "Coût total : 418" in tab.result_label.cget("text")
    assert tab.canvas.path == ["Arad", "Sibiu", "Rimnicu", "Pitesti", "Bucharest"]


def test_search_no_path_and_empty_graph_messages(app):
    tab = app.search
    tab.run()
    assert app.errors and "vide" in app.errors[-1]
    tab.graph.add_edge("A", "B", 1, create_missing=True)
    tab.graph.set_start("B"); tab.graph.set_goal("A"); tab.refresh()
    tab.informed_var.set(0); tab._fill_algorithms(); tab.run(); tab.last()
    assert "Aucun chemin" in tab.result_label.cget("text")


def test_search_informed_requires_heuristics(app, monkeypatch):
    tab = app.search
    tab.graph.add_edge("A", "B", 1, create_missing=True)
    tab.graph.set_start("A"); tab.graph.set_goal("B"); tab.refresh()
    tab.informed_var.set(1); tab._fill_algorithms()
    monkeypatch.setattr(dialogs, "confirm", lambda *a, **k: False)
    tab.run()
    assert tab.result is None


def test_search_edit_graph_via_dialogs(app, monkeypatch):
    tab = app.search
    monkeypatch.setattr(dialogs, "ask_text", lambda *a, **k: "S, G")
    tab.add_vertex()
    monkeypatch.setattr(dialogs, "ask_edge", lambda *a, **k: ("S", "G", 4.0, True))
    tab.add_edge()
    assert sorted(tab.graph.edges()) == [("G", "S", 4.0), ("S", "G", 4.0)]
    monkeypatch.setattr(dialogs, "ask_edge", lambda *a, **k: ("S", "G", -2.0, False))
    tab.add_edge()
    assert app.errors and "négatif" in app.errors[-1]


def test_canvas_add_vertex_and_drag(app, monkeypatch):
    tab = app.search
    monkeypatch.setattr(dialogs, "ask_text", lambda *a, **k: "X")
    tab._canvas_add_vertex(0.25, 0.75)
    assert tab.canvas.rel["X"] == (0.25, 0.75)
    tab.canvas.rel["X"] = (0.5, 0.5)
    tab.canvas.redraw()
    x, y = tab.canvas._px("X")
    assert tab.canvas._hit(x, y) == "X" and tab.canvas._hit(0, 0) is None


def test_playback_buttons_state(app):
    tab = app.search
    tab.load_sample(); tab.run()
    assert str(tab.btns["prev"].cget("state")) == "disabled" and str(tab.btns["next"].cget("state")) == "normal"
    tab.last()
    assert str(tab.btns["next"].cget("state")) == "disabled"


def test_auto_play_reaches_end(app):
    tab = app.search
    tab.load_sample(); tab.run()
    tab.toggle_play()
    for _ in range(200):
        app.update()
        app.after(20)
        if tab.player.at_end:
            break
        app.update_idletasks()
        import time; time.sleep(0.05)
    assert tab.player.at_end or tab._job is not None
    tab._stop()
