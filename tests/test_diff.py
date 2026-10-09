"""Tests for 'evalkit diff': comparing two run reports."""

import json

import pytest

from evalkit.cli import main
from evalkit.runner import diff_reports


def _report(cases):
    return {
        "summary": {},
        "results": [
            {"case": name, "passed": passed, "judge": "contains", "latency_ms": 1.0}
            for name, passed in cases
        ],
    }


def _write_report(tmp_path, name, cases):
    path = tmp_path / name
    path.write_text(json.dumps(_report(cases)))
    return path


def test_diff_reports_finds_regressions_and_improvements():
    old = _report([("a", True), ("b", False), ("c", True)])
    new = _report([("a", False), ("b", True), ("c", True)])
    diff = diff_reports(old, new)
    assert diff["regressions"] == ["a"]
    assert diff["improvements"] == ["b"]
    assert diff["added"] == []
    assert diff["removed"] == []


def test_diff_reports_added_and_removed_cases():
    old = _report([("a", True), ("gone", True)])
    new = _report([("a", True), ("fresh", False)])
    diff = diff_reports(old, new)
    assert diff["added"] == ["fresh"]
    assert diff["removed"] == ["gone"]
    assert diff["old_pass_rate"] == 1.0
    assert diff["new_pass_rate"] == 0.5


def test_diff_reports_empty_baseline():
    diff = diff_reports(_report([]), _report([("a", True)]))
    assert diff["added"] == ["a"]
    assert diff["old_pass_rate"] == 0.0


def test_diff_command_exits_one_on_regressions(tmp_path, capsys):
    old = _write_report(tmp_path, "old.json", [("a", True)])
    new = _write_report(tmp_path, "new.json", [("a", False)])
    assert main(["diff", str(old), str(new)]) == 1
    out = capsys.readouterr().out
    assert "Regressions (passed -> failed): 1" in out
    assert "- a" in out


def test_diff_command_exits_zero_when_clean(tmp_path, capsys):
    old = _write_report(tmp_path, "old.json", [("a", False)])
    new = _write_report(tmp_path, "new.json", [("a", True)])
    assert main(["diff", str(old), str(new)]) == 0
    out = capsys.readouterr().out
    assert "Fixed (failed -> passed): 1" in out


def test_diff_command_rejects_missing_file(tmp_path):
    old = _write_report(tmp_path, "old.json", [("a", True)])
    with pytest.raises(SystemExit) as excinfo:
        main(["diff", str(old), str(tmp_path / "nope.json")])
    assert "nope.json" in str(excinfo.value)


def test_diff_command_rejects_bad_payload(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"summary": {}}))
    good = _write_report(tmp_path, "good.json", [("a", True)])
    with pytest.raises(SystemExit) as excinfo:
        main(["diff", str(bad), str(good)])
    assert "not an evalkit report" in str(excinfo.value)


def test_diff_command_rejects_invalid_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    good = _write_report(tmp_path, "good.json", [("a", True)])
    with pytest.raises(SystemExit) as excinfo:
        main(["diff", str(bad), str(good)])
    assert "invalid JSON" in str(excinfo.value)
