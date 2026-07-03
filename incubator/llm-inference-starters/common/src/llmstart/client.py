"""Streaming client for OpenAI-compatible chat-completions endpoints."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import httpx

from llmstart.metrics import RequestTiming, compute_timing
from llmstart.streaming import (
    extract_completion_tokens,
    extract_content_delta,
    parse_sse_line,
)


class StreamingClient:
    def __init__(
        self,
        base_url: str,
        api_key: str = "not-needed",
        timeout_s: float = 300.0,
    ) -> None:
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout_s,
        )

    def list_models(self) -> list[str]:
        resp = self._http.get("/models")
        resp.raise_for_status()
        return [m["id"] for m in resp.json().get("data", [])]

    def timed_completion(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 128,
        temperature: float = 0.0,
        on_delta: Callable[[str], None] | None = None,
    ) -> RequestTiming:
        """Stream one completion and measure TTFT and decode rate."""
        body: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
            # Ask for a final usage chunk; servers that don't support this
            # ignore it and we fall back to counting deltas.
            "stream_options": {"include_usage": True},
        }
        start_t = time.monotonic()
        first_delta_t: float | None = None
        last_delta_t: float | None = None
        chunk_count = 0
        usage_tokens: int | None = None
        with self._http.stream("POST", "/chat/completions", json=body) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                chunk = parse_sse_line(line)
                if chunk is None:
                    continue
                tokens = extract_completion_tokens(chunk)
                if tokens is not None:
                    usage_tokens = tokens
                delta = extract_content_delta(chunk)
                if delta is None:
                    continue
                now = time.monotonic()
                if first_delta_t is None:
                    first_delta_t = now
                last_delta_t = now
                chunk_count += 1
                if on_delta is not None:
                    on_delta(delta)
        end_t = time.monotonic()
        if first_delta_t is None or last_delta_t is None:
            raise RuntimeError("stream ended without any content deltas")
        return compute_timing(
            start_t=start_t,
            first_delta_t=first_delta_t,
            last_delta_t=last_delta_t,
            end_t=end_t,
            chunk_count=chunk_count,
            usage_completion_tokens=usage_tokens,
        )

    def close(self) -> None:
        self._http.close()
