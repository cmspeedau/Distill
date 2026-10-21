"""Shared pytest fixtures. Tests must never touch the real network."""

from pathlib import Path

import pytest

from app.config import Settings


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url="sqlite:///:memory:",
        storage_dir=str(tmp_path),
    )
