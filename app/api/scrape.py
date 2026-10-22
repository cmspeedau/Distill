"""Scrape endpoint."""

from fastapi import APIRouter

from app.schemas.scrape import ErrorResponse, ScrapeRequest, ScrapeResponse
from app.services.scrape import scrape

router = APIRouter()


@router.post(
    "/scrape",
    response_model=ScrapeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "The URL is not allowed"},
        403: {"model": ErrorResponse, "description": "Blocked by robots.txt"},
        422: {"model": ErrorResponse, "description": "Invalid request"},
        502: {"model": ErrorResponse, "description": "The upstream fetch failed"},
    },
)
def create_scrape(request: ScrapeRequest) -> ScrapeResponse:
    """Fetch and extract one URL."""
    result = scrape(str(request.url), include_images=request.include_images)
    return ScrapeResponse(
        url=result.fetched.url,
        final_url=result.fetched.final_url,
        status_code=result.fetched.status_code,
        content_type=result.fetched.content_type,
        title=result.extracted.title,
        description=result.extracted.description,
        language=result.extracted.language,
        canonical_url=result.extracted.canonical_url,
        links=list(result.extracted.links),
        markdown=result.extracted.markdown,
        cleaned_html=result.extracted.cleaned_html,
        content_hash=result.extracted.content_hash,
    )
