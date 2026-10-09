"""evalkit: a tiny YAML-driven eval harness for LLM prompts and agents."""

from .cases import EvalCase, load_suite
from .judges import JUDGES, evaluate
from .providers import DictProvider, EchoProvider, OpenAICompatibleProvider, Provider
from .runner import EvalResult, diff_reports, run_suite, summarize

__version__ = "0.1.0"

__all__ = [
    "EvalCase",
    "load_suite",
    "JUDGES",
    "evaluate",
    "Provider",
    "DictProvider",
    "EchoProvider",
    "OpenAICompatibleProvider",
    "EvalResult",
    "run_suite",
    "summarize",
    "diff_reports",
]
