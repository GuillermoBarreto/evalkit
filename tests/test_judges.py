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


def test_json_contains_matches_top_level_and_nested_keys():
    output = '{"model": {"name": "gpt-4o"}, "ok": true}'
    assert evaluate("json_contains", output, '{"model.name": "gpt-4o", "ok": true}')
    assert evaluate("json_contains", output, "{}")


def test_json_contains_fails_on_missing_or_wrong_values():
    assert not evaluate("json_contains", '{"a": 1}', '{"a": 2}')
    assert not evaluate("json_contains", '{"a": 1}', '{"b": 1}')
    assert not evaluate("json_contains", '{"a": {"b": 1}}', '{"a.c": 1}')


def test_json_contains_fails_on_invalid_json():
    assert not evaluate("json_contains", "not json", '{"a": 1}')
    assert not evaluate("json_contains", '{"a": 1}', "not json")
    assert not evaluate("json_contains", '{"a": 1}', "[1, 2]")


def test_unknown_judge_raises():
    with pytest.raises(ValueError, match="Unknown judge"):
        evaluate("vibes", "x", "y")


def test_judges_registry():
    assert set(JUDGES) == {"exact", "contains", "regex", "json_contains"}

