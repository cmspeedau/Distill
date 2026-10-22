import httpx
import pytest
from httpx import ASGITransport

from app.main import app
from app.services import fetcher, url_guard


@pytest.fixture(autouse=True)
def mock_outbound_network(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(url_guard, "resolve_host", lambda host: ["93.184.216.34"])
    monkeypatch.setattr(fetcher, "_ensure_pinned", lambda client: None)
    monkeypatch.setattr(fetcher.get_settings(), "respect_robots", False)
    fetcher._robots_cache.clear()
    yield
    fetcher._robots_cache.clear()


@pytest.fixture
def outbound_mock(monkeypatch: pytest.MonkeyPatch):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            text=(
                "<html lang='en'><head><title>API article</title></head><body><article>"
                "<h1>API article</h1>"
                "<p>Enough text for this API test to exercise the extractor.</p>"
                "</article></body></html>"
            ),
            headers={"content-type": "text/html; charset=utf-8"},
        )
    )
    client = httpx.Client(transport=transport, follow_redirects=False)
    monkeypatch.setattr(fetcher.httpx, "Client", lambda **kwargs: client)
    yield
    client.close()


@pytest.fixture
async def api_client():
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


async def test_health(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_scrape_returns_extracted_page(
    api_client: httpx.AsyncClient, outbound_mock: None
) -> None:
    response = await api_client.post("/scrape", json={"url": "https://example.com/article"})

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "API article"
    assert data["final_url"] == "https://example.com/article"
    assert "# API article" in data["markdown"]
    assert len(data["content_hash"]) == 64


@pytest.mark.parametrize(
    "payload",
    [
        {"url": "file:///etc/passwd"},
        {"url": "not a url"},
        {"url": "https://example.com", "extra": True},
    ],
)
async def test_scrape_rejects_invalid_request(
    api_client: httpx.AsyncClient, payload: dict[str, object]
) -> None:
    response = await api_client.post("/scrape", json=payload)

    assert response.status_code == 422
    assert response.json() == {"error": "ValidationError", "detail": "Invalid request"}


async def test_scrape_maps_private_url_error(api_client: httpx.AsyncClient) -> None:
    response = await api_client.post("/scrape", json={"url": "http://127.0.0.1/"})

    assert response.status_code == 400
    assert response.json() == {"error": "UnsafeURLError", "detail": "URL is not allowed"}


async def test_scrape_maps_upstream_failure(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(fetcher, "_ensure_pinned", lambda client: None)
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(503)),
        follow_redirects=False,
    )
    monkeypatch.setattr(fetcher.httpx, "Client", lambda **kwargs: client)
    response = await api_client.post("/scrape", json={"url": "https://example.com/"})

    assert response.status_code == 502
    assert response.json()["error"] == "FetchError"
