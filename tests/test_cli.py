import json
from collections.abc import Callable, Generator
from typing import NoReturn

import httpx
import pytest

from app import cli
from app.services import fetcher, url_guard
from app.services import scrape as scrape_service
from app.services.fetcher import FetchError


@pytest.fixture(autouse=True)
def mock_network(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    monkeypatch.setattr(url_guard, "resolve_host", lambda host: ["93.184.216.34"])
    monkeypatch.setattr(fetcher, "_ensure_pinned", lambda client: None)
    monkeypatch.setattr(fetcher.get_settings(), "respect_robots", False)
    fetcher._robots_cache.clear()
    yield
    fetcher._robots_cache.clear()


def mock_client(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False)


def test_scrape_command_prints_markdown(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text=(
                "<html><body><article><h1>CLI article</h1>"
                "<p>Content for the command line should be visible in Markdown.</p>"
                "</article></body></html>"
            ),
            headers={"content-type": "text/html; charset=utf-8"},
        )

    _use_mock_fetch(monkeypatch, handler)

    assert cli.main(["scrape", "https://example.com/article"]) == 0
    output = capsys.readouterr()
    assert "# CLI article" in output.out
    assert output.err == ""


def test_scrape_command_json_option(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text="<html><body><h1>JSON article</h1><p>A short page.</p></body></html>",
            headers={"content-type": "text/html"},
        )

    _use_mock_fetch(monkeypatch, handler)

    assert cli.main(["scrape", "https://example.com/article", "--json"]) == 0
    output = capsys.readouterr()
    data = json.loads(output.out)
    assert data["final_url"] == "https://example.com/article"
    assert data["title"] == "JSON article"
    assert data["markdown"]
    assert output.err == ""


def test_scrape_command_reports_fetch_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail(url: str, *, include_images: bool = False) -> NoReturn:
        raise FetchError("server returned HTTP 500")

    monkeypatch.setattr(cli, "scrape", fail)

    assert cli.main(["scrape", "https://example.com/failed"]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "server returned HTTP 500" in output.err


def test_scrape_command_requires_url(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["scrape"])

    assert exc_info.value.code == 2


def _use_mock_fetch(
    monkeypatch: pytest.MonkeyPatch,
    handler: Callable[[httpx.Request], httpx.Response],
) -> None:
    def fetch_with_mock(url: str) -> fetcher.FetchResult:
        with mock_client(handler) as client:
            return fetcher.fetch(url, client=client)

    monkeypatch.setattr(scrape_service, "fetch", fetch_with_mock)
