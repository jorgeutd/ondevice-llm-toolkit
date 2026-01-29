"""Report generation for benchmark runs."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from odlt.errors import ValidationError
from odlt.models import BenchRun


def load_runs(runs_dir: Path) -> list[BenchRun]:
    """Load metrics.json files from run directories."""
    if not runs_dir.exists():
        raise ValidationError(f"Runs directory not found: {runs_dir}")
    runs: list[BenchRun] = []
    for metrics_path in sorted(runs_dir.glob("*/metrics.json")):
        try:
            runs.append(BenchRun.model_validate_json(metrics_path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return runs


def render_report_markdown(runs: list[BenchRun]) -> str:
    """Render a markdown report from runs."""
    lines = [
        "# Benchmark Report",
        "",
        "| Run | Model | Prompt t/s | Gen t/s | TTFT (s) | Load (s) | Peak RSS (MB) |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for run in runs:
        prompt_tps = _fmt(run.metrics.prompt_tps)
        gen_tps = _fmt(run.metrics.generation_tps)
        ttft = _fmt(run.metrics.ttft_s)
        load_time = _fmt(run.metrics.load_time_s)
        peak_rss = _fmt(_bytes_to_mb(run.metrics.peak_rss_bytes))
        lines.append(
            f"| {run.run_id} | {run.model.file} | {prompt_tps} | {gen_tps} | {ttft} | {load_time} | {peak_rss} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_report(runs: list[BenchRun], output_dir: Path) -> Path:
    """Write markdown report and charts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    charts_dir = output_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / "report.md"
    content = render_report_markdown(runs)

    if runs:
        _plot_tokens_per_second(runs, charts_dir / "tokens_per_second.png")
        _plot_peak_rss(runs, charts_dir / "peak_rss.png")
        content += "\n## Charts\n\n![](charts/tokens_per_second.png)\n\n![](charts/peak_rss.png)\n"
    report_path.write_text(content, encoding="utf-8")
    return report_path


def _plot_tokens_per_second(runs: list[BenchRun], path: Path) -> None:
    labels = [run.run_id for run in runs]
    prompt = [run.metrics.prompt_tps or 0 for run in runs]
    gen = [run.metrics.generation_tps or 0 for run in runs]

    x = range(len(labels))
    width = 0.4
    plt.figure(figsize=(10, 4))
    plt.bar([i - width / 2 for i in x], prompt, width=width, label="prompt t/s")
    plt.bar([i + width / 2 for i in x], gen, width=width, label="gen t/s")
    plt.xticks(list(x), labels, rotation=45, ha="right")
    plt.ylabel("tokens/sec")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def _plot_peak_rss(runs: list[BenchRun], path: Path) -> None:
    labels = [run.run_id for run in runs]
    rss = [_bytes_to_mb(run.metrics.peak_rss_bytes) or 0 for run in runs]
    x = range(len(labels))
    plt.figure(figsize=(10, 4))
    plt.bar(list(x), rss)
    plt.xticks(list(x), labels, rotation=45, ha="right")
    plt.ylabel("Peak RSS (MB)")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def _bytes_to_mb(value: int | None) -> float | None:
    if value is None:
        return None
    return value / (1024 * 1024)


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"
