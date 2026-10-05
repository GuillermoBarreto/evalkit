"""Tests for the deterministic judges."""

import pytest

from evalkit.judges import JUDGES, evaluate


def test_contains_is_case_insensitive():
    assert evaluate("contains", "Hello, Ada!", "ada")
    assert not evaluate("contains", "Hello!", "ada")


def test_exact_ignores_edge_whitespace():
    assert evaluate("exact", "  OK\n", "OK")
    assert not evaluate("exact", "OK!", "OK")


def test_regex_matches_anywhere_in_output():
    assert evaluate("regex", "The answer is 7.", r"\d+")
    assert not evaluate("regex", "The answer is seven.", r"^\d+$")


def test_unknown_judge_raises():
    with pytest.raises(ValueError, match="Unknown judge"):
        evaluate("vibes", "x", "y")


def test_judges_registry():
    assert set(JUDGES) == {"exact", "contains", "regex"}
