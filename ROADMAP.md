Here is the full roadmap with everything we've added: the MCP server, the setup wizard, storage, metrics, Grafana, and the extra features. It is rebuilt from our conversation and the phase list in the estimates, so if your repo's `ROADMAP.md` has diverged, tell me and I'll reconcile it.

````markdown
# ROADMAP.md

Self-hosted web scraper (Firecrawl-style): URL in, clean Markdown out, stored in
a ledger, usable from the UI, REST API, and AI tools via MCP.

Legend: [ ] todo, [x] done

---

## Milestone 1: MVP (scrape, API, ledger)

### Phase 1: Core scraper
- [ ] Project setup (uv, ruff, mypy, pytest, pre-commit)
- [ ] Fetcher (timeouts, size limits, redirects, retries)
- [ ] SSRF protection (private/loopback/metadata IPs, redirect re-checks)
- [ ] robots.txt support with per-origin cache
- [ ] Main-content extraction, metadata, links
- [ ] Markdown + cleaned HTML output, content hash
- [ ] CLI: `python -m app.cli scrape <url>`

### Phase 2: REST API + React input page
- [ ] FastAPI app, `POST /scrape`, `GET /health`
- [ ] Pydantic request/response schemas, error mapping
- [ ] React + Vite UI: URL input, options, rendered Markdown result

### Phase 3: Persistence
- [ ] SQLAlchemy models + Alembic migrations
- [ ] Store every scrape (ledger row, content hash, timing, status)
- [ ] Dedupe / re-scrape detection by content hash

### Phase 5: Ledger UI
- [ ] List, search, filter scrapes
- [ ] Detail view (Markdown, HTML, metadata, links)
- [ ] Re-scrape and delete actions

---

## Milestone 2: Make it yours (wizard, storage, dashboard)

### Phase 2b: Setup wizard
- [ ] First-run wizard in the UI and a CLI equivalent
- [ ] Choose database: SQLite or PostgreSQL (recommended)
- [ ] Choose storage: local disk or S3-compatible
- [ ] Connection tests for DB and storage before saving
- [ ] Bootstrap config file, credentials encrypted at rest

### Phase 4: Storage abstraction
- [ ] `Storage` interface
- [ ] Local filesystem implementation
- [ ] S3-compatible implementation (AWS, MinIO, R2)
- [ ] Store raw HTML, Markdown, and assets via the interface

### Phase 6: Built-in metrics dashboard
- [ ] Metrics collection (scrapes, success rate, latency, errors, bytes)
- [ ] In-app dashboard page with charts

---

## Milestone 3: Operate it (observability, jobs, hardening)

### Phase 6b: Prometheus + Grafana
- [ ] `/metrics` endpoint (prometheus-client)
- [ ] Docker Compose profile with Prometheus + Grafana
- [ ] Provisioned Grafana dashboards
- [ ] Alert rules (error rate, latency, queue depth)

### Phase 7: Background jobs
- [ ] Job queue and workers
- [ ] Async scrape endpoints, job status and results
- [ ] Retry policy, dead-letter handling

### Phase 9: Hardening
- [ ] Authentication and API keys
- [ ] Rate limiting
- [ ] SSRF review and tests, credential handling review
- [ ] CI pipeline (lint, types, tests)
- [ ] Production Dockerfile and Compose setup
- [ ] Docs: install, config, security notes

---

## Milestone 4: AI-ready

### Phase 8: MCP server
- [ ] MCP server in `app/mcp/`, calling the same service layer
- [ ] Tools: scrape, search ledger, get scrape, map, crawl
- [ ] Auth and usage docs for Claude Desktop / other MCP clients

### Phase 10: Map
- [ ] Discover URLs for a site (sitemap + link discovery)
- [ ] API endpoint, UI, MCP tool

### Phase 11: Crawl
- [ ] Recursive crawl with depth and page limits
- [ ] Scope rules (domain, path include/exclude)
- [ ] Politeness (delays, concurrency per host)
- [ ] URL dedupe, failure handling, progress reporting

### Phase 12: Batch scrape
- [ ] Submit many URLs in one request
- [ ] Per-URL status and aggregated results

---

## Milestone 5: Power features (optional, build as needed)

### Phase 13: Webhooks
- [ ] Register webhooks for job and crawl events
- [ ] Signed payloads, retries, delivery log

### Phase 14: LLM extract
- [ ] Structured extraction from a JSON schema or prompt
- [ ] Pluggable LLM provider config

### Phase 15: Scheduling and change monitoring
- [ ] Recurring scrapes (cron-style)
- [ ] Change detection with diffs and notifications

### Phase 16: Browser rendering
- [ ] Playwright worker pool for JavaScript-heavy pages
- [ ] Wait conditions, actions, screenshots
- [ ] Per-request opt-in (`render: true`)

### Phase 17: Search
- [ ] Full-text search over stored content
- [ ] Web search integration
- [ ] Optional pgvector semantic search

### Phase 18: Proxies and anti-bot
- [ ] Proxy pool configuration and rotation
- [ ] Per-domain overrides, header/UA strategies

---

## Milestone 6: Polish

### Phase 19: PGlite local-first frontend
- [ ] In-browser PGlite cache of the ledger
- [ ] Offline browsing and sync with the server

### Phase 20: Loki + OpenTelemetry
- [ ] Structured logs shipped to Loki
- [ ] OpenTelemetry traces across API, workers, and fetcher

---

## Cross-cutting rules
- One service layer (`app/services/`); API, MCP, CLI, and workers stay thin
- DB and storage are always accessed through abstractions
- Every scrape emits metrics and a ledger row
- SSRF protection and robots.txt are on by default

## Open questions
- [ ] Queue backend: Postgres-based, Redis, or in-process for small installs
- [ ] SQLite to Postgres migration path for existing users
- [ ] Auth model for MCP (shared API key vs per-client keys)
- [ ] LLM provider default for Phase 14
````

I kept the phase numbers from the estimates table (including 2b and 6b) so the time estimates and the Phase 1 prompt still line up. The milestone order follows the estimates, so Phase 8 (MCP) sits under "AI-ready" even though its number is lower than some earlier-built phases.

I can also produce a shorter version with only the unchecked work, or add a time estimate next to each phase.
