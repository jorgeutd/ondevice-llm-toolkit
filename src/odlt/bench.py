"""Benchmarking workflows."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from odlt.config import AppConfig
from odlt.errors import CommandError, ValidationError
from odlt.llama import ensure_llama_cpp
from odlt.models import BenchArtifacts, BenchMetrics, BenchRun, LlamaBenchRecord, ModelInfo, SystemInfo
from odlt.process import run_command, run_with_metrics
from odlt.utils import file_size_bytes, sha256_file, system_metadata, utc_now


def run_benchmark(
    cfg: AppConfig,
    *,
    model_path: Path,
    prompt: str,
    n_predict: int,
    n_prompt: int,
    n_gen: int,
    repetitions: int,
    threads: Optional[int] = None,
    n_gpu_layers: Optional[int] = None,
    helper_path: Path | None = None,
) -> BenchRun:
    """Run llama-bench and llama-cli, then store metrics.

    Args:
        cfg: Application config.
        model_path: Path to GGUF model.
        prompt: Prompt for llama-cli.
        n_predict: Tokens to predict for llama-cli.
        n_prompt: Prompt length for llama-bench.
        n_gen: Generation length for llama-bench.
        repetitions: Repetitions for llama-bench.
        threads: Optional thread count.
        n_gpu_layers: Optional GPU layer count.
        helper_path: Optional native helper.

    Returns:
        BenchRun object.
    """
    if not model_path.exists():
        raise ValidationError(f"Model file not found: {model_path}")
    if not prompt.strip():
        raise ValidationError("Prompt must not be empty.")

    llama_paths = ensure_llama_cpp(cfg)

    bench_cmd = [
        str(llama_paths.bench_path),
        "-m",
        str(model_path),
        "-o",
        "json",
        "-p",
        str(n_prompt),
        "-n",
        str(n_gen),
        "-r",
        str(repetitions),
    ]
    if threads:
        bench_cmd.extend(["-t", str(threads)])
    if n_gpu_layers is not None:
        bench_cmd.extend(["-ngl", str(n_gpu_layers)])

    bench_result = run_command(bench_cmd, cwd=llama_paths.build_dir)
    if bench_result.exit_code != 0:
        raise CommandError(f"llama-bench failed: {bench_result.stderr}")

    try:
        bench_rows = json.loads(bench_result.stdout)
    except json.JSONDecodeError as exc:
        raise CommandError(f"Failed to parse llama-bench output: {exc}") from exc
    if not isinstance(bench_rows, list):
        raise CommandError("llama-bench output must be a JSON list.")
    if not bench_rows:
        raise CommandError("llama-bench output is empty.")

    prompt_tps = _extract_tokens_per_second(bench_rows, mode="prompt")
    generation_tps = _extract_tokens_per_second(bench_rows, mode="generation")
    ttft = (1.0 / generation_tps) if generation_tps and generation_tps > 0 else None

    cli_cmd = [
        str(llama_paths.cli_path),
        "-m",
        str(model_path),
        "-p",
        prompt,
        "-n",
        str(n_predict),
        "--simple-io",
        "--no-display-prompt",
        "--show-timings",
    ]

    cli_result = run_with_metrics(
        cli_cmd, cwd=llama_paths.build_dir, helper_path=helper_path
    )
    if cli_result.exit_code != 0:
        raise CommandError(f"llama-cli failed: {cli_result.stderr}")
    load_time_s = _parse_load_time(cli_result.stderr + cli_result.stdout)
    load_time_source = "llama-cli"
    if load_time_s is None:
        load_time_s = cli_result.wall_time_s
        load_time_source = "wall-time"

    run_id = utc_now().strftime("%Y%m%d_%H%M%S")
    run_dir = cfg.paths.runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = run_dir / "metrics.json"

    system = SystemInfo(timestamp=utc_now(), **system_metadata())
    model_info = ModelInfo(
        model_id=cfg.model.model_id,
        file=model_path.name,
        path=str(model_path),
        revision=cfg.model.revision,
        license=cfg.model.license,
        sha256=sha256_file(model_path),
        size_bytes=file_size_bytes(model_path),
    )

    metrics = BenchMetrics(
        load_time_s=load_time_s,
        load_time_source=load_time_source,
        prompt_tps=prompt_tps,
        generation_tps=generation_tps,
        ttft_s=ttft,
        peak_rss_bytes=cli_result.peak_rss_bytes,
    )

    payload = BenchRun(
        run_id=run_id,
        system=system,
        model=model_info,
        metrics=metrics,
        llama_bench=bench_rows,
        llama_cli={
            "prompt": prompt,
            "n_predict": n_predict,
            "stdout": _strip_timings(cli_result.stdout),
            "stderr": cli_result.stderr,
            "wall_time_s": cli_result.wall_time_s,
        },
        artifacts=BenchArtifacts(metrics_path=str(metrics_path), run_dir=str(run_dir)),
    )
    metrics_path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
    return payload


def _extract_tokens_per_second(rows: list[dict[str, Any]], *, mode: str) -> float | None:
    """Extract tokens/sec for prompt or generation test."""
    records = []
    for row in rows:
        try:
            record = LlamaBenchRecord.model_validate(row)
        except Exception:
            continue
        records.append((row, record))

    for row, record in records:
        if mode == "prompt":
            if row.get("n_prompt", 0) > 0 and row.get("n_gen", 0) == 0:
                return float(record.avg_ts)
        if mode == "generation":
            if row.get("n_gen", 0) > 0:
                return float(record.avg_ts)
    return None


def _parse_load_time(output: str) -> float | None:
    """Parse load time from llama-cli output."""
    match = re.search(r"load time\s*=\s*([0-9.]+)\s*ms", output)
    if not match:
        return None
    return float(match.group(1)) / 1000.0


def _strip_timings(text: str) -> str:
    """Remove timing lines from llama-cli output."""
    lines = []
    for line in text.splitlines():
        if "llama_print_timings" in line:
            continue
        lines.append(line)
    return "\n".join(lines).strip()
