"""Minimal OpenAI-compatible chat-completions client.

Works against any server that speaks the /v1/chat/completions protocol:
llama.cpp `llama-server`, vLLM, SGLang, Ollama, LM Studio, or hosted APIs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: str  # raw JSON string as returned by the model


@dataclass(frozen=True)
class ModelResponse:
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)


class ChatClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "not-needed",
        temperature: float = 0.0,
        seed: int | None = 42,
        timeout_s: float = 120.0,
    ) -> None:
        self._model = model
        self._temperature = temperature
        self._seed = seed
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout_s,
        )

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> ModelResponse:
        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
        }
        if self._seed is not None:
            body["seed"] = self._seed
        if tools:
            body["tools"] = tools
        resp = self._http.post("/chat/completions", json=body)
        resp.raise_for_status()
        return parse_completion(resp.json())

    def close(self) -> None:
        self._http.close()


def parse_completion(payload: dict[str, Any]) -> ModelResponse:
    """Extract content and tool calls from a chat-completions response."""
    message = payload["choices"][0]["message"]
    calls = [
        ToolCall(
            name=tc["function"]["name"],
            arguments=tc["function"].get("arguments") or "{}",
        )
        for tc in message.get("tool_calls") or []
    ]
    return ModelResponse(content=message.get("content"), tool_calls=calls)
