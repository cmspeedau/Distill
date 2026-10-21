<div align="center">

# Distill

**Messy web in, clean Markdown out.**

Self-hosted web scraper with a dashboard, a REST API, and an MCP server for AI tools.

[![CI](https://img.shields.io/github/actions/workflow/status/cmspeedau/Distill/ci.yml?branch=main&label=CI&logo=github)](https://github.com/cmspeedau/Distill/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![MCP](https://img.shields.io/badge/MCP-compatible-8A2BE2)](https://modelcontextprotocol.io/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-261230?logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

> **Status:** early development. The roadmap is written; code lands phase by phase. Everything below describes the target design, not what works today.

---

## Why Distill?

Hosted scraping APIs are convenient, but your data and your bill live on someone
else's servers. Distill gives you the same workflow on your own machine:
paste a URL, get clean Markdown, and keep a searchable ledger of everything
you've scraped.

## Planned features

- **Clean Markdown output**: main-content extraction strips nav, ads, and footers
- **Metadata and links**: title, description, language, canonical URL, OpenGraph
- **Ledger of every scrape**: status, timing, content hash, and stored output
- **Setup wizard**: pick SQLite or PostgreSQL and local or S3-compatible storage on first run
- **Metrics dashboard**: success rate, latency, volume, plus Prometheus and Grafana
- **REST API**: documented with OpenAPI at `/docs`
- **MCP server**: let Claude and other AI tools scrape through Distill
- **Crawl, map, and batch**: scrape whole sites with scope and politeness rules
- **Safe by default**: SSRF protection, robots.txt support, size and redirect limits
- **CLI**: `python -m app.cli scrape <url>` straight from your terminal

## Quick start

> Not runnable yet. This is the intended workflow once Phase 1 and 2 land.

```bash
git clone https://github.com/cmspeedau/Distill.git
cd Distill
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload     # API on :8000
cd frontend && npm install && npm run dev  # UI on :5173
```

## Usage (target design)

### CLI

```bash
python -m app.cli scrape https://example.com
```

### REST API

```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

| Endpoint | Description |
|---|---|
| `POST /scrape` | Scrape a URL and return the result |
| `GET /health` | Health check |
| `GET /metrics` | Prometheus metrics (Phase 6b) |

The ledger endpoints arrive with Phase 3 and 5. See [ROADMAP.md](ROADMAP.md).

## Configuration

Settings are read from environment variables and a bootstrap config file in one place (`app/config.py`). See [`.env.example`](.env.example) for the current list.

## Architecture

```
 URL --> SSRF check --> robots.txt --> Fetcher --> Extractor --> Markdown
                                                       |
                                  +--------------------+-------------------+
                                  v                    v                   v
                              Storage              Ledger (DB)         Metrics
                         (disk / S3)          (SQLite / Postgres)    (Prometheus)
                                  +--------------------+-------------------+
                                                       v
                                       REST API / React UI / CLI / MCP
```

Business logic lives in `app/services/`. The API, CLI, MCP server, and workers are
thin wrappers around it.

## Roadmap

| Milestone | Focus |
|---|---|
| 1. MVP | Core scraper, REST API and UI, persistence, ledger UI |
| 2. Make it yours | Setup wizard, storage abstraction, metrics dashboard |
| 3. Operate it | Prometheus and Grafana, background jobs, hardening |
| 4. AI-ready | MCP server, map, crawl, batch |
| 5. Power features | Webhooks, LLM extract, scheduling, browser rendering, search, proxies |
| 6. Polish | PGlite local-first UI, Loki and OpenTelemetry |

Full details in [ROADMAP.md](ROADMAP.md).

## Responsible use

Distill respects robots.txt by default and blocks requests to private networks.
You are responsible for following each site's terms of service and applicable laws.

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md) for project conventions.

## License

[MIT](LICENSE)
