"""Command-line interface for Distill."""

import argparse
import json
import sys
from collections.abc import Sequence

from app.services.fetcher import FetchError
from app.services.scrape import ScrapeResult, scrape
from app.services.url_guard import UnsafeURLError


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli", description="Scrape web pages with Distill."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    scrape_parser = commands.add_parser("scrape", help="scrape one URL")
    scrape_parser.add_argument("url", help="HTTP(S) URL to scrape")
    scrape_parser.add_argument(
        "--include-images",
        action="store_true",
        help="include images in the extracted content",
    )
    scrape_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="write metadata and content as JSON instead of Markdown",
    )
    return parser


def _print_json(result: ScrapeResult) -> None:
    output = {
        "url": result.fetched.url,
        "final_url": result.fetched.final_url,
        "status_code": result.fetched.status_code,
        "content_type": result.fetched.content_type,
        "title": result.extracted.title,
        "description": result.extracted.description,
        "language": result.extracted.language,
        "canonical_url": result.extracted.canonical_url,
        "links": result.extracted.links,
        "markdown": result.extracted.markdown,
        "cleaned_html": result.extracted.cleaned_html,
        "content_hash": result.extracted.content_hash,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        result = scrape(args.url, include_images=args.include_images)
    except (FetchError, UnsafeURLError) as exc:
        print(f"distill: {exc}", file=sys.stderr)
        return 1

    if args.json_output:
        _print_json(result)
    else:
        print(result.extracted.markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
