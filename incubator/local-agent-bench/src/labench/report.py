"""Markdown report rendering for benchmark runs."""

from __future__ import annotations

from labench.runner import RunResult


def render_markdown(result: RunResult) -> str:
    lines = [
        f"# local-agent-bench report: `{result.model}`",
        "",
        f"- Endpoint: `{result.base_url}`",
        f"- Repetitions per task: {result.repetitions}",
        f"- Started: {result.started_at}",
        f"- Duration: {result.duration_s:.1f}s",
        "",
        "| Category | Pass | n | Pass rate | 95% CI (Wilson) |",
        "|---|---|---|---|---|",
    ]
    for category, summary in result.summary().items():
        ci = summary.pass_rate
        lines.append(
            f"| {category} | {summary.passed} | {summary.n} "
            f"| {ci.point:.1%} | [{ci.low:.1%}, {ci.high:.1%}] |"
        )
    overall = result.overall()
    ci = overall.pass_rate
    lines.append(
        f"| **overall** | {overall.passed} | {overall.n} "
        f"| {ci.point:.1%} | [{ci.low:.1%}, {ci.high:.1%}] |"
    )
    if overall.failure_reasons:
        lines += ["", "## Failure breakdown", ""]
        for reason, count in sorted(overall.failure_reasons.items(), key=lambda kv: -kv[1]):
            lines.append(f"- `{reason}`: {count}")
    failures = [s for s in result.scores if not s.passed]
    if failures:
        lines += ["", "## Failed attempts", ""]
        for s in failures:
            lines.append(f"- `{s.task_id}` ({s.reason}): {s.detail}")
    lines.append("")
    return "\n".join(lines)
