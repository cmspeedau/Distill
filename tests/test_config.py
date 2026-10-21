from app.config import Settings


def test_defaults_are_safe() -> None:
    s = Settings()
    assert s.respect_robots is True
    assert s.timeout > 0
    assert s.max_response_bytes > 0


def test_env_prefix_is_applied(monkeypatch: object) -> None:
    import os

    os.environ["DISTILL_TIMEOUT"] = "7"
    try:
        assert Settings().timeout == 7.0
    finally:
        del os.environ["DISTILL_TIMEOUT"]
