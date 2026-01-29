from __future__ import annotations

from pathlib import Path

from odlt.config import load_config


def test_load_config_creates_defaults(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ODLT_HOME", str(tmp_path))
    cfg = load_config()
    assert (tmp_path / "config.yaml").exists()
    assert cfg.paths.models_dir.exists()
    assert cfg.model.model_id
