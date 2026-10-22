"""End-to-end scrape service shared by CLI, API, MCP, and workers."""

from dataclasses import dataclass
from email.message import Message

from app.services.extractor import ExtractResult, extract
from app.services.fetcher import FetchError, FetchResult, fetch


@dataclass(frozen=True)
class ScrapeResult:
    """Fetch and extraction results for one successfully scraped page."""

    fetched: FetchResult
    extracted: ExtractResult


def scrape(url: str, *, include_images: bool = False) -> ScrapeResult:
    """Fetch a URL and extract its content, raising FetchError on HTTP failure."""
    fetched = fetch(url)
    if not 200 <= fetched.status_code < 300:
        raise FetchError(f"server returned HTTP {fetched.status_code}")

    message = Message()
    message["content-type"] = fetched.content_type
    charset = message.get_content_charset() or "utf-8"
    try:
        html = fetched.body.decode(charset, errors="replace")
    except LookupError as exc:
        raise FetchError(f"unsupported response charset: {charset}") from exc

    return ScrapeResult(
        fetched=fetched,
        extracted=extract(html, fetched.final_url, include_images=include_images),
    )
