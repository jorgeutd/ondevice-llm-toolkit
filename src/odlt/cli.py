"""Command-line interface for ODLT."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from odlt.bench import run_benchmark
from odlt.config import load_config
from odlt.errors import ODLTError
from odlt.gguf import create_manifest, download_gguf, smoke_test, verify_gguf
from odlt.llama import build_llama_cpp
from odlt.logging_utils import configure_logging
from odlt.report import load_runs, write_report


app = typer.Typer(add_completion=False, no_args_is_help=True)
bench_app = typer.Typer(no_args_is_help=True)
gguf_app = typer.Typer(no_args_is_help=True)
deps_app = typer.Typer(no_args_is_help=True)
console = Console()


@app.callback()
def main(verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging")) -> None:
    """OnDevice LLM Toolkit CLI."""
    configure_logging(level=10 if verbose else 20)


def _native_helper(cfg) -> Path | None:
    candidates = [
        cfg.paths.native_bin_dir / "odlt_run",
        Path(__file__).resolve().parents[3] / "bin" / "odlt_run",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _handle_error(exc: ODLTError) -> None:
    console.print(f"Error: {exc}")


@bench_app.command("run")
def bench_run(
    model_path: Optional[Path] = typer.Option(
        None, "--model-path", help="Path to GGUF model"
    ),
    prompt: str = typer.Option(
        "Say hello in one sentence.", "--prompt", help="Prompt for llama-cli"
    ),
    n_predict: int = typer.Option(32, "--n-predict", min=1, help="Tokens to predict"),
    n_prompt: int = typer.Option(512, "--n-prompt", min=0, help="Prompt size"),
    n_gen: int = typer.Option(128, "--n-gen", min=0, help="Generation size"),
    repetitions: int = typer.Option(5, "--repetitions", min=1, help="Benchmark repeats"),
    threads: Optional[int] = typer.Option(None, "--threads", min=1, help="Thread count"),
    n_gpu_layers: Optional[int] = typer.Option(
        None, "--n-gpu-layers", min=0, help="GPU layers"
    ),
) -> None:
    """Run llama-bench and llama-cli, store metrics JSON."""
    try:
        cfg = load_config()
        helper = _native_helper(cfg)
        model_path = model_path or (cfg.paths.models_dir / cfg.model.file)
        run = run_benchmark(
            cfg,
            model_path=model_path,
            prompt=prompt,
            n_predict=n_predict,
            n_prompt=n_prompt,
            n_gen=n_gen,
            repetitions=repetitions,
            threads=threads,
            n_gpu_layers=n_gpu_layers,
            helper_path=helper,
        )
        console.print(f"Metrics written to: {run.artifacts.metrics_path}")
    except ODLTError as exc:
        _handle_error(exc)
        raise typer.Exit(code=1) from exc


@bench_app.command("report")
def bench_report(
    runs_dir: Optional[Path] = typer.Option(
        None, "--runs-dir", help="Directory containing runs"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output-dir", help="Output report directory"
    ),
) -> None:
    """Aggregate run metrics into markdown + charts."""
    try:
        cfg = load_config()
        runs_dir = runs_dir or cfg.paths.runs_dir
        output_dir = output_dir or (cfg.paths.reports_dir / utc_timestamp())
        runs = load_runs(runs_dir)
        report_path = write_report(runs, output_dir)
        console.print(f"Report written to: {report_path}")
    except ODLTError as exc:
        _handle_error(exc)
        raise typer.Exit(code=1) from exc


@gguf_app.command("download")
def gguf_download(
    model_id: Optional[str] = typer.Option(None, "--model-id", help="HF model id"),
    filename: Optional[str] = typer.Option(None, "--file", help="GGUF filename"),
    revision: Optional[str] = typer.Option(None, "--revision", help="Model revision"),
    token: Optional[str] = typer.Option(None, "--token", help="HF token"),
    force_download: bool = typer.Option(False, "--force", help="Force download"),
) -> None:
    """Download a GGUF model from Hugging Face."""
    try:
        cfg = load_config()
        model_id = model_id or cfg.model.model_id
        filename = filename or cfg.model.file
        revision = revision or cfg.model.revision
        path = download_gguf(
            cfg,
            model_id=model_id,
            filename=filename,
            revision=revision,
            token=token,
            force_download=force_download,
        )
        console.print(f"Downloaded to: {path}")
    except ODLTError as exc:
        _handle_error(exc)
        raise typer.Exit(code=1) from exc


@gguf_app.command("verify")
def gguf_verify(
    file_path: Path = typer.Option(..., "--file-path", help="GGUF file path"),
    expected_sha256: Optional[str] = typer.Option(
        None, "--expected-sha256", help="Expected SHA256"
    ),
) -> None:
    """Verify checksum and size of a GGUF file."""
    try:
        info = verify_gguf(file_path, expected_sha256=expected_sha256)
        table = Table(title="GGUF Verification")
        table.add_column("SHA256")
        table.add_column("Size (bytes)")
        table.add_row(str(info["sha256"]), str(info["size"]))
        console.print(table)
    except ODLTError as exc:
        _handle_error(exc)
        raise typer.Exit(code=1) from exc


@gguf_app.command("manifest")
def gguf_manifest(
    file_path: Path = typer.Option(..., "--file-path", help="GGUF file path"),
    model_id: Optional[str] = typer.Option(None, "--model-id", help="HF model id"),
    license_name: Optional[str] = typer.Option(
        None, "--license", help="Model license"
    ),
    output_path: Optional[Path] = typer.Option(
        None, "--output", help="Output manifest path"
    ),
) -> None:
    """Create a minimal GGUF manifest JSON."""
    try:
        cfg = load_config()
        manifest = create_manifest(
            model_id=model_id or cfg.model.model_id,
            file_path=file_path,
            license_name=license_name or cfg.model.license,
        )
        output_path = output_path or Path("manifest.json")
        output_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"Manifest written to: {output_path}")
    except ODLTError as exc:
        _handle_error(exc)
        raise typer.Exit(code=1) from exc


@gguf_app.command("smoke")
def gguf_smoke(
    model_path: Optional[Path] = typer.Option(
        None, "--model-path", help="Path to GGUF model"
    ),
    prompt: str = typer.Option(
        "Respond with a short JSON object.", "--prompt", help="Smoke prompt"
    ),
    n_predict: int = typer.Option(32, "--n-predict", min=1, help="Tokens to predict"),
) -> None:
    """Run a short llama-cli prompt and validate output."""
    try:
        cfg = load_config()
        helper = _native_helper(cfg)
        model_path = model_path or (cfg.paths.models_dir / cfg.model.file)
        result = smoke_test(
            cfg,
            model_path=model_path,
            prompt=prompt,
            n_predict=n_predict,
            helper_path=helper,
        )
        console.print(f"Smoke ok: {result.ok}")
    except ODLTError as exc:
        _handle_error(exc)
        raise typer.Exit(code=1) from exc


@deps_app.command("build-llama")
def deps_build_llama(
    cmake_arg: list[str] = typer.Option(
        [], "--cmake-arg", help="Extra cmake args"
    ),
) -> None:
    """Clone and build llama.cpp with CMake."""
    try:
        cfg = load_config()
        paths = build_llama_cpp(cfg, cmake_args=cmake_arg)
        console.print(f"Built llama.cpp at: {paths.build_dir}")
    except ODLTError as exc:
        _handle_error(exc)
        raise typer.Exit(code=1) from exc


def utc_timestamp() -> str:
    """UTC timestamp for report directories."""
    from odlt.utils import utc_now

    return utc_now().strftime("%Y%m%d_%H%M%S")


app.add_typer(bench_app, name="bench")
app.add_typer(gguf_app, name="gguf")
app.add_typer(deps_app, name="deps")
