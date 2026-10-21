# AGENTS.md

## Project
**Distill** is a self-hosted web scraper (Firecrawl-style). It turns URLs into
clean Markdown, stores results in a ledger, and exposes a REST API, a React UI,
and an MCP server. Roadmap lives in `ROADMAP.md`.

## Stack
- Backend: Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, httpx, selectolax or
  BeautifulSoup, trafilatura (main-content extraction), markdownify
- Frontend: React + Vite + TypeScript
- DB: SQLite (dev) / PostgreSQL (recommended), chosen via setup wizard
- Storage: `Storage` interface, Local and S3-compatible implementations
- Metrics: prometheus-client
- Tests: pytest, pytest-asyncio, respx (HTTP mocking); Vitest for frontend
- Tooling: uv (deps), ruff (lint+format), mypy, pre-commit

## Architecture rules (do not break)
1. **One service layer.** All business logic lives in `app/services/`.
   The REST API, MCP server, CLI and workers only call service functions.
   Never put logic in route handlers or MCP tool handlers.
2. **Storage and DB are abstractions.** Code depends on the `Storage`
   interface and SQLAlchemy sessions, never on a specific backend.
3. **Config comes from one place.** `app/config.py` (env + bootstrap file).
   No `os.environ` reads scattered around the code.
4. **Every scrape emits metrics and a ledger row**, regardless of entry point.
5. **Security defaults on:** SSRF protection for all outbound fetches
   (block private/loopback/link-local IPs, re-check after redirects),
   robots.txt respected, request timeouts and size limits.

## Layout
```
app/
  api/          # FastAPI routers (thin)
  services/     # business logic (scrape, ledger, storage, ...)
  models/       # SQLAlchemy models
  schemas/      # Pydantic schemas
  mcp/          # MCP server (thin, calls services)
  workers/      # background jobs (thin, calls services)
  config.py
  main.py
tests/
frontend/
ROADMAP.md
AGENTS.md
```

## Conventions
- Type hints everywhere; `mypy --strict` on `app/services`.
- Async by default for I/O.
- Pydantic models for all inputs and outputs, no raw dicts across layers.
- Small, focused commits. One phase per branch (`phase-1-core-scraper`).
- Errors: raise typed exceptions in services (`FetchError`, `BlockedByRobots`,
  `SSRFBlocked`), map them to HTTP codes in the API layer only.
- No new dependency without a one-line justification in the PR description.

## Definition of done (every phase)
- [ ] Acceptance criteria in the phase prompt are met
- [ ] Tests written and passing (`uv run pytest`)
- [ ] `ruff check`, `ruff format --check` and `mypy` clean
- [ ] No network calls in tests (mock with respx)
- [ ] `ROADMAP.md` phase ticked, README updated if user-facing behaviour changed
- [ ] Summary of what changed, what was skipped, and any open questions

## Working agreement
- Build only the phase you were asked to build. Do not start later phases.
- If a requirement is ambiguous, ask before guessing on anything touching
  security, storage credentials, or data model changes.
- Do not weaken SSRF/robots checks to make a test pass; fix the test.
- Never commit secrets. Use `.env.example` for new variables.
