"""Tests for YAML suite loading."""

import pytest

from evalkit.cases import load_suite


def test_load_suite(tmp_path):
    suite = tmp_path / "evals.yaml"
    suite.write_text("- name: a\n  prompt: Say hi.\n  expected: hi\n  judge: contains\n")
    (case,) = load_suite(suite)
    assert case.name == "a"
    assert case.prompt == "Say hi."
    assert case.expected == "hi"
    assert case.judge == "contains"


def test_defaults(tmp_path):
    suite = tmp_path / "evals.yaml"
    suite.write_text("- name: b\n  prompt: Say hi.\n")
    (case,) = load_suite(suite)
    assert case.expected == ""
    assert case.judge == "contains"


def test_not_a_list_raises(tmp_path):
    suite = tmp_path / "evals.yaml"
    suite.write_text("name: oops\n")
    with pytest.raises(ValueError, match="YAML list"):
        load_suite(suite)


def test_missing_field_raises(tmp_path):
    suite = tmp_path / "evals.yaml"
    suite.write_text("- prompt: Say hi.\n")
    with pytest.raises(ValueError, match="missing required field"):
        load_suite(suite)


def test_unknown_judge_rejected_at_load(tmp_path):
    suite = tmp_path / "evals.yaml"
    suite.write_text("- name: c\n  prompt: Say hi.\n  judge: vibes\n")
    with pytest.raises(ValueError, match="vibes"):
        load_suite(suite)


def test_invalid_regex_rejected_at_load(tmp_path):
    suite = tmp_path / "evals.yaml"
    suite.write_text(
        "- name: bad-regex\n  prompt: Say hi.\n  expected: '([unclosed'\n  judge: regex\n"
    )
    with pytest.raises(ValueError, match="invalid regex pattern"):
        load_suite(suite)


def test_invalid_yaml_raises_value_error(tmp_path):
    suite = tmp_path / "evals.yaml"
    suite.write_text("- name: [\n  this is not: [valid\n")
    with pytest.raises(ValueError, match="Invalid YAML"):
        load_suite(suite)
