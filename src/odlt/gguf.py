"""GGUF workflows."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from odlt.config import AppConfig
from odlt.errors import ValidationError
from odlt.hf import download_model, verify_repo_file
from odlt.llama import ensure_llama_cpp
from odlt.models import GGUFManifest, SmokeResult
from odlt.process import run_with_metrics
from odlt.utils import file_size_bytes, sha256_file, utc_now


def download_gguf(
    cfg: AppConfig,
    *,
    model_id: str,
    filename: str,
    revision: Optional[str],
    token: Optional[str],
    force_download: bool,
) -> Path:
    """Download a GGUF file from Hugging Face."""
    verify_repo_file(repo_id=model_id, filename=filename, revision=revision, token=token)
    path = asyncio.run(
        download_model(
            repo_id=model_id,
            filename=filename,
            revision=revision,
            local_dir=cfg.paths.models_dir,
            cache_dir=cfg.paths.cache_dir,
            token=token,
            force_download=force_download,
        )
    )
    return path


def verify_gguf(file_path: Path, *, expected_sha256: str | None = None) -> dict[str, str | int]:
    """Verify GGUF file checksum and metadata."""
    if not file_path.exists():
        raise ValidationError(f"GGUF file not found: {file_path}")
    checksum = sha256_file(file_path)
    size = file_size_bytes(file_path)
    if expected_sha256 and expected_sha256.lower() != checksum:
        raise ValidationError(
            f"Checksum mismatch: expected {expected_sha256} got {checksum}"
        )
    return {"sha256": checksum, "size": size}


def create_manifest(
    *,
    model_id: str,
    file_path: Path,
    license_name: str,
) -> GGUFManifest:
    """Create a GGUF manifest."""
    meta = verify_gguf(file_path)
    return GGUFManifest(
        model_id=model_id,
        file=file_path.name,
        sha256=str(meta["sha256"]),
        size=int(meta["size"]),
        license=license_name,
    )


def smoke_test(
    cfg: AppConfig,
    *,
    model_path: Path,
    prompt: str,
    n_predict: int,
    helper_path: Path | None = None,
) -> SmokeResult:
    """Run a short llama-cli prompt and validate output."""
    if not model_path.exists():
        raise ValidationError(f"GGUF file not found: {model_path}")
    if not prompt.strip():
        raise ValidationError("Prompt must not be empty.")

    llama_paths = ensure_llama_cpp(cfg)
    cmd = [
        str(llama_paths.cli_path),
        "-m",
        str(model_path),
        "-p",
        prompt,
        "-n",
        str(n_predict),
        "--simple-io",
        "--no-display-prompt",
    ]
    result = run_with_metrics(cmd, cwd=llama_paths.build_dir, helper_path=helper_path)
    response = _strip_timings(result.stdout)
    ok = result.exit_code == 0 and bool(response)
    smoke = SmokeResult(
        timestamp=utc_now(),
        model_path=str(model_path),
        prompt=prompt,
        response=response,
        ok=ok,
        notes=None if ok else "Empty response or non-zero exit code.",
    )
    SmokeResult.model_validate_json(smoke.model_dump_json())
    return smoke


def _strip_timings(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if "llama_print_timings" in line:
            continue
        lines.append(line)
    return "\n".join(lines).strip()
