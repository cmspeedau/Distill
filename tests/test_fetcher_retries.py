import httpx
import pytest
import respx

from app.config import get_settings
from app.services import fetcher, url_guard
from app.services.fetcher import BlockedByRobots, fetch


@pytest.fixture(autouse=True)
def public_dns(monkeypatch):
    monkeypatch.setattr(url_guard, "resolve_host", lambda host: ["93.184.216.34"])
    monkeypatch.setattr(get_settings(), "respect_robots", False)
    monkeypatch.setattr(fetcher, "_ensure_pinned", lambda client: None)


def test_retries_transient_503_then_succeeds(monkeypatch):
    sleeps = []
    monkeypatch.setattr(fetcher.time, "sleep", sleeps.append)
    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://example.com/").mock(
            side_effect=[httpx.Response(503), httpx.Response(200, text="ok")]
        )
        result = fetch("https://example.com/")

    assert result.status_code == 200
    assert route.call_count == 2
    assert sleeps == [0.5]


def test_gives_up_after_three_transient_attempts(monkeypatch):
    sleeps = []
    monkeypatch.setattr(fetcher.time, "sleep", sleeps.append)
    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://example.com/").mock(return_value=httpx.Response(503))
        result = fetch("https://example.com/")

    assert result.status_code == 503
    assert route.call_count == 3
    assert sleeps == [0.5, 1.0]


def test_does_not_retry_404():
    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://example.com/").mock(return_value=httpx.Response(404))
        result = fetch("https://example.com/")

    assert result.status_code == 404
    assert route.call_count == 1


def test_numeric_retry_after_is_honored(monkeypatch):
    sleeps = []
    monkeypatch.setattr(fetcher.time, "sleep", sleeps.append)
    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://example.com/").mock(
            side_effect=[
                httpx.Response(429, headers={"Retry-After": "3"}),
                httpx.Response(200, text="ok"),
            ]
        )
        result = fetch("https://example.com/")

    assert result.status_code == 200
    assert route.call_count == 2
    assert sleeps == [3.0]


@pytest.mark.parametrize(
    ("header", "expected"),
    [("999999", fetcher._MAX_RETRY_DELAY), ("-5", 0.0)],
)
def test_retry_after_is_clamped(monkeypatch, header, expected):
    sleeps = []
    monkeypatch.setattr(fetcher.time, "sleep", sleeps.append)
    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://example.com/").mock(
            side_effect=[
                httpx.Response(429, headers={"Retry-After": header}),
                httpx.Response(200, text="ok"),
            ]
        )
        result = fetch("https://example.com/")

    assert result.status_code == 200
    assert route.call_count == 2
    assert sleeps == [expected]


def test_robots_denial_is_not_retried(monkeypatch):
    monkeypatch.setattr(get_settings(), "respect_robots", True)
    fetcher._robots_cache.clear()
    with respx.mock(assert_all_called=True) as router:
        robots = router.get("https://example.com/robots.txt").mock(
            return_value=httpx.Response(200, text="User-agent: *\nDisallow: /")
        )
        with pytest.raises(BlockedByRobots):
            fetch("https://example.com/")

    assert robots.call_count == 1
