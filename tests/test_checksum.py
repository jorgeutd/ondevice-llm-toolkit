from __future__ import annotations

from pathlib import Path

from odlt.utils import sha256_file


def test_sha256_file(tmp_path: Path) -> None:
    file_path = tmp_path / "data.txt"
    file_path.write_text("hello", encoding="utf-8")
    digest = sha256_file(file_path)
    assert digest == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
