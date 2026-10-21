<div align="center">

# Distill

**Messy web in, clean Markdown out.**

Self-hosted web scraper with a dashboard, a REST API, and an MCP server for AI tools.

[![CI](https://img.shields.io/github/actions/workflow/status/YOUR_USER/distill/ci.yml?branch=main&label=CI&logo=github)](https://github.com/YOUR_USER/distill/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](docker-compose.yml)
[![MCP](https://img.shields.io/badge/MCP-compatible-8A2BE2)](https://modelcontextprotocol.io/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-261230?logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

## Why Distill?

Hosted scraping APIs are convenient, but your data and your bill live on someone
else's servers. Distill gives you the same workflow on your own machine:
paste a URL, get clean Markdown, and keep a searchable ledger of everything
you've scraped.

## Features

- **Clean Markdown output**: main-content extraction strips nav, ads, and footers
- **Metadata and links**: title, description, language, canonical URL, OpenGraph
- **Ledger of every scrape**: status, timing, content hash, and stored output
- **Metrics dashboard**: success rate, latency, volume, and Prometheus endpoint
- **REST API**: documented with OpenAPI at `/docs`
- **MCP server**: let Claude and other AI tools scrape through Distill
- **Safe by default**: SSRF protection, robots.txt support, size and redirect limits
- **Flexible storage**: SQLite or PostgreSQL, local disk or S3-compatible
- **CLI**: `distill scrape <url>` straight from your terminal

## Quick start

### Docker (recommended)

```bash
git clone https://github.com/YOUR_USER/distill.git
cd distill
cp .env.example .env
docker compose up
```

Open the UI at <http://localhost:5173> and the API docs at <http://localhost:8000/docs>.

### Local development

```bash
uv sync
uv run uvicorn distill.api.main:app --reload     # API
cd web && npm install && npm run dev             # UI
```

## Usage

### CLI

```bash
distill scrape https://example.com
distill scrape https://example.com --json
distill scrape https://example.com --html --timeout 20
```

### REST API

```bash
curl -X POST http://localhost:8000/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

| Endpoint | Description |
|---|---|
| `POST /v1/scrape` | Scrape a URL and return the result |
| `GET /v1/scrapes` | List the ledger (pagination, filters) |
| `GET /v1/scrapes/{id}` | Scrape metadata |
| `GET /v1/scrapes/{id}/markdown` | Stored Markdown |
| `GET /v1/scrapes/{id}/html` | Stored cleaned HTML |
| `DELETE /v1/scrapes/{id}` | Remove a scrape |
| `GET /healthz` | Health check |
| `GET /metrics` | Prometheus metrics |

### MCP (AI tools)

Add Distill to your MCP client config:

```json
{
  "mcpServers": {
    "distill": {
      "command": "uv",
      "args": ["run", "python", "-m", "distill.mcp"],
      "env": { "DISTILL_API_URL": "http://localhost:8000" }
    }
  }
}
```

> MCP support lands in a later phase. See the [roadmap](ROADMAP.md).

## Configuration

All settings use the `DISTILL_` prefix. See [`.env.example`](.env.example) for the full list.

| Variable | Default | Description |
|---|---|---|
| `DISTILL_DATABASE_URL` | `sqlite:///distill.db` | SQLite or PostgreSQL URL |
| `DISTILL_STORAGE_DIR` | `./data` | Where Markdown and HTML are stored |
| `DISTILL_TIMEOUT` | `15` | Request timeout in seconds |
| `DISTILL_MAX_RESPONSE_BYTES` | `10485760` | Abort bodies larger than this |
| `DISTILL_RESPECT_ROBOTS` | `true` | Honor robots.txt |
| `DISTILL_USER_AGENT` | `Distill/1.0` | User agent sent with requests |

## Architecture

```
 URL ──► SSRF check ──► robots.txt ──► Fetcher ──► Extractor ──► Markdown
                                                       │
                                  ┌────────────────────┼───────────────────┐
                                  ▼                    ▼                   ▼
                              Storage              Ledger (DB)         Metrics
                         (disk / S3)          (SQLite / Postgres)    (Prometheus)
                                  └────────────────────┬───────────────────┘
                                                       ▼
                                       REST API · React UI · CLI · MCP
```

Business logic lives in `distill/services/`. The API, CLI, and MCP server are
thin wrappers around it.

## Roadmap

| Phase | Focus | Status |
|---|---|---|
| 1 | Core scraper, SSRF protection, robots.txt, CLI | Planned |
| 2 | REST API, database ledger, React UI | Planned |
| 3 | MCP server, API keys | Planned |
| 4 | Crawling, depth and rate limits | Planned |
| 5 | Metrics dashboard, Grafana | Planned |

Full details in [ROADMAP.md](ROADMAP.md).

## Responsible use

Distill respects robots.txt by default and blocks requests to private networks.
You are responsible for following each site's terms of service and applicable laws.

## Contributing

Contributions are welcome. Please read [AGENTS.md](AGENTS.md) for project
conventions, then:

```bash
uv run pytest
uv run ruff check . && uv run mypy .
```

## License

[MIT](LICENSE)
