"""Command-line interface: evalkit run suite.yaml."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .cases import load_suite
from .providers import DictProvider, EchoProvider, OpenAICompatibleProvider
from .runner import diff_reports, run_suite, summarize


def _build_provider(args):
    if args.provider == "echo":
        return EchoProvider()
    if args.provider == "dict":
        if not args.fixtures:
            raise SystemExit("The dict provider needs --fixtures <fixtures.json>.")
        mapping = json.loads(Path(args.fixtures).read_text(encoding="utf-8"))
        if not isinstance(mapping, dict):
            raise SystemExit(
                "The dict provider needs a JSON object mapping prompts to "
                f"outputs; {args.fixtures} contains "
                f"{type(mapping).__name__} instead."
            )
        return DictProvider(mapping)
    if args.provider == "openai-compatible":
        return OpenAICompatibleProvider(model=args.model)
    raise SystemExit(f"Unknown provider {args.provider!r}.")


def cmd_run(args) -> int:
    try:
        provider = _build_provider(args)
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(f"evalkit: {exc}") from exc
    try:
        cases = load_suite(args.suite)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"evalkit: {exc}") from exc
    results = run_suite(cases, provider)
    summary = summarize(results)
    for r in results:
        mark = "PASS" if r.passed else "FAIL"
        detail = f" ({r.error})" if r.error else ""
        print(f"[{mark}] {r.case} [{r.judge}] {r.latency_ms:.0f}ms{detail}")
    print(
        f"\n{summary['passed']}/{summary['total']} passed "
        f"(pass rate {summary['pass_rate']:.0%}, avg {summary['avg_latency_ms']:.0f}ms)"
    )
    if args.report:
        payload = {"summary": summary, "results": [r.to_dict() for r in results]}
        Path(args.report).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Report written to {args.report}")
    return 0 if summary["failed"] == 0 else 1


def cmd_validate(args) -> int:
    """Check a suite file for problems without running any provider."""
    try:
        cases = load_suite(args.suite)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"evalkit: {exc}") from exc
    warnings: list[str] = []
    seen: set[str] = set()
    for case in cases:
        if case.name in seen:
            warnings.append(f"duplicate case name {case.name!r}")
        seen.add(case.name)
        if case.expected == "" and case.judge in ("contains", "exact"):
            warnings.append(
                f"[{case.name}] empty 'expected' with judge {case.judge!r}: "
                "the case always passes"
            )
    print(f"{args.suite}: {len(cases)} case(s) OK")
    for warning in warnings:
        print(f"warning: {warning}")
    if warnings and args.strict:
        print(
            f"evalkit: {len(warnings)} warning(s) found; failing due to --strict",
            file=sys.stderr,
        )
        return 1
    return 0


def _load_report(path: str) -> dict:
    """Load a ``--report`` JSON file, validating its shape."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"evalkit: cannot read report {path}: {exc}") from exc
    except ValueError as exc:
        raise SystemExit(f"evalkit: invalid JSON in report {path}: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise SystemExit(
            f"evalkit: {path} is not an evalkit report (missing 'results' list)"
        )
    for i, result in enumerate(payload["results"]):
        if (
            not isinstance(result, dict)
            or "case" not in result
            or "passed" not in result
        ):
            raise SystemExit(
                f"evalkit: {path} result #{i} is missing 'case' or 'passed'"
            )
    return payload


def cmd_diff(args) -> int:
    """Compare two run reports and highlight regressions."""
    old = _load_report(args.old_report)
    new = _load_report(args.new_report)
    diff = diff_reports(old, new)

    def _section(title: str, names: list[str]) -> None:
        print(f"{title}: {len(names)}")
        for name in names:
            print(f"  - {name}")

    print(f"Comparing {args.old_report} -> {args.new_report}")
    _section("Regressions (passed -> failed)", diff["regressions"])
    _section("Fixed (failed -> passed)", diff["improvements"])
    _section("New cases", diff["added"])
    _section("Removed cases", diff["removed"])
    print(f"Pass rate: {diff['old_pass_rate']:.0%} -> {diff['new_pass_rate']:.0%}")
    return 1 if diff["regressions"] else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evalkit",
        description="A tiny YAML-driven eval harness for LLM prompts and agents.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run an eval suite against a provider.")
    run.add_argument("suite", help="Path to a YAML eval suite.")
    run.add_argument(
        "--provider",
        default="dict",
        choices=["dict", "echo", "openai-compatible"],
        help="Which model provider to test (default: dict).",
    )
    run.add_argument(
        "--fixtures",
        help="JSON prompt->output mapping for the dict provider.",
    )
    run.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Model name for the openai-compatible provider.",
    )
    run.add_argument("--report", help="Write a JSON report to this path.")
    run.set_defaults(func=cmd_run)
    validate = sub.add_parser(
        "validate", help="Check a suite file without running any provider."
    )
    validate.add_argument("suite", help="Path to a YAML eval suite.")
    validate.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when any warnings are found (useful in CI).",
    )
    validate.set_defaults(func=cmd_validate)
    diff = sub.add_parser(
        "diff", help="Compare two run reports to catch regressions."
    )
    diff.add_argument("old_report", help="Baseline report JSON (from --report).")
    diff.add_argument(
        "new_report", help="New report JSON to compare against the baseline."
    )
    diff.set_defaults(func=cmd_diff)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
