import pytest

from ia_app.search import run_search
from ia_app.search.samples import romania_graph
from ia_app.search.viz import draw_graph, render_frames, to_dot


def test_dot_export_highlights_path():
    g = romania_graph()
    dot = to_dot(g, run_search(g, "astar"))
    assert dot.startswith("digraph") and '"Arad" -> "Sibiu" [label="140", color="#d9480f"' in dot


def test_png_output(tmp_path):
    pytest.importorskip("matplotlib")
    g = romania_graph()
    result = run_search(g, "astar")
    out = draw_graph(g, result, save_to=tmp_path / "g.png")
    assert out.exists() and out.stat().st_size > 5_000
    frames = render_frames(g, result, tmp_path / "frames")
    assert len(frames) == len(result.steps) + 1
