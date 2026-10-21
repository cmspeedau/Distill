"""Fetch web pages with timeouts, a size cap, redirect re-validation, and robots.txt checks."""

import threading
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from app.config import get_settings
from app.services.url_guard import resolve_and_pin, validate_url

# Fixed for now. Will be replaced by an admin-configurable setting later.
MAX_REDIRECTS = 5
ROBOTS_CACHE_TTL = 3600  # seconds (1 hour)
_RETRY_STATUS_CODES = frozenset({429, 502, 503, 504})
_MAX_ATTEMPTS = 3
_RETRY_BACKOFF = 0.5


def _get_with_retries(client: httpx.Client, url: str) -> httpx.Response:
    """GET a page or redirect hop, retrying transient failures."""
    for attempt in range(_MAX_ATTEMPTS):
        try:
            response = client.get(url)
        except (httpx.TimeoutException, httpx.TransportError):
            if attempt == _MAX_ATTEMPTS - 1:
                raise
            time.sleep(_RETRY_BACKOFF * (2**attempt))
            continue

        if response.status_code not in _RETRY_STATUS_CODES:
            return response
        if attempt == _MAX_ATTEMPTS - 1:
            return response

        retry_after = response.headers.get("retry-after")
        try:
            delay = float(retry_after) if retry_after is not None else _RETRY_BACKOFF * (2**attempt)
        except ValueError:
            delay = _RETRY_BACKOFF * (2**attempt)
        time.sleep(delay)

    raise AssertionError("unreachable")


class FetchError(Exception):
    """Raised when a page cannot be fetched."""


class BlockedByRobots(FetchError):
    """Raised when robots.txt disallows fetching a URL."""


@dataclass(frozen=True)
class FetchResult:
    url: str
    final_url: str
    status_code: int
    content_type: str
    body: bytes


class PinnedTransport(httpx.BaseTransport):
    """Wrapper transport that closes the DNS-rebinding window.

    URL validation and the HTTP client's own DNS lookup are two separate
    resolutions, and a hostile TTL-0 zone can answer them differently: public
    IP first, loopback second. This transport re-resolves at connection time,
    validates the answer, and rewrites the request to dial the validated IP
    directly. The original hostname is kept in the ``Host`` header (httpx sets
    it before the rewrite) and in the TLS SNI/verification name through
    httpcore's ``sni_hostname`` request extension.
    """

    def __init__(self, inner: httpx.BaseTransport | None = None) -> None:
        self._inner = inner if inner is not None else httpx.HTTPTransport()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        target = resolve_and_pin(str(request.url))
        pinned_host = f"[{target.ip}]" if ":" in target.ip else target.ip
        if request.url.host != pinned_host:
            # Dial the validated address directly (IPv6 hosts need brackets).
            request.url = request.url.copy_with(host=pinned_host)
        request.extensions["sni_hostname"] = target.host
        return self._inner.handle_request(request)

    def close(self) -> None:
        self._inner.close()


def _ensure_pinned(client: httpx.Client) -> None:
    """Force every request the client sends through a PinnedTransport.

    httpx exposes no public accessor for a client's transport; patching the
    private attribute is the only way to guarantee caller-supplied clients are
    pinned too, so the SSRF check cannot be bypassed by passing a custom client.
    """
    transport = client._transport  # noqa: SLF001 - no public accessor in httpx
    if not isinstance(transport, PinnedTransport):
        client._transport = PinnedTransport(inner=transport)  # noqa: SLF001


@dataclass
class _RobotsEntry:
    parser: RobotFileParser | None  # None means allow all
    deny_all: bool
    expires_at: float


_robots_cache: dict[str, _RobotsEntry] = {}
_robots_lock = threading.Lock()


def _origin(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def _load_robots(origin: str, client: httpx.Client) -> _RobotsEntry:
    """Fetch and parse robots.txt for an origin.

    4xx -> allow all. 5xx or network error -> deny all (fail closed).
    """
    try:
        response = client.get(f"{origin}/robots.txt")
    except httpx.HTTPError:
        return _RobotsEntry(None, True, time.monotonic() + ROBOTS_CACHE_TTL)

    expires = time.monotonic() + ROBOTS_CACHE_TTL
    if 400 <= response.status_code < 500:
        return _RobotsEntry(None, False, expires)
    if response.status_code >= 500:
        return _RobotsEntry(None, True, expires)

    parser = RobotFileParser()
    parser.parse(response.text.splitlines())
    return _RobotsEntry(parser, False, expires)


def check_robots(url: str, client: httpx.Client) -> bool:
    """Return True if robots.txt allows fetching this URL."""
    origin = _origin(url)
    now = time.monotonic()
    with _robots_lock:
        entry = _robots_cache.get(origin)
        if entry is None or entry.expires_at <= now:
            entry = _load_robots(origin, client)
            _robots_cache[origin] = entry

    if entry.deny_all:
        return False
    if entry.parser is None:
        return True
    user_agent = get_settings().user_agent
    return entry.parser.can_fetch(user_agent, url)


def fetch(url: str, client: httpx.Client | None = None) -> FetchResult:
    """Fetch a URL, validating every hop including redirects."""
    settings = get_settings()
    owns_client = client is None
    client = client or httpx.Client(
        timeout=settings.timeout,
        follow_redirects=False,
        headers={"User-Agent": settings.user_agent},
    )
    _ensure_pinned(client)
    try:
        current = validate_url(url)
        if settings.respect_robots and not check_robots(current, client):
            raise BlockedByRobots(f"disallowed by robots.txt: {current}")

        for _ in range(MAX_REDIRECTS + 1):
            response = _get_with_retries(client, current)
            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    raise FetchError("redirect without Location header")
                current = validate_url(urljoin(current, location))
                if settings.respect_robots and not check_robots(current, client):
                    raise BlockedByRobots(f"disallowed by robots.txt: {current}")
                continue

            body = response.read() if not response.is_closed else response.content
            if len(body) > settings.max_response_bytes:
                raise FetchError("response exceeds max_response_bytes")

            return FetchResult(
                url=url,
                final_url=current,
                status_code=response.status_code,
                content_type=response.headers.get("content-type", ""),
                body=body,
            )

        raise FetchError(f"too many redirects (limit {MAX_REDIRECTS})")
    except httpx.HTTPError as exc:
        raise FetchError(str(exc)) from exc
    finally:
        if owns_client:
            client.close()
