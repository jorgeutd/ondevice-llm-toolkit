"""Scoring of model responses against task expectations.

Every score is binary pass/fail with a machine-readable failure reason so
that aggregate reports can break down *why* a model fails, not just how
often. Reasons are stable strings, safe to group by.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from jsonschema import Draft202012Validator

from labench.client import ModelResponse
from labench.tasks import Task

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


@dataclass(frozen=True)
class Score:
    task_id: str
    category: str
    passed: bool
    reason: str  # "ok" on success, stable failure code otherwise
    detail: str = ""


def score_response(task: Task, response: ModelResponse) -> Score:
    if task.category == "tool_call":
        return _score_tool_call(task, response)
    if task.category == "no_tool":
        return _score_no_tool(task, response)
    return _score_structured_output(task, response)


def _score_tool_call(task: Task, response: ModelResponse) -> Score:
    expected = task.expected
    if not response.tool_calls:
        return _fail(task, "no_tool_call", "model answered directly instead of calling a tool")
    if len(response.tool_calls) > 1:
        return _fail(task, "multiple_tool_calls", f"got {len(response.tool_calls)} calls")
    call = response.tool_calls[0]
    if call.name != expected.tool_name:
        return _fail(task, "wrong_tool", f"expected {expected.tool_name!r}, got {call.name!r}")
    try:
        got_args = json.loads(call.arguments)
    except json.JSONDecodeError as exc:
        return _fail(task, "malformed_arguments", str(exc))
    if not isinstance(got_args, dict):
        return _fail(task, "malformed_arguments", "arguments are not a JSON object")
    if expected.arguments is not None:
        if expected.argument_match == "exact" and got_args != expected.arguments:
            return _fail(task, "wrong_arguments", f"expected {expected.arguments}, got {got_args}")
        if expected.argument_match == "subset" and not _is_subset(expected.arguments, got_args):
            return _fail(task, "wrong_arguments", f"missing/mismatched keys in {got_args}")
    return _ok(task)


def _score_no_tool(task: Task, response: ModelResponse) -> Score:
    if response.tool_calls:
        names = [c.name for c in response.tool_calls]
        return _fail(task, "unexpected_tool_call", f"called {names}")
    if not (response.content or "").strip():
        return _fail(task, "empty_response", "no content returned")
    return _ok(task)


def _score_structured_output(task: Task, response: ModelResponse) -> Score:
    if response.tool_calls:
        return _fail(task, "unexpected_tool_call", "structured-output task must answer inline")
    text = (response.content or "").strip()
    if not text:
        return _fail(task, "empty_response", "no content returned")
    parsed = _parse_json_lenient(text)
    if parsed is None:
        return _fail(task, "invalid_json", "content is not parseable JSON")
    validator = Draft202012Validator(task.expected.json_schema)
    errors = sorted(validator.iter_errors(parsed), key=lambda e: e.json_path)
    if errors:
        first = errors[0]
        return _fail(task, "schema_violation", f"{first.json_path}: {first.message}")
    return _ok(task)


def _parse_json_lenient(text: str) -> Any | None:
    """Parse JSON directly, or from the first fenced code block if present."""
    for candidate in (text, *(m.strip() for m in _FENCE_RE.findall(text))):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def _is_subset(expected: dict[str, Any], got: dict[str, Any]) -> bool:
    return all(key in got and got[key] == value for key, value in expected.items())


def _ok(task: Task) -> Score:
    return Score(task_id=task.id, category=task.category, passed=True, reason="ok")


def _fail(task: Task, reason: str, detail: str) -> Score:
    return Score(
        task_id=task.id, category=task.category, passed=False, reason=reason, detail=detail
    )
