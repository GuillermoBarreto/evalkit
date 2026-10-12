"""Deterministic judges: exact, contains, regex, and JSON matching."""

from __future__ import annotations

import json
import re


def exact_match(output: str, expected: str) -> bool:
    """True when the output equals the expected string (ignoring edge whitespace)."""
    return output.strip() == expected.strip()


def contains(output: str, expected: str) -> bool:
    """True when the expected string appears anywhere in the output (case-insensitive)."""
    return expected.strip().lower() in output.strip().lower()


def regex_match(output: str, pattern: str) -> bool:
    """True when the expected regex pattern matches somewhere in the output."""
    return re.search(pattern, output, re.DOTALL) is not None


def json_contains(output: str, expected: str) -> bool:
    """True when the output is valid JSON containing every expected key/value pair.

    ``expected`` must be a JSON object; each of its top-level keys must exist in
    the parsed output with an equal value. Nested values can be addressed with
    dot-separated paths, e.g. ``{"model.name": "gpt-4o"}`` matches
    ``{"model": {"name": "gpt-4o"}}``. Returns False when the output or the
    expected value is not valid JSON (or the expected value is not an object),
    so malformed cases fail the case instead of crashing the run.
    """
    try:
        payload = json.loads(output)
        checks = json.loads(expected)
    except ValueError:
        return False
    if not isinstance(checks, dict):
        return False
    for path, wanted in checks.items():
        current = payload
        for part in str(path).split("."):
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]
        if current != wanted:
            return False
    return True


JUDGES = {
    "exact": exact_match,
    "contains": contains,
    "regex": regex_match,
    "json_contains": json_contains,
}


def evaluate(judge: str, output: str, expected: str) -> bool:
    """Run a named judge against an output. Raises ValueError for unknown judges."""
    try:
        fn = JUDGES[judge]
    except KeyError:
        raise ValueError(
            f"Unknown judge {judge!r}. Choose from: {sorted(JUDGES)}"
        ) from None
    return fn(output, expected)
