"""Extract useful page content, metadata, and links from fetched HTML."""

import hashlib
import re
from dataclasses import dataclass
from urllib.parse import urljoin

import trafilatura
from markdownify import markdownify
from selectolax.lexbor import LexborHTMLParser


@dataclass(frozen=True)
class ExtractResult:
    """Normalized content and metadata extracted from an HTML page."""

    title: str | None
    description: str | None
    language: str | None
    canonical_url: str | None
    links: tuple[str, ...]
    markdown: str
    cleaned_html: str
    content_hash: str


def extract(html: str, url: str, *, include_images: bool = False) -> ExtractResult:
    """Extract main content and metadata, returning Markdown and cleaned HTML.

    Trafilatura provides the primary article extraction. If it cannot identify
    article-like content (common on short pages), convert the document body
    after removing obvious non-content elements instead of discarding the page.
    """
    metadata = trafilatura.extract_metadata(html, default_url=url)
    extracted_html = trafilatura.extract(
        html,
        url=url,
        output_format="html",
        include_links=True,
        include_images=include_images,
        include_tables=True,
        include_comments=False,
        with_metadata=False,
    )

    extracted_parser = LexborHTMLParser(extracted_html) if extracted_html is not None else None
    extracted_text = extracted_parser.text(strip=True) if extracted_parser is not None else ""
    if extracted_parser is not None and len(extracted_text) >= 200:
        content = (
            extracted_parser.body.inner_html or ""
            if extracted_parser.body is not None
            else extracted_html or ""
        )
        content = _remove_non_content(content)
    else:
        content = _fallback_body(html, url)

    content_parser = LexborHTMLParser(content)
    links = _extract_links(content_parser, url)
    cleaned_html = (
        content_parser.body.inner_html or "" if content_parser.body is not None else content
    )
    markdown = _normalize_markdown(markdownify(cleaned_html, heading_style="ATX", bullets="-"))

    return ExtractResult(
        title=_optional_text(metadata.title),
        description=_optional_text(metadata.description),
        language=_document_language(html),
        canonical_url=_canonical_url(html, url),
        links=links,
        markdown=markdown,
        cleaned_html=cleaned_html.strip(),
        content_hash=hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
    )


def _fallback_body(html: str, url: str) -> str:
    """Return a conservative body fallback when article extraction finds none."""
    parser = LexborHTMLParser(html)
    body = parser.body
    if body is None:
        return ""

    cleaned_body = _remove_non_content(body.inner_html or "")
    body_parser = LexborHTMLParser(cleaned_body)
    for node in body_parser.css("a[href], img[src]"):
        attribute = "href" if node.tag == "a" else "src"
        value = node.attributes.get(attribute)
        if value:
            node.attrs[attribute] = urljoin(url, value)
    return body_parser.body.inner_html or "" if body_parser.body is not None else cleaned_body


def _remove_non_content(html: str) -> str:
    parser = LexborHTMLParser(html)
    for node in parser.css(
        "script, style, noscript, iframe, svg, nav, header, footer, aside, form"
    ):
        node.decompose()
    body = parser.body
    return body.inner_html if body is not None and body.inner_html is not None else html


def _extract_links(parser: LexborHTMLParser, page_url: str) -> tuple[str, ...]:
    links: list[str] = []
    seen: set[str] = set()
    for node in parser.css("a[href]"):
        href = (node.attributes.get("href") or "").strip()
        if not href:
            continue
        absolute_url = urljoin(page_url, href)
        if absolute_url not in seen:
            seen.add(absolute_url)
            links.append(absolute_url)
    return tuple(links)


def _canonical_url(html: str, page_url: str) -> str | None:
    parser = LexborHTMLParser(html)
    for node in parser.css("link[rel][href]"):
        rel_tokens = (node.attributes.get("rel") or "").lower().split()
        href = (node.attributes.get("href") or "").strip()
        if "canonical" in rel_tokens and href:
            return str(urljoin(page_url, href))
    return None


def _document_language(html: str) -> str | None:
    parser = LexborHTMLParser(html)
    language = parser.css_first("html")
    if language is None:
        return None
    return _optional_text(language.attributes.get("lang"))


def _optional_text(value: str | None) -> str | None:
    return value.strip() or None if value is not None else None


def _normalize_markdown(markdown: str) -> str:
    markdown = markdown.replace("\r\n", "\n").replace("\r", "\n")
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    return markdown.strip()
