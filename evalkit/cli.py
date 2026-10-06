"""Command-line interface: evalkit run suite.yaml."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .cases import load_suite
from .providers import DictProvider, EchoProvider, OpenAICompatibleProvider
from .runner import run_suite, summarize


def _build_provider(args):
    if args.provider == "echo":
        return EchoProvider()
    if args.provider == "dict":
        if not args.fixtures:
            raise SystemExit("The dict provider needs --fixtures <fixtures.json>.")
        mapping = json.loads(Path(args.fixtures).read_text(encoding="utf-8"))
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
