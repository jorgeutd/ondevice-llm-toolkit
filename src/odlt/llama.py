"""llama.cpp integration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import os

from odlt.config import AppConfig
from odlt.errors import CommandError
from odlt.process import find_executable, run_command


LLAMA_REPO_URL = "https://github.com/ggml-org/llama.cpp.git"


@dataclass(frozen=True)
class LlamaPaths:
    """Resolved llama.cpp paths."""

    src_dir: Path
    build_dir: Path
    cli_path: Path
    bench_path: Path


def resolve_llama_paths(cfg: AppConfig) -> LlamaPaths:
    """Resolve llama.cpp source/build and tool paths."""
    src_dir = cfg.paths.llama_cpp_dir
    build_dir = cfg.paths.llama_cpp_build_dir
    cli_path = build_dir / "bin" / "llama-cli"
    bench_path = build_dir / "bin" / "llama-bench"
    return LlamaPaths(src_dir=src_dir, build_dir=build_dir, cli_path=cli_path, bench_path=bench_path)


def ensure_llama_cpp(cfg: AppConfig) -> LlamaPaths:
    """Ensure llama.cpp is cloned and built."""
    paths = resolve_llama_paths(cfg)
    if paths.cli_path.exists() and paths.bench_path.exists():
        return paths
    return build_llama_cpp(cfg, cmake_args=cfg.llama.cmake_args)


def build_llama_cpp(cfg: AppConfig, *, cmake_args: Iterable[str] | None = None) -> LlamaPaths:
    """Clone and build llama.cpp at pinned commit.

    Args:
        cfg: App configuration.
        cmake_args: Extra cmake arguments.

    Returns:
        Resolved llama.cpp paths.

    Raises:
        CommandError: If build fails.
    """
    if not find_executable("git"):
        raise CommandError("git is required to build llama.cpp.")
    if not find_executable("cmake"):
        raise CommandError("cmake is required to build llama.cpp.")

    paths = resolve_llama_paths(cfg)
    cmake_args = list(cmake_args or [])

    if not paths.src_dir.exists():
        paths.src_dir.parent.mkdir(parents=True, exist_ok=True)
        result = run_command(["git", "clone", LLAMA_REPO_URL, str(paths.src_dir)])
        if result.exit_code != 0:
            raise CommandError(f"git clone failed: {result.stderr}")

    result = run_command(["git", "fetch", "--all"], cwd=paths.src_dir)
    if result.exit_code != 0:
        raise CommandError(f"git fetch failed: {result.stderr}")

    result = run_command(["git", "checkout", cfg.llama.commit], cwd=paths.src_dir)
    if result.exit_code != 0:
        raise CommandError(f"git checkout failed: {result.stderr}")

    paths.build_dir.mkdir(parents=True, exist_ok=True)
    cmake_config = [
        "cmake",
        "-S",
        str(paths.src_dir),
        "-B",
        str(paths.build_dir),
        "-DCMAKE_BUILD_TYPE=Release",
        *cmake_args,
    ]
    result = run_command(cmake_config, cwd=paths.src_dir)
    if result.exit_code != 0:
        raise CommandError(f"cmake configure failed: {result.stderr}")

    build_cmd = [
        "cmake",
        "--build",
        str(paths.build_dir),
        "--config",
        "Release",
        "-j",
        str(os.cpu_count() or 8),
    ]
    result = run_command(build_cmd, cwd=paths.src_dir)
    if result.exit_code != 0:
        raise CommandError(f"cmake build failed: {result.stderr}")
    return paths
