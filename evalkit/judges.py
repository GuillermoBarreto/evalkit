"""Deterministic judges: exact, contains, and regex matching."""

from __future__ import annotations

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


JUDGES = {
    "exact": exact_match,
    "contains": contains,
    "regex": regex_match,
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
