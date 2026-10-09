"""Run a suite of cases against a provider and summarize the results."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Iterable

from .cases import EvalCase
from .judges import evaluate
from .providers import Provider


@dataclass
class EvalResult:
    case: str
    judge: str
    output: str
    expected: str
    passed: bool
    latency_ms: float
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def run_suite(cases: Iterable[EvalCase], provider: Provider) -> list[EvalResult]:
    """Run every case against the provider.

    Provider failures and unknown judges fail the individual case, not the run.
    """
    results: list[EvalResult] = []
    for case in cases:
        started = time.perf_counter()
        try:
            output = provider.complete(case.prompt)
            passed = evaluate(case.judge, output, case.expected)
            error = ""
        except Exception as exc:  # noqa: BLE001 - recorded on the result, not raised
            output, passed, error = "", False, f"{type(exc).__name__}: {exc}"
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        results.append(
            EvalResult(
                case=case.name,
                judge=case.judge,
                output=output,
                expected=case.expected,
                passed=passed,
                latency_ms=latency_ms,
                error=error,
            )
        )
    return results


def summarize(results: list[EvalResult]) -> dict:
    """Aggregate pass/fail stats across a run."""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    latencies = [r.latency_ms for r in results]
    by_judge: dict[str, dict[str, int]] = {}
    for r in results:
        bucket = by_judge.setdefault(r.judge, {"total": 0, "passed": 0})
        bucket["total"] += 1
        if r.passed:
            bucket["passed"] += 1
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "avg_latency_ms": (
            round(sum(latencies) / len(latencies), 2) if latencies else 0.0
        ),
        "by_judge": by_judge,
    }


def _pass_rate(results: dict[str, dict]) -> float:
    total = len(results)
    if not total:
        return 0.0
    passed = sum(1 for r in results.values() if r.get("passed"))
    return round(passed / total, 4)


def diff_reports(old: dict, new: dict) -> dict:
    """Compare two run-report payloads (as written by ``--report``).

    Returns the case names that regressed (passed -> failed), improved
    (failed -> passed), were added, or were removed, plus each run's
    pass rate.
    """
    old_results = {r["case"]: r for r in old["results"]}
    new_results = {r["case"]: r for r in new["results"]}
    common = old_results.keys() & new_results.keys()
    return {
        "regressions": sorted(
            c
            for c in common
            if old_results[c].get("passed") and not new_results[c].get("passed")
        ),
        "improvements": sorted(
            c
            for c in common
            if not old_results[c].get("passed") and new_results[c].get("passed")
        ),
        "added": sorted(new_results.keys() - old_results.keys()),
        "removed": sorted(old_results.keys() - new_results.keys()),
        "old_pass_rate": _pass_rate(old_results),
        "new_pass_rate": _pass_rate(new_results),
    }
