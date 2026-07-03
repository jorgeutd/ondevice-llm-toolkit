"""Command-line interface: probe an endpoint, run a micro-benchmark."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from llmstart.client import StreamingClient
from llmstart.metrics import summarize

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()

DEFAULT_PROMPT = (
    "Explain the difference between throughput and latency in three short sentences."
)


@app.command("probe")
def probe(
    base_url: str = typer.Option(..., "--base-url", help="OpenAI-compatible endpoint"),
    api_key: str = typer.Option("not-needed", "--api-key", envvar="LLMSTART_API_KEY"),
) -> None:
    """Check an endpoint is alive and list its models."""
    client = StreamingClient(base_url=base_url, api_key=api_key)
    try:
        models = client.list_models()
    finally:
        client.close()
    console.print(f"[green]OK[/green] {base_url} is serving {len(models)} model(s):")
    for model in models:
        console.print(f"  - {model}")


@app.command("bench")
def bench(
    base_url: str = typer.Option(..., "--base-url", help="OpenAI-compatible endpoint"),
    model: str = typer.Option(..., "--model", help="Model name as known by the server"),
    api_key: str = typer.Option("not-needed", "--api-key", envvar="LLMSTART_API_KEY"),
    prompt: str = typer.Option(DEFAULT_PROMPT, "--prompt"),
    requests: int = typer.Option(5, "--requests", min=1, help="Measured requests"),
    warmup: int = typer.Option(1, "--warmup", min=0, help="Unmeasured warmup requests"),
    max_tokens: int = typer.Option(128, "--max-tokens", min=1),
) -> None:
    """Measure TTFT and decode tokens/sec over sequential streaming requests."""
    client = StreamingClient(base_url=base_url, api_key=api_key)
    try:
        for i in range(warmup):
            console.print(f"warmup {i + 1}/{warmup} ...")
            client.timed_completion(model=model, prompt=prompt, max_tokens=max_tokens)
        timings = []
        for i in range(requests):
            timing = client.timed_completion(model=model, prompt=prompt, max_tokens=max_tokens)
            tps = f"{timing.decode_tps:.1f} tok/s" if timing.decode_tps else "n/a"
            console.print(
                f"request {i + 1}/{requests}: ttft={timing.ttft_s:.3f}s "
                f"decode={tps} tokens={timing.completion_tokens}"
            )
            timings.append(timing)
    finally:
        client.close()

    summary = summarize(timings)
    table = Table(title=f"Benchmark: {model} ({summary.n} requests)")
    table.add_column("metric")
    table.add_column("p50", justify="right")
    table.add_column("p95", justify="right")
    table.add_column("worst", justify="right")
    table.add_row(
        "time to first token",
        f"{summary.ttft_p50:.3f}s",
        f"{summary.ttft_p95:.3f}s",
        f"{summary.ttft_max:.3f}s",
    )
    table.add_row(
        "decode tokens/sec",
        _fmt(summary.tps_p50),
        _fmt(summary.tps_p95),
        _fmt(summary.tps_min),
    )
    table.add_row(
        "total request time",
        f"{summary.total_p50:.2f}s",
        f"{summary.total_p95:.2f}s",
        f"{summary.total_max:.2f}s",
    )
    console.print(table)
    console.print(f"token counts from: {summary.tokens_source}")


def _fmt(value: float | None) -> str:
    return f"{value:.1f}" if value is not None else "n/a"
