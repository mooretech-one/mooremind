"""OpenAI-compatible chat calls using the standard library.

Ollama's local server is the intended endpoint
(``http://localhost:11434/v1``). Nothing here imports an HTTP package.
Thinking is off: ``think`` false, ``reasoning_effort`` ``none``, and a
``/no_think`` prefix on the user message.
"""

from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_TIMEOUT = 120.0
DEFAULT_MAX_TOKENS = 512
DEFAULT_SEED = 0


class ChatClient(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str:
        """Return the assistant content, or raise ``TransportError``."""


class TransportError(Exception):
    """The server was not reached, timed out, or returned a bad envelope."""

    def __init__(self, kind: str, detail: str) -> None:
        self.kind = kind
        super().__init__(detail)


@dataclass(frozen=True)
class LlmSettings:
    base_url: str
    model: str
    api_key: str
    timeout: float
    max_tokens: int
    seed: int

    def require_model(self) -> None:
        if not self.model.strip():
            raise TransportError(
                "config",
                "Set MOOREMIND_LLM_MODEL to the model name, for example gemma3:1b.",
            )


def settings_from_env() -> LlmSettings:
    """Read the tower settings. The harness builds learners with no arguments."""
    model = os.environ.get("MOOREMIND_LLM_MODEL", "").strip()
    base = os.environ.get("MOOREMIND_LLM_BASE_URL", DEFAULT_BASE_URL).strip()
    key = os.environ.get("MOOREMIND_LLM_API_KEY", "").strip()
    if not key:
        key = os.environ.get("OPENAI_API_KEY", "").strip()
    timeout = float(os.environ.get("MOOREMIND_LLM_TIMEOUT", str(DEFAULT_TIMEOUT)))
    max_tokens = int(os.environ.get("MOOREMIND_LLM_MAX_TOKENS", str(DEFAULT_MAX_TOKENS)))
    seed = int(os.environ.get("MOOREMIND_LLM_SEED", str(DEFAULT_SEED)))
    return LlmSettings(
        base_url=base.rstrip("/"),
        model=model,
        api_key=key,
        timeout=timeout,
        max_tokens=max_tokens,
        seed=seed,
    )


def request_body(settings: LlmSettings, messages: list[dict[str, str]]) -> dict[str, Any]:
    """One chat completion. Thinking is always off."""
    return {
        "max_tokens": settings.max_tokens,
        "messages": messages,
        "model": settings.model,
        "reasoning_effort": "none",
        "seed": settings.seed,
        "temperature": 0,
        "think": False,
    }


def with_no_think(text: str) -> str:
    return f"/no_think\n\n{text}"


class UrllibChat:
    """POST ``{base}/chat/completions`` and return ``message.content`` only."""

    def __init__(self, settings: LlmSettings) -> None:
        self.settings = settings

    def complete(self, messages: list[dict[str, str]]) -> str:
        self.settings.require_model()
        url = self.settings.base_url + "/chat/completions"
        payload = json.dumps(request_body(self.settings, messages)).encode("utf-8")
        request = urllib.request.Request(url, data=payload, method="POST")
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json")
        if self.settings.api_key:
            request.add_header("Authorization", f"Bearer {self.settings.api_key}")
        try:
            with urllib.request.urlopen(request, timeout=self.settings.timeout) as response:
                raw = response.read().decode("utf-8")
        except TimeoutError as exc:
            raise TransportError("timeout", str(exc)) from exc
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            raise TransportError("http", f"{exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            reason = exc.reason
            if isinstance(reason, (TimeoutError, socket.timeout)):
                raise TransportError("timeout", str(reason)) from exc
            raise TransportError("http", str(reason)) from exc
        return _content(raw)


def _content(raw: str) -> str:
    try:
        body = json.loads(raw)
        message = body["choices"][0]["message"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise TransportError("http", "chat response had no message content") from exc
    content = message.get("content") if isinstance(message, dict) else None
    if content is None:
        return ""
    if not isinstance(content, str):
        raise TransportError("http", "chat content was not text")
    return content
