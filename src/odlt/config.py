"""Configuration loading and validation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from odlt.constants import (
    DEFAULT_LLAMA_COMMIT,
    DEFAULT_MODEL_FILE,
    DEFAULT_MODEL_ID,
    DEFAULT_MODEL_LICENSE,
)
from odlt.errors import ConfigError


class ModelConfig(BaseModel):
    """Model settings."""

    model_config = ConfigDict(extra="forbid")

    model_id: str = Field(..., min_length=1)
    file: str = Field(..., min_length=1)
    revision: str | None = None
    license: str = Field(..., min_length=1)


class PathsConfig(BaseModel):
    """Filesystem layout."""

    model_config = ConfigDict(extra="forbid")

    base_dir: Path
    cache_dir: Path
    models_dir: Path
    runs_dir: Path
    reports_dir: Path
    llama_cpp_dir: Path
    llama_cpp_build_dir: Path
    native_bin_dir: Path


class LlamaConfig(BaseModel):
    """llama.cpp settings."""

    model_config = ConfigDict(extra="forbid")

    commit: str = Field(..., min_length=7)
    cmake_args: list[str] = Field(default_factory=list)


class AppConfig(BaseModel):
    """Root configuration schema."""

    model_config = ConfigDict(extra="forbid")

    model: ModelConfig
    paths: PathsConfig
    llama: LlamaConfig


def _base_dir() -> Path:
    """Get base directory for config and artifacts."""
    home_override = os.environ.get("ODLT_HOME")
    if home_override:
        return Path(home_override).expanduser().resolve()
    return Path("~/.ondevice-llm-toolkit").expanduser().resolve()


def config_path() -> Path:
    """Get configuration file path."""
    return _base_dir() / "config.yaml"


def _default_paths(base_dir: Path) -> PathsConfig:
    """Build default paths config."""
    llama_dir = base_dir / "llama.cpp"
    return PathsConfig(
        base_dir=base_dir,
        cache_dir=base_dir / "cache",
        models_dir=base_dir / "models",
        runs_dir=base_dir / "runs",
        reports_dir=base_dir / "reports",
        llama_cpp_dir=llama_dir,
        llama_cpp_build_dir=llama_dir / "build",
        native_bin_dir=base_dir / "bin",
    )


def default_config() -> AppConfig:
    """Create default configuration."""
    base_dir = _base_dir()
    return AppConfig(
        model=ModelConfig(
            model_id=DEFAULT_MODEL_ID,
            file=DEFAULT_MODEL_FILE,
            revision=None,
            license=DEFAULT_MODEL_LICENSE,
        ),
        paths=_default_paths(base_dir),
        llama=LlamaConfig(commit=DEFAULT_LLAMA_COMMIT, cmake_args=[]),
    )


def _deep_update(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    """Recursively update a nested dictionary.

    Args:
        base: Base dictionary.
        updates: Updates to merge into base.

    Returns:
        Merged dictionary.
    """
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def _resolve_paths(cfg: AppConfig) -> AppConfig:
    """Resolve and normalize paths in config."""
    base_dir = cfg.paths.base_dir.expanduser().resolve()
    cfg.paths.base_dir = base_dir
    for field in cfg.paths.model_fields:
        current = getattr(cfg.paths, field)
        if isinstance(current, Path):
            resolved = current.expanduser()
            if not resolved.is_absolute():
                resolved = base_dir / resolved
            setattr(cfg.paths, field, resolved.resolve())
    return cfg


def ensure_dirs(cfg: AppConfig) -> None:
    """Ensure all configured directories exist.

    Args:
        cfg: Application configuration.
    """
    for field in cfg.paths.model_fields:
        path = getattr(cfg.paths, field)
        if isinstance(path, Path):
            path.mkdir(parents=True, exist_ok=True)


def load_config() -> AppConfig:
    """Load configuration from disk, creating defaults if missing.

    Returns:
        Loaded configuration.

    Raises:
        ConfigError: If the configuration is invalid.
    """
    cfg_path = config_path()
    data = default_config().model_dump(mode="json")
    if cfg_path.exists():
        try:
            with cfg_path.open("r", encoding="utf-8") as handle:
                file_data = yaml.safe_load(handle) or {}
        except OSError as exc:
            raise ConfigError(f"Failed to read config: {exc}") from exc
        if not isinstance(file_data, dict):
            raise ConfigError("Config file must contain a YAML mapping.")
        data = _deep_update(data, file_data)
    try:
        cfg = AppConfig.model_validate(data)
    except Exception as exc:
        raise ConfigError(f"Invalid config: {exc}") from exc
    cfg = _resolve_paths(cfg)
    ensure_dirs(cfg)
    if not cfg_path.exists():
        save_config(cfg)
    return cfg


def save_config(cfg: AppConfig) -> None:
    """Persist configuration to disk.

    Args:
        cfg: Configuration to save.

    Raises:
        ConfigError: If the config cannot be written.
    """
    cfg_path = config_path()
    try:
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        with cfg_path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(cfg.model_dump(mode="json"), handle, sort_keys=False)
    except OSError as exc:
        raise ConfigError(f"Failed to write config: {exc}") from exc
