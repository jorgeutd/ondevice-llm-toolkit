"""Benchmark runner: executes every task N times and aggregates results."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

from labench.client import ChatClient
from labench.scoring import Score, score_response
from labench.stats import Interval, wilson_interval
from labench.tasks import Task

DEFAULT_SYSTEM = (
    "You are a precise assistant. When tools are provided, call the correct tool "
    "with correct arguments. When asked for JSON, respond with JSON only."
)


@dataclass(frozen=True)
class CategorySummary:
    n: int
    passed: int
    pass_rate: Interval
    failure_reasons: dict[str, int]


@dataclass
class RunResult:
    model: str
    base_url: str
    repetitions: int
    started_at: str
    duration_s: float = 0.0
    scores: list[Score] = field(default_factory=list)

    def summary(self) -> dict[str, CategorySummary]:
        out: dict[str, CategorySummary] = {}
        for category in sorted({s.category for s in self.scores}):
            scores = [s for s in self.scores if s.category == category]
            passed = sum(s.passed for s in scores)
            reasons: dict[str, int] = {}
            for s in scores:
                if not s.passed:
                    reasons[s.reason] = reasons.get(s.reason, 0) + 1
            out[category] = CategorySummary(
                n=len(scores),
                passed=passed,
                pass_rate=wilson_interval(passed, len(scores)),
                failure_reasons=reasons,
            )
        return out

    def overall(self) -> CategorySummary:
        passed = sum(s.passed for s in self.scores)
        reasons: dict[str, int] = {}
        for s in self.scores:
            if not s.passed:
                reasons[s.reason] = reasons.get(s.reason, 0) + 1
        return CategorySummary(
            n=len(self.scores),
            passed=passed,
            pass_rate=wilson_interval(passed, max(1, len(self.scores))),
            failure_reasons=reasons,
        )

    def to_json(self) -> str:
        return json.dumps(
            {
                "model": self.model,
                "base_url": self.base_url,
                "repetitions": self.repetitions,
                "started_at": self.started_at,
                "duration_s": round(self.duration_s, 2),
                "scores": [asdict(s) for s in self.scores],
            },
            indent=2,
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json())


def run_suite(
    client: ChatClient,
    tasks: list[Task],
    model: str,
    base_url: str,
    repetitions: int = 3,
    on_score: Callable[[Score], None] | None = None,
) -> RunResult:
    result = RunResult(
        model=model,
        base_url=base_url,
        repetitions=repetitions,
        started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    start = time.monotonic()
    for task in tasks:
        messages_base = [{"role": "system", "content": task.system or DEFAULT_SYSTEM}]
        for _ in range(repetitions):
            messages = [*messages_base, {"role": "user", "content": task.prompt}]
            response = client.complete(messages, tools=task.tools or None)
            score = score_response(task, response)
            result.scores.append(score)
            if on_score is not None:
                on_score(score)
    result.duration_s = time.monotonic() - start
    return result
