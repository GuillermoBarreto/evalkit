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
