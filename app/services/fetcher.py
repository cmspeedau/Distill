"""Fetch web pages with timeouts, a size cap, and redirect re-validation."""

from dataclasses import dataclass
from urllib.parse import urljoin

import httpx

from app.config import get_settings
from app.services.url_guard import validate_url

# Fixed for now. Will be replaced by an admin-configurable setting later.
MAX_REDIRECTS = 5


class FetchError(Exception):
    """Raised when a page cannot be fetched."""


@dataclass(frozen=True)
class FetchResult:
    url: str
    final_url: str
    status_code: int
    content_type: str
    body: bytes


def check_robots(url: str) -> bool:
    """Stub: robots.txt support is planned. Always allows for now."""
    return True


def fetch(url: str, client: httpx.Client | None = None) -> FetchResult:
    """Fetch a URL, validating every hop including redirects."""
    settings = get_settings()
    owns_client = client is None
    client = client or httpx.Client(
        timeout=settings.timeout,
        follow_redirects=False,
        headers={"User-Agent": settings.user_agent},
    )
    try:
        current = validate_url(url)
        if settings.respect_robots and not check_robots(current):
            raise FetchError(f"disallowed by robots.txt: {current}")

        for _ in range(MAX_REDIRECTS + 1):
            response = client.get(current)
            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    raise FetchError("redirect without Location header")
                current = validate_url(urljoin(current, location))
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
