import httpx
import pytest

from app.config import get_settings
from app.services import fetcher, url_guard
from app.services.fetcher import BlockedByRobots, FetchError, fetch


@pytest.fixture(autouse=True)
def no_real_dns(monkeypatch):
    monkeypatch.setattr(url_guard, "resolve_host", lambda host: ["93.184.216.34"])


@pytest.fixture(autouse=True)
def clear_robots_cache():
    fetcher._robots_cache.clear()
    yield
    fetcher._robots_cache.clear()


def make_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False)


def page_handler(robots_status=404, robots_body="", page_status=200):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(robots_status, text=robots_body)
        if request.url.path == "/start":
            return httpx.Response(301, headers={"location": "/end"})
        return httpx.Response(
            page_status,
            text="<html>hi</html>",
            headers={"content-type": "text/html"},
        )

    return handler


def test_fetches_page():
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, text="<html>hi</html>", headers={"content-type": "text/html"})

    result = fetch("https://example.com/", client=make_client(handler))
    assert result.status_code == 200
    assert result.body == b"<html>hi</html>"
    assert result.content_type == "text/html"


def test_follows_safe_redirect():
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        if request.url.path == "/start":
            return httpx.Response(301, headers={"location": "/end"})
        return httpx.Response(200, text="done")

    result = fetch("https://example.com/start", client=make_client(handler))
    assert result.final_url == "https://example.com/end"


def test_blocks_redirect_to_private_address(monkeypatch):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(302, headers={"location": "http://127.0.0.1/admin"})

    with pytest.raises(url_guard.UnsafeURLError):
        fetch("https://example.com/", client=make_client(handler))


def test_redirect_limit_enforced():
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(302, headers={"location": "/loop"})

    with pytest.raises(FetchError, match="too many redirects"):
        fetch("https://example.com/loop", client=make_client(handler))


def test_rejects_oversized_response(monkeypatch):
    monkeypatch.setattr(get_settings(), "max_response_bytes", 10)

    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, content=b"x" * 100)

    with pytest.raises(FetchError, match="max_response_bytes"):
        fetch("https://example.com/", client=make_client(handler))


def test_robots_disallow_blocks_fetch(monkeypatch):
    monkeypatch.setattr(get_settings(), "respect_robots", True)
    handler = page_handler(robots_status=200, robots_body="User-agent: *\nDisallow: /")

    with pytest.raises(BlockedByRobots):
        fetch("https://example.com/", client=make_client(handler))


def test_robots_allow_permits_fetch(monkeypatch):
    monkeypatch.setattr(get_settings(), "respect_robots", True)
    handler = page_handler(robots_status=200, robots_body="User-agent: *\nDisallow: /private")

    result = fetch("https://example.com/", client=make_client(handler))
    assert result.status_code == 200


def test_robots_404_allows_all(monkeypatch):
    monkeypatch.setattr(get_settings(), "respect_robots", True)
    handler = page_handler(robots_status=404)

    result = fetch("https://example.com/", client=make_client(handler))
    assert result.status_code == 200


def test_robots_5xx_fails_closed(monkeypatch):
    monkeypatch.setattr(get_settings(), "respect_robots", True)
    handler = page_handler(robots_status=503)

    with pytest.raises(BlockedByRobots):
        fetch("https://example.com/", client=make_client(handler))


def test_robots_redirect_target_checked(monkeypatch):
    monkeypatch.setattr(get_settings(), "respect_robots", True)

    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /end")
        if request.url.path == "/start":
            return httpx.Response(301, headers={"location": "/end"})
        return httpx.Response(200, text="done")

    with pytest.raises(BlockedByRobots):
        fetch("https://example.com/start", client=make_client(handler))


def test_robots_cached_per_origin(monkeypatch):
    monkeypatch.setattr(get_settings(), "respect_robots", True)
    robots_calls = 0

    def handler(request):
        nonlocal robots_calls
        if request.url.path == "/robots.txt":
            robots_calls += 1
            return httpx.Response(404)
        return httpx.Response(200, text="ok")

    client = make_client(handler)
    fetch("https://example.com/a", client=client)
    fetch("https://example.com/b", client=client)
    assert robots_calls == 1


def test_dns_rebinding_blocked(monkeypatch):
    # First lookup (validation) returns a public IP; any later lookup returns loopback.
    answers = iter([["93.184.216.34"]])

    def rebinding_resolve(host):
        try:
            return next(answers)
        except StopIteration:
            return ["127.0.0.1"]

    monkeypatch.setattr(url_guard, "resolve_host", rebinding_resolve)
    requested_hosts: list[str] = []

    def handler(request):
        requested_hosts.append(request.url.host)
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, text="secret")

    with pytest.raises(url_guard.UnsafeURLError):
        fetch("https://rebind.example/", client=make_client(handler))
    assert "127.0.0.1" not in requested_hosts


def test_dns_rebinding_on_redirect_blocked(monkeypatch):
    # The first hop keeps resolving public; the redirect target answers the
    # validation lookup with a public IP, then rebinds to loopback at
    # connection time — only a connect-time re-check of every hop catches this.
    rebind_answers = iter([["93.184.216.34"]])

    def resolve(host):
        if host == "rebind.example":
            try:
                return next(rebind_answers)
            except StopIteration:
                return ["127.0.0.1"]
        return ["93.184.216.34"]

    monkeypatch.setattr(url_guard, "resolve_host", resolve)
    served_paths: list[str] = []

    def handler(request):
        served_paths.append(request.url.path)
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        if request.url.path == "/start":
            return httpx.Response(302, headers={"location": "https://rebind.example/admin"})
        return httpx.Response(200, text="secret")

    with pytest.raises(url_guard.UnsafeURLError):
        fetch("https://first.example/start", client=make_client(handler))
    assert "/admin" not in served_paths
