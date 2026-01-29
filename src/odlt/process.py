"""Process execution helpers."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Iterable

from odlt.errors import CommandError
from odlt.models import CommandResult


def find_executable(name: str) -> str | None:
    """Find an executable on PATH.

    Args:
        name: Executable name.

    Returns:
        Full path or None if not found.
    """
    return shutil.which(name)


def run_command(
    cmd: Iterable[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int | None = None,
) -> CommandResult:
    """Run a command and capture stdout/stderr.

    Args:
        cmd: Command list.
        cwd: Working directory.
        env: Environment variables.
        timeout: Optional timeout in seconds.

    Returns:
        CommandResult with outputs and timing.

    Raises:
        CommandError: If the command fails.
    """
    cmd_list = list(cmd)
    if not cmd_list:
        raise CommandError("Command is empty.")
    start = time.perf_counter()
    result = subprocess.run(
        cmd_list,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    wall_time_s = time.perf_counter() - start
    return CommandResult(
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.returncode,
        wall_time_s=wall_time_s,
    )


def run_with_metrics(
    cmd: Iterable[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int | None = None,
    helper_path: Path | None = None,
) -> CommandResult:
    """Run a command and collect peak RSS metrics.

    Args:
        cmd: Command list.
        cwd: Working directory.
        env: Environment variables.
        timeout: Optional timeout in seconds.
        helper_path: Optional native helper binary path.

    Returns:
        CommandResult with metrics.

    Raises:
        CommandError: If command execution fails.
    """
    cmd_list = list(cmd)
    if not cmd_list:
        raise CommandError("Command is empty.")

    stdout_tmp = tempfile.NamedTemporaryFile(delete=False)
    stderr_tmp = tempfile.NamedTemporaryFile(delete=False)
    stdout_tmp.close()
    stderr_tmp.close()

    if helper_path and helper_path.exists() and helper_path.is_file():
        helper_cmd = [
            str(helper_path),
            "--stdout-path",
            stdout_tmp.name,
            "--stderr-path",
            stderr_tmp.name,
            "--",
            *cmd_list,
        ]
        result = run_command(helper_cmd, cwd=cwd, env=env, timeout=timeout)
        if result.exit_code != 0:
            raise CommandError(
                f"Helper failed with exit code {result.exit_code}: {result.stderr}"
            )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid helper output: {exc}") from exc
        stdout_path = Path(stdout_tmp.name)
        stderr_path = Path(stderr_tmp.name)
        stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace")
        stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
        stdout_path.unlink(missing_ok=True)
        stderr_path.unlink(missing_ok=True)
        return CommandResult(
            stdout=stdout_text,
            stderr=stderr_text,
            exit_code=int(payload.get("exit_code", 1)),
            wall_time_s=float(payload.get("wall_time_sec", 0.0)),
            peak_rss_bytes=payload.get("max_rss_bytes"),
        )

    time_cmd = ["/usr/bin/time", "-l", *cmd_list]
    start = time.perf_counter()
    with Path(stdout_tmp.name).open("w", encoding="utf-8") as stdout_handle, Path(
        stderr_tmp.name
    ).open("w", encoding="utf-8") as stderr_handle:
        result = subprocess.run(
            time_cmd,
            cwd=str(cwd) if cwd else None,
            env=env,
            stdout=stdout_handle,
            stderr=stderr_handle,
            text=True,
            timeout=timeout,
            check=False,
        )
    wall_time_s = time.perf_counter() - start
    stdout_text = Path(stdout_tmp.name).read_text(encoding="utf-8", errors="replace")
    stderr_text = Path(stderr_tmp.name).read_text(encoding="utf-8", errors="replace")
    Path(stdout_tmp.name).unlink(missing_ok=True)
    Path(stderr_tmp.name).unlink(missing_ok=True)
    peak_rss = _parse_time_peak_rss(stderr_text)
    return CommandResult(
        stdout=stdout_text,
        stderr=stderr_text,
        exit_code=result.returncode,
        wall_time_s=wall_time_s,
        peak_rss_bytes=peak_rss,
    )


def _parse_time_peak_rss(stderr_text: str) -> int | None:
    """Parse maximum resident set size from /usr/bin/time output."""
    for line in stderr_text.splitlines():
        line = line.strip()
        if line.endswith("maximum resident set size"):
            value = line.split()[0]
            if value.isdigit():
                return int(value)
    return None
