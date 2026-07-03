"""Task schema and loading.

A task is a single prompt sent to the model together with a set of tool
definitions (OpenAI function-calling format) and an expectation describing
the correct behavior. Tasks are stored as YAML files, one list per file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, model_validator

Category = Literal["tool_call", "no_tool", "structured_output"]


class Expectation(BaseModel):
    """Describes the correct model behavior for a task.

    - tool_call tasks: `tool_name` is required; `arguments` optionally pins
      the exact or subset argument values.
    - no_tool tasks: the model must answer directly without calling a tool.
    - structured_output tasks: `json_schema` is required; the response body
      must be valid JSON conforming to the schema.
    """

    tool_name: str | None = None
    arguments: dict[str, Any] | None = None
    argument_match: Literal["exact", "subset"] = "exact"
    json_schema: dict[str, Any] | None = None


class Task(BaseModel):
    id: str
    category: Category
    prompt: str
    system: str | None = None
    tools: list[dict[str, Any]] = Field(default_factory=list)
    expected: Expectation

    @model_validator(mode="after")
    def _check_consistency(self) -> Task:
        if self.category == "tool_call":
            if not self.expected.tool_name:
                raise ValueError(f"task {self.id}: tool_call tasks require expected.tool_name")
            if not self.tools:
                raise ValueError(f"task {self.id}: tool_call tasks require tool definitions")
        if self.category == "structured_output" and not self.expected.json_schema:
            raise ValueError(
                f"task {self.id}: structured_output tasks require expected.json_schema"
            )
        return self


def load_tasks(tasks_dir: Path) -> list[Task]:
    """Load every task from all YAML files in `tasks_dir`, sorted by id."""
    if not tasks_dir.is_dir():
        raise FileNotFoundError(f"tasks directory not found: {tasks_dir}")
    tasks: list[Task] = []
    for path in sorted(tasks_dir.glob("*.yaml")):
        payload = yaml.safe_load(path.read_text())
        if payload is None:
            continue
        if not isinstance(payload, list):
            raise ValueError(f"{path}: expected a YAML list of tasks")
        tasks.extend(Task.model_validate(item) for item in payload)
    seen: set[str] = set()
    for task in tasks:
        if task.id in seen:
            raise ValueError(f"duplicate task id: {task.id}")
        seen.add(task.id)
    return sorted(tasks, key=lambda t: t.id)
