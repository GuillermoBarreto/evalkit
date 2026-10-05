"""Eval cases: a suite is a YAML list of {name, prompt, expected, judge} mappings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

import yaml

from .judges import JUDGES


@dataclass
class EvalCase:
    name: str
    prompt: str
    expected: str = ""
    judge: str = "contains"

    def __post_init__(self) -> None:
        if self.judge not in JUDGES:
            raise ValueError(
                f"Case {self.name!r} uses unknown judge {self.judge!r}. "
                f"Choose from: {sorted(JUDGES)}"
            )


def load_suite(path: Union[str, Path]) -> list[EvalCase]:
    """Load a YAML eval suite file into a list of EvalCase objects."""
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(
            f"Eval suite must be a YAML list of cases, got {type(data).__name__}: {path}"
        )
    cases: list[EvalCase] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Case #{i} must be a mapping, got {type(item).__name__}")
        try:
            cases.append(
                EvalCase(
                    name=str(item["name"]),
                    prompt=str(item["prompt"]),
                    expected=str(item.get("expected", "")),
                    judge=str(item.get("judge", "contains")),
                )
            )
        except KeyError as exc:
            raise ValueError(f"Case #{i} is missing required field {exc}") from exc
    return cases
