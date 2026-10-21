"""Shared pytest fixtures. Tests must never touch the real network."""

import pytest

from app.config import Settings


@pytest.fixture
def settings(tmp_path: pytest.TempPathFactory) -> Settings:
    return Settings(
        database_url="sqlite:///:memory:",
        storage_dir=str(tmp_path),  # type: ignore[arg-type]
    )
