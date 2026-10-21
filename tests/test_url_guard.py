import pytest

from app.services import url_guard
from app.services.url_guard import UnsafeURLError, validate_url


@pytest.fixture(autouse=True)
def no_real_dns(monkeypatch):
    monkeypatch.setattr(url_guard, "resolve_host", lambda host: ["93.184.216.34"])


@pytest.mark.parametrize(
    "url", ["ftp://example.com/x", "file:///etc/passwd", "javascript:alert(1)"]
)
def test_rejects_non_http_schemes(url):
    with pytest.raises(UnsafeURLError):
        validate_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://10.0.0.5/",
        "http://192.168.1.1/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
        "http://0.0.0.0/",
    ],
)
def test_rejects_blocked_literal_addresses(url):
    with pytest.raises(UnsafeURLError):
        validate_url(url)


def test_rejects_hostname_resolving_to_private(monkeypatch):
    monkeypatch.setattr(url_guard, "resolve_host", lambda host: ["10.1.2.3"])
    with pytest.raises(UnsafeURLError):
        validate_url("https://internal.example/")


def test_accepts_public_url():
    assert validate_url("https://example.com/page") == "https://example.com/page"
