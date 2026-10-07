"""Tests for the suite runner."""

from evalkit.cases import EvalCase
from evalkit.providers import DictProvider, EchoProvider
from evalkit.runner import run_suite, summarize

CASES = [
    EvalCase(name="contains-ok", prompt="Say hello to Ada.", expected="ada", judge="contains"),
    EvalCase(name="exact-ok", prompt="Reply with exactly: OK", expected="OK", judge="exact"),
    EvalCase(name="will-fail", prompt="Say hello.", expected="goodbye", judge="contains"),
]

MAPPING = {
    "Say hello to Ada.": "Hello, Ada!",
    "Reply with exactly: OK": "OK",
    "Say hello.": "Hello!",
}


def test_run_suite_mixed_results():
    results = run_suite(CASES, DictProvider(MAPPING))
    by_name = {r.case: r for r in results}
    assert by_name["contains-ok"].passed
    assert by_name["exact-ok"].passed
    assert not by_name["will-fail"].passed
    assert all(r.latency_ms >= 0 for r in results)


def test_summarize():
    summary = summarize(run_suite(CASES, DictProvider(MAPPING)))
    assert summary["total"] == 3
    assert summary["passed"] == 2
    assert summary["failed"] == 1
    assert summary["pass_rate"] == 0.6667


def test_provider_error_fails_case_not_run():
    class Broken:
        name = "broken"

        def complete(self, prompt):  # noqa: ARG002
            raise RuntimeError("boom")

    (result,) = run_suite([CASES[0]], Broken())
    assert not result.passed
    assert "boom" in result.error


def test_missing_fixture_fails_case():
    (result,) = run_suite([CASES[0]], DictProvider({}))
    assert not result.passed
    assert "no fixture" in result.error


def test_echo_provider_smoke():
    (result,) = run_suite(
        [EvalCase(name="echo", prompt="hello world", expected="hello", judge="contains")],
        EchoProvider(),
    )
    assert result.passed


def test_summarize_includes_per_judge_breakdown():
    summary = summarize(run_suite(CASES, DictProvider(MAPPING)))
    assert summary["by_judge"] == {
        "contains": {"total": 2, "passed": 1},
        "exact": {"total": 1, "passed": 1},
    }


def test_summarize_by_judge_empty_for_no_results():
    assert summarize([])["by_judge"] == {}
