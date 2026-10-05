"""Model providers.

API keys always come from environment variables, never from files or arguments.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Protocol


class Provider(Protocol):
    name: str

    def complete(self, prompt: str) -> str:
        """Return the model's completion for a prompt."""
        ...


class EchoProvider:
    """Returns the prompt unchanged. Useful for smoke-testing the harness itself."""

    name = "echo"

    def complete(self, prompt: str) -> str:
        return prompt


class DictProvider:
    """Deterministic provider backed by a prompt -> output mapping (loaded from JSON).

    Missing prompts fail the case instead of crashing the run.
    """

    name = "dict"

    def __init__(self, mapping: dict[str, str]):
        self.mapping = mapping

    def complete(self, prompt: str) -> str:
        try:
            return self.mapping[prompt]
        except KeyError:
            raise KeyError(f"DictProvider has no fixture for prompt: {prompt!r}") from None


class OpenAICompatibleProvider:
    """Any OpenAI-compatible chat-completions endpoint.

    The API key is read from the EVALKIT_API_KEY environment variable.
    """

    name = "openai-compatible"

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        api_key_env: str = "EVALKIT_API_KEY",
    ):
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise RuntimeError(
                f"Set the {api_key_env} environment variable to use this provider."
            )
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key

    def complete(self, prompt: str) -> str:
        body = json.dumps(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
