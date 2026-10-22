"""Pydantic schemas for the scrape API."""

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ScrapeRequest(BaseModel):
    """Input for scraping one HTTP(S) URL."""

    model_config = ConfigDict(extra="forbid")

    url: HttpUrl = Field(description="Public HTTP(S) URL to fetch and extract")
    include_images: bool = Field(
        default=False, description="Include images found in the extracted page"
    )


class ScrapeResponse(BaseModel):
    """Extracted page content and fetch metadata."""

    url: str
    final_url: str
    status_code: int
    content_type: str
    title: str | None
    description: str | None
    language: str | None
    canonical_url: str | None
    links: list[str]
    markdown: str
    cleaned_html: str
    content_hash: str


class ErrorResponse(BaseModel):
    """Stable API error shape."""

    error: str
    detail: str
