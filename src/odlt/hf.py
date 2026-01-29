"""Hugging Face Hub interactions."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.utils import HfHubHTTPError

from odlt.errors import DownloadError, ValidationError
from odlt.utils import retry


def verify_repo_file(
    *,
    repo_id: str,
    filename: str,
    revision: Optional[str] = None,
    token: Optional[str] = None,
) -> None:
    """Ensure the file exists in a Hugging Face repository.

    Args:
        repo_id: Hugging Face repo id.
        filename: File name to validate.
        revision: Optional revision.
        token: Optional HF token.

    Raises:
        ValidationError: If the file is not found.
    """
    api = HfApi(token=token)

    def _list_files() -> list[str]:
        return api.list_repo_files(repo_id=repo_id, revision=revision)

    try:
        files = retry(_list_files, retries=3, base_delay=1.0, max_delay=8.0)
    except HfHubHTTPError as exc:
        raise ValidationError(f"Failed to list repo files: {exc}") from exc

    if filename not in files:
        raise ValidationError(f"File not found in repo: {filename}")


async def download_model(
    *,
    repo_id: str,
    filename: str,
    revision: Optional[str],
    local_dir: Path,
    cache_dir: Path,
    token: Optional[str],
    force_download: bool = False,
) -> Path:
    """Download a file from the Hugging Face Hub.

    Args:
        repo_id: Hugging Face repo id.
        filename: File name to download.
        revision: Optional revision.
        local_dir: Directory to place the file.
        cache_dir: Hugging Face cache directory.
        token: Optional HF token.
        force_download: Whether to force re-download.

    Returns:
        Path to the downloaded file.

    Raises:
        DownloadError: If download fails.
    """
    local_dir.mkdir(parents=True, exist_ok=True)

    def _download() -> str:
        return hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            revision=revision,
            local_dir=str(local_dir),
            cache_dir=str(cache_dir),
            token=token,
            force_download=force_download,
        )

    try:
        path = await asyncio.to_thread(
            retry, _download, retries=3, base_delay=1.0, max_delay=10.0
        )
    except Exception as exc:
        raise DownloadError(f"Download failed: {exc}") from exc
    return Path(path)
