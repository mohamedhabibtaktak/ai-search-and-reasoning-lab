import pytest

from ia_app.common.errors import KnowledgeBaseError, StorageError
from ia_app.expert import KnowledgeBase, backward_chaining, forward_chaining, parse_rule
from ia_app.expert.samples import animal_kb
from ia_app.expert.storage import load_kb, save_kb


@pytest.fixture
def kb():
    return animal_kb()


# --- modèle ---------------------------------------------------------------
def test_facts_are_normalized_and_deduplicated():
    base = KnowledgeBase(["  Poils ", "poils", "A  B"])
    assert base.facts == ["poils", "a b"]


def test_empty_fact_rejected():
    with pytest.raises(KnowledgeBaseError):
        KnowledgeBase().add_fact("   ")


@pytest.mark.parametrize("conditions,conclusion", [([], "x"), (["a"], "a"), (["a"], " ")])
def test_invalid_rules_rejected(conditions, conclusion):
    with pytest.raises(KnowledgeBaseError):
        KnowledgeBase().add_rule(conditions, conclusion)


def test_rule_names_unique_and_auto_generated():
    base = KnowledgeBase()
    assert base.add_rule(["a"], "b").name == "R1"
    assert base.add_rule(["b"], "c").name == "R2"
    base.remove_rule("R1")
    assert base.add_rule(["c"], "d").name == "R1"  # réutilise le plus petit nom libre
    with pytest.raises(KnowledgeBaseError):
        base.add_rule(["x"], "y", name="R2")


def test_update_and_remove_unknown_rule():
    base = KnowledgeBase()
    with pytest.raises(KnowledgeBaseError):
        base.update_rule("R9", ["a"], "b")
    with pytest.raises(KnowledgeBaseError):
        base.remove_rule("R9")


@pytest.mark.parametrize("text", ["SI a ET b ALORS c", "a, b -> c", "a & b => c", "si a et b alors c"])
def test_parse_rule_formats(text):
    assert parse_rule(text) == (["a", "b"], "c")


def test_parse_rule_without_arrow():
    with pytest.raises(KnowledgeBaseError):
        parse_rule("a b c")


# --- chaînage avant ---------------------------------------------------------
def test_forward_proves_goal(kb):
    r = forward_chaining(kb, "guepard")
    assert r.success and r.rules_used == ["R1", "R5", "R9"]
    assert r.derived_facts == ["mammifere", "carnivore", "guepard"]


def test_forward_goal_already_a_fact(kb):
    r = forward_chaining(kb, "poils")
    assert r.success and r.rules_used == []


def test_forward_failure_reaches_fixpoint(kb):
    r = forward_chaining(kb, "tigre")
    assert not r.success
    assert "Point fixe" in r.trace[-1].message


def test_forward_does_not_mutate_kb(kb):
    before = kb.to_dict()
    forward_chaining(kb, "guepard")
    assert kb.to_dict() == before


def test_forward_skips_rule_with_known_conclusion():
    base = KnowledgeBase(["a", "b"])
    base.add_rule(["a"], "b")
    base.add_rule(["b"], "c")
    r = forward_chaining(base, "c")
    assert r.success and any(e.kind == "skip" for e in r.trace)


def test_forward_terminates_on_cyclic_rules():
    base = KnowledgeBase(["x"])
    base.add_rule(["a"], "b")
    base.add_rule(["b"], "a")
    assert not forward_chaining(base, "a").success


# --- chaînage arrière -------------------------------------------------------
def test_backward_proves_goal(kb):
    r = backward_chaining(kb, "guepard")
    assert r.success and r.rules_used == ["R1", "R5", "R9"]


def test_backward_failure(kb):
    assert not backward_chaining(kb, "tigre").success


def test_backward_unknown_goal(kb):
    r = backward_chaining(kb, "licorne")
    assert not r.success and "Aucune règle" in r.trace[-1].message


def test_backward_cycle_does_not_loop():
    base = KnowledgeBase()
    base.add_rule(["b"], "a")
    base.add_rule(["a"], "b")
    r = backward_chaining(base, "a")
    assert not r.success and any(e.kind == "cycle-cut" for e in r.trace)


def test_backward_cycle_with_escape_route():
    base = KnowledgeBase(["c"])
    base.add_rule(["b"], "a")
    base.add_rule(["a"], "b")
    base.add_rule(["c"], "b")
    assert backward_chaining(base, "a").success


def test_backward_tries_alternative_rule():
    base = KnowledgeBase(["y"])
    base.add_rule(["x"], "g")   # échoue
    base.add_rule(["y"], "g")   # réussit
    r = backward_chaining(base, "g")
    assert r.success and r.rules_used == ["R2"]


def test_both_methods_agree_on_every_symbol(kb):
    for symbol in kb.symbols():
        assert forward_chaining(kb, symbol).success == backward_chaining(kb, symbol).success


# --- persistance -------------------------------------------------------------
def test_roundtrip(tmp_path, kb):
    path = save_kb(kb, tmp_path / "kb.json")
    assert load_kb(path).to_dict() == kb.to_dict()


def test_load_errors(tmp_path):
    with pytest.raises(StorageError):
        load_kb(tmp_path / "absent.json")
    bad = tmp_path / "bad.json"
    bad.write_text("{oops", encoding="utf-8")
    with pytest.raises(StorageError):
        load_kb(bad)
    wrong = tmp_path / "wrong.json"
    wrong.write_text('{"rules": [{"name": "R1"}]}', encoding="utf-8")
    with pytest.raises(KnowledgeBaseError):
        load_kb(wrong)
