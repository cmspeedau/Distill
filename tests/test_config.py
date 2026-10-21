import pytest

from app.config import Settings


def test_defaults_are_safe() -> None:
    s = Settings()
    assert s.respect_robots is True
    assert s.timeout > 0
    assert s.max_response_bytes > 0


def test_env_prefix_is_applied(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISTILL_TIMEOUT", "7")
    assert Settings().timeout == 7.0
