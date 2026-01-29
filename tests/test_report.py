from __future__ import annotations

from datetime import datetime, timezone

from odlt.models import BenchArtifacts, BenchMetrics, BenchRun, ModelInfo, SystemInfo
from odlt.report import render_report_markdown


def test_render_report_markdown() -> None:
    run = BenchRun(
        run_id="20260101_000000",
        system=SystemInfo(
            timestamp=datetime.now(timezone.utc),
            platform="test",
            python_version="3.11",
            machine="arm64",
            processor="test",
            cpu_count=8,
        ),
        model=ModelInfo(
            model_id="test/model",
            file="model.gguf",
            path="/tmp/model.gguf",
        ),
        metrics=BenchMetrics(
            load_time_s=1.0,
            load_time_source="llama-cli",
            prompt_tps=10.0,
            generation_tps=20.0,
            ttft_s=0.05,
            peak_rss_bytes=1024 * 1024,
        ),
        llama_bench=[],
        llama_cli={"prompt": "hi", "n_predict": 8, "stdout": "ok", "stderr": "", "wall_time_s": 0.1},
        artifacts=BenchArtifacts(metrics_path="runs/x/metrics.json", run_dir="runs/x"),
    )
    report = render_report_markdown([run])
    assert "Benchmark Report" in report
    assert "model.gguf" in report
