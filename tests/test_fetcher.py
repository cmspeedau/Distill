import httpx
import pytest

from app.services import url_guard
from app.services.fetcher import FetchError, fetch


@pytest.fixture(autouse=True)
def no_real_dns(monkeypatch):
    monkeypatch.setattr(url_guard, "resolve_host", lambda host: ["93.184.216.34"])


def make_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False)


def test_fetches_page():
    def handler(request):
        return httpx.Response(200, text="<html>hi</html>", headers={"content-type": "text/html"})

    result = fetch("https://example.com/", client=make_client(handler))
    assert result.status_code == 200
    assert result.body == b"<html>hi</html>"
    assert result.content_type == "text/html"


def test_follows_safe_redirect():
    def handler(request):
        if request.url.path == "/start":
            return httpx.Response(301, headers={"location": "/end"})
        return httpx.Response(200, text="done")

    result = fetch("https://example.com/start", client=make_client(handler))
    assert result.final_url == "https://example.com/end"


def test_blocks_redirect_to_private_address(monkeypatch):
    def handler(request):
        return httpx.Response(302, headers={"location": "http://127.0.0.1/admin"})

    with pytest.raises(url_guard.UnsafeURLError):
        fetch("https://example.com/", client=make_client(handler))


def test_redirect_limit_enforced():
    def handler(request):
        return httpx.Response(302, headers={"location": "/loop"})

    with pytest.raises(FetchError, match="too many redirects"):
        fetch("https://example.com/loop", client=make_client(handler))


def test_rejects_oversized_response(monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "max_response_bytes", 10)

    def handler(request):
        return httpx.Response(200, content=b"x" * 100)

    with pytest.raises(FetchError, match="max_response_bytes"):
        fetch("https://example.com/", client=make_client(handler))
