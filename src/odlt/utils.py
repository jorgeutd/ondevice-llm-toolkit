"""Utility helpers for filesystem, hashing, and retries."""

from __future__ import annotations

import hashlib
import os
import platform
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, TypeVar

from odlt.errors import ValidationError


T = TypeVar("T")


def utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute SHA256 checksum for a file.

    Args:
        path: File path.
        chunk_size: Size of chunks for streaming.

    Returns:
        Hex digest of SHA256.

    Raises:
        ValidationError: If the file does not exist.
    """
    if not path.exists():
        raise ValidationError(f"File does not exist: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_size_bytes(path: Path) -> int:
    """Return file size in bytes.

    Args:
        path: File path.

    Returns:
        File size in bytes.

    Raises:
        ValidationError: If the file does not exist.
    """
    if not path.exists():
        raise ValidationError(f"File does not exist: {path}")
    return path.stat().st_size


def system_metadata() -> dict[str, str | int]:
    """Collect basic system metadata."""
    return {
        "platform": platform.platform(),
        "python_version": sys.version.split()[0],
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count() or 0,
    }


def retry(
    operation: Callable[[], T],
    *,
    retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    retry_on: Iterable[type[Exception]] = (Exception,),
) -> T:
    """Retry an operation with exponential backoff.

    Args:
        operation: Callable to execute.
        retries: Number of attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        retry_on: Exception types to retry on.

    Returns:
        The operation result.

    Raises:
        Exception: Last exception after retries are exhausted.
    """
    if retries < 1:
        raise ValidationError("Retries must be at least 1.")
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            return operation()
        except tuple(retry_on) as exc:
            last_exc = exc
            if attempt == retries - 1:
                raise
            delay = min(max_delay, base_delay * (2**attempt))
            jitter = random.uniform(0, delay * 0.1)
            time.sleep(delay + jitter)
    raise last_exc or RuntimeError("Retry failed without exception.")  # pragma: no cover
