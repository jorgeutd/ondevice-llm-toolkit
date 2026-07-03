"""Command-line interface for local-agent-bench."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from labench.client import ChatClient
from labench.report import render_markdown
from labench.runner import run_suite
from labench.stats import bootstrap_diff_ci
from labench.tasks import load_tasks

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()

DEFAULT_TASKS_DIR = Path("tasks")


@app.command("run")
def run(
    base_url: str = typer.Option(
        "http://localhost:8080/v1", "--base-url", help="OpenAI-compatible endpoint"
    ),
    model: str = typer.Option(..., "--model", help="Model name as known by the server"),
    api_key: str = typer.Option("not-needed", "--api-key", envvar="LABENCH_API_KEY"),
    tasks_dir: Path = typer.Option(
        DEFAULT_TASKS_DIR, "--tasks-dir", help="Directory of YAML tasks"
    ),
    repetitions: int = typer.Option(3, "--repetitions", min=1, help="Attempts per task"),
    temperature: float = typer.Option(0.0, "--temperature", min=0.0),
    seed: int = typer.Option(42, "--seed"),
    out: Path = typer.Option(Path("runs/latest.json"), "--out", help="Where to save raw results"),
) -> None:
    """Run the benchmark suite against a model endpoint."""
    tasks = load_tasks(tasks_dir)
    console.print(f"Loaded [bold]{len(tasks)}[/bold] tasks from {tasks_dir}")
    client = ChatClient(
        base_url=base_url, model=model, api_key=api_key, temperature=temperature, seed=seed
    )
    try:
        result = run_suite(
            client,
            tasks,
            model=model,
            base_url=base_url,
            repetitions=repetitions,
            on_score=lambda s: console.print(
                f"  {'[green]PASS[/green]' if s.passed else '[red]FAIL[/red]'} "
                f"{s.task_id} {'' if s.passed else f'({s.reason})'}"
            ),
        )
    finally:
        client.close()
    result.save(out)
    console.print(f"\nRaw results saved to [bold]{out}[/bold]\n")
    _print_summary_table(result)


def _print_summary_table(result) -> None:
    table = Table(title=f"Results: {result.model}")
    table.add_column("category")
    table.add_column("pass", justify="right")
    table.add_column("n", justify="right")
    table.add_column("pass rate", justify="right")
    table.add_column("95% CI (Wilson)", justify="right")
    rows = [*result.summary().items(), ("overall", result.overall())]
    for category, summary in rows:
        ci = summary.pass_rate
        table.add_row(
            category,
            str(summary.passed),
            str(summary.n),
            f"{ci.point:.1%}",
            f"[{ci.low:.1%}, {ci.high:.1%}]",
        )
    console.print(table)


@app.command("report")
def report(
    run_file: Path = typer.Argument(..., help="Raw results JSON produced by `labench run`"),
    out: Path | None = typer.Option(None, "--out", help="Write Markdown report to this path"),
) -> None:
    """Render a Markdown report from a saved run."""
    from labench.runner import RunResult
    from labench.scoring import Score

    payload = json.loads(run_file.read_text())
    result = RunResult(
        model=payload["model"],
        base_url=payload["base_url"],
        repetitions=payload["repetitions"],
        started_at=payload["started_at"],
        duration_s=payload["duration_s"],
        scores=[Score(**s) for s in payload["scores"]],
    )
    markdown = render_markdown(result)
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(markdown)
        console.print(f"Report written to [bold]{out}[/bold]")
    else:
        console.print(markdown)


@app.command("compare")
def compare(
    run_a: Path = typer.Argument(..., help="Raw results JSON for run A"),
    run_b: Path = typer.Argument(..., help="Raw results JSON for run B"),
) -> None:
    """Compare overall pass rates of two runs with a bootstrap CI."""
    a = [s["passed"] for s in json.loads(run_a.read_text())["scores"]]
    b = [s["passed"] for s in json.loads(run_b.read_text())["scores"]]
    ci = bootstrap_diff_ci(a, b)
    console.print(
        f"Pass-rate difference (A - B): {ci.point:+.1%} "
        f"(95% bootstrap CI [{ci.low:+.1%}, {ci.high:+.1%}])"
    )
    if ci.low > 0 or ci.high < 0:
        console.print("[bold]The difference is unlikely to be noise at alpha=0.05.[/bold]")
    else:
        console.print("The CI includes zero: treat the difference as noise.")


@app.command("tasks")
def tasks_list(
    tasks_dir: Path = typer.Option(DEFAULT_TASKS_DIR, "--tasks-dir"),
) -> None:
    """List all tasks in the suite."""
    table = Table(title="Benchmark tasks")
    table.add_column("id")
    table.add_column("category")
    table.add_column("expected")
    for task in load_tasks(tasks_dir):
        if task.category == "tool_call":
            expected = f"call {task.expected.tool_name}"
        elif task.category == "no_tool":
            expected = "answer directly"
        else:
            expected = "JSON matching schema"
        table.add_row(task.id, task.category, expected)
    console.print(table)
