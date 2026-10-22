"""FastAPI application assembly."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.scrape import router as scrape_router
from app.schemas.scrape import ErrorResponse
from app.services.fetcher import BlockedByRobots, FetchError
from app.services.url_guard import UnsafeURLError

app = FastAPI(title="Distill", version="0.1.0")
app.include_router(scrape_router)
app.include_router(health_router)


@app.exception_handler(BlockedByRobots)
async def robots_error_handler(request: Request, exc: BlockedByRobots) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content=ErrorResponse(
            error="BlockedByRobots", detail="URL is disallowed by robots.txt"
        ).model_dump(),
    )


@app.exception_handler(UnsafeURLError)
async def unsafe_url_error_handler(request: Request, exc: UnsafeURLError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(error="UnsafeURLError", detail="URL is not allowed").model_dump(),
    )


@app.exception_handler(FetchError)
async def fetch_error_handler(request: Request, exc: FetchError) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content=ErrorResponse(error="FetchError", detail=str(exc)).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(error="ValidationError", detail="Invalid request").model_dump(),
    )
