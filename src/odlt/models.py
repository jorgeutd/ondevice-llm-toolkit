"""Pydantic models for toolkit outputs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class CommandResult(BaseModel):
    """Execution result with optional metrics."""

    stdout: str
    stderr: str
    exit_code: int
    wall_time_s: float
    peak_rss_bytes: Optional[int] = None


class GGUFManifest(BaseModel):
    """Minimal GGUF manifest."""

    model_id: str
    file: str
    sha256: str
    size: int
    license: str


class SystemInfo(BaseModel):
    """Runtime system metadata for a benchmark."""

    timestamp: datetime
    platform: str
    python_version: str
    machine: str
    processor: str
    cpu_count: int


class ModelInfo(BaseModel):
    """Model metadata for a benchmark."""

    model_id: str
    file: str
    path: str
    revision: Optional[str] = None
    license: Optional[str] = None
    sha256: Optional[str] = None
    size_bytes: Optional[int] = None


class LlamaBenchRecord(BaseModel):
    """Single llama-bench output row."""

    model_config = ConfigDict(extra="allow")

    avg_ts: float = Field(..., description="Average tokens/sec")


class BenchMetrics(BaseModel):
    """Computed benchmark metrics."""

    load_time_s: Optional[float] = None
    load_time_source: Optional[str] = None
    prompt_tps: Optional[float] = None
    generation_tps: Optional[float] = None
    ttft_s: Optional[float] = None
    peak_rss_bytes: Optional[int] = None


class BenchArtifacts(BaseModel):
    """Generated artifacts for a benchmark run."""

    metrics_path: str
    run_dir: str


class BenchRun(BaseModel):
    """Full benchmark run payload."""

    run_id: str
    system: SystemInfo
    model: ModelInfo
    metrics: BenchMetrics
    llama_bench: list[dict[str, Any]]
    llama_cli: dict[str, Any]
    artifacts: BenchArtifacts


class SmokeResult(BaseModel):
    """Smoke test result for GGUF models."""

    timestamp: datetime
    model_path: str
    prompt: str
    response: str
    ok: bool
    notes: Optional[str] = None
