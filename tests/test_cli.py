"""End-to-end tests for the evalkit CLI."""

import json

from evalkit.cli import main


def _write_suite_and_fixtures(tmp_path, expected="hi", output="hi there"):
    suite = tmp_path / "evals.yaml"
    suite.write_text(
        f"- name: ok\n  prompt: Say hi.\n  expected: {expected}\n  judge: contains\n"
    )
    fixtures = tmp_path / "fixtures.json"
    fixtures.write_text(json.dumps({"Say hi.": output}))
    return suite, fixtures


def test_cli_run_passes_and_writes_report(tmp_path):
    suite, fixtures = _write_suite_and_fixtures(tmp_path)
    report = tmp_path / "report.json"
    code = main(
        [
            "run",
            str(suite),
            "--provider",
            "dict",
            "--fixtures",
            str(fixtures),
            "--report",
            str(report),
        ]
    )
    assert code == 0
    payload = json.loads(report.read_text())
    assert payload["summary"]["passed"] == 1
    assert payload["results"][0]["case"] == "ok"


def test_cli_exit_code_is_one_on_failure(tmp_path):
    suite, fixtures = _write_suite_and_fixtures(tmp_path, expected="bye")
    code = main(["run", str(suite), "--provider", "dict", "--fixtures", str(fixtures)])
    assert code == 1


def test_missing_suite_file_exits_cleanly(tmp_path):
    import pytest

    with pytest.raises(SystemExit) as excinfo:
        main(["run", str(tmp_path / "nope.yaml"), "--provider", "echo"])
    assert "nope.yaml" in str(excinfo.value)


def test_missing_api_key_exits_cleanly(tmp_path, monkeypatch):
    import pytest

    monkeypatch.delenv("EVALKIT_API_KEY", raising=False)
    suite = tmp_path / "evals.yaml"
    suite.write_text("- name: a\n  prompt: hi\n  expected: hi\n  judge: contains\n")
    with pytest.raises(SystemExit) as excinfo:
        main(["run", str(suite), "--provider", "openai-compatible"])
    assert "EVALKIT_API_KEY" in str(excinfo.value)


def test_validate_ok_suite(tmp_path, capsys):
    suite = tmp_path / "evals.yaml"
    suite.write_text("- name: a\n  prompt: hi\n  expected: hi\n  judge: contains\n")
    assert main(["validate", str(suite)]) == 0
    assert "1 case(s) OK" in capsys.readouterr().out


def test_validate_warns_on_empty_expected_and_duplicates(tmp_path, capsys):
    suite = tmp_path / "evals.yaml"
    suite.write_text(
        "- name: a\n  prompt: hi\n"
        "- name: a\n  prompt: yo\n  expected: yo\n  judge: contains\n"
    )
    assert main(["validate", str(suite)]) == 0
    out = capsys.readouterr().out
    assert "empty 'expected'" in out
    assert "duplicate case name" in out


def test_validate_rejects_bad_suite(tmp_path):
    import pytest

    suite = tmp_path / "evals.yaml"
    suite.write_text("- name: b\n  prompt: hi\n  judge: vibes\n")
    with pytest.raises(SystemExit):
        main(["validate", str(suite)])


def test_validate_strict_fails_on_warnings(tmp_path, capsys):
    suite = tmp_path / "evals.yaml"
    suite.write_text("- name: a\n  prompt: hi\n- name: a\n  prompt: yo\n  expected: yo\n  judge: contains\n")
    assert main(["validate", str(suite), "--strict"]) == 1
    assert "failing due to --strict" in capsys.readouterr().err


def test_validate_strict_passes_on_clean_suite(tmp_path):
    suite = tmp_path / "evals.yaml"
    suite.write_text("- name: a\n  prompt: hi\n  expected: hi\n  judge: contains\n")
    assert main(["validate", str(suite), "--strict"]) == 0
