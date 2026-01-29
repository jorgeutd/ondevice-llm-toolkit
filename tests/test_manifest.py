from __future__ import annotations

from pathlib import Path

from odlt.gguf import create_manifest


def test_create_manifest(tmp_path: Path) -> None:
    file_path = tmp_path / "model.gguf"
    file_path.write_bytes(b"sample-data")
    manifest = create_manifest(model_id="test/model", file_path=file_path, license_name="MIT")
    assert manifest.model_id == "test/model"
    assert manifest.file == "model.gguf"
    assert manifest.license == "MIT"
