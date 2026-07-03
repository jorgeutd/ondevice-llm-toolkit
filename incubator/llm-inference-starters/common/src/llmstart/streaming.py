"""Parsing helpers for OpenAI-compatible SSE streaming responses.

Kept free of I/O so the parsing logic is unit-testable without a server.
"""

from __future__ import annotations

import json
from typing import Any

DONE_SENTINEL = "[DONE]"


def parse_sse_line(line: str) -> dict[str, Any] | None:
    """Parse one SSE line into a chunk dict.

    Returns None for blank lines, comments, non-data fields, and the
    [DONE] sentinel. Raises ValueError on malformed JSON payloads so the
    caller can surface a clear protocol error.
    """
    line = line.strip()
    if not line or line.startswith(":") or not line.startswith("data:"):
        return None
    payload = line[len("data:"):].strip()
    if payload == DONE_SENTINEL:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed SSE data payload: {payload[:200]!r}") from exc


def extract_content_delta(chunk: dict[str, Any]) -> str | None:
    """Content text carried by a stream chunk, or None if it has none."""
    choices = chunk.get("choices") or []
    if not choices:
        return None
    return (choices[0].get("delta") or {}).get("content") or None


def extract_completion_tokens(chunk: dict[str, Any]) -> int | None:
    """Completion token count from a usage-bearing chunk, if present."""
    usage = chunk.get("usage")
    if usage is None:
        return None
    tokens = usage.get("completion_tokens")
    return int(tokens) if tokens is not None else None
