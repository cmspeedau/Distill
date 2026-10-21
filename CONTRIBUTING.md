# Contributing to Distill

Thanks for helping make Distill better. This guide covers setup, conventions, and how to get a change merged.

> The project is in early development. Some commands below work only after the relevant roadmap phase lands.

## Ground rules

- Be kind and constructive. Assume good intent.
- For anything larger than a small fix, **open an issue first** so we can agree on the approach before you invest time.
- Keep pull requests focused. One logical change per PR.
- Build only the roadmap phase you are working on. See [ROADMAP.md](ROADMAP.md) and [AGENTS.md](AGENTS.md).

## Development setup

**Requirements:** Python 3.12+, [uv](https://docs.astral.sh/uv/), Node 22+ (for the UI), Docker (optional).

```bash
git clone https://github.com/cmspeedau/Distill.git
cd Distill

# Backend
uv sync --all-extras --dev
cp .env.example .env

# Frontend (from Phase 2 onward)
cd frontend && npm ci && cd ..
```

Run the app:

```bash
uv run uvicorn app.main:app --reload   # API on :8000
cd frontend && npm run dev             # UI on :5173
```

## Project layout

```
app/
  api/        # FastAPI routers (thin)
  services/   # business logic (scrape, ledger, storage, ...)
  models/     # SQLAlchemy models
  schemas/    # Pydantic schemas
  mcp/        # MCP server (thin, calls services)
  workers/    # background jobs (thin, calls services)
  config.py
  main.py
frontend/     # React dashboard
tests/
```

Put logic in `app/services/`. The API, CLI, MCP, and worker layers only translate inputs and outputs.

## Before you open a PR

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy --strict app/services
uv run pytest

# Frontend
cd frontend && npm run lint && npx tsc --noEmit && npm test -- --run
```

Auto-fix formatting with `uv run ruff format .` and `uv run ruff check --fix .`.

## Code conventions

- **Python:** fully typed, formatted with ruff, async for I/O.
- **TypeScript:** strict mode, no `any` unless justified in a comment.
- **Tests:** every bug fix gets a regression test; every feature gets tests for the happy path and key failures. Mock the network (respx), never hit live sites.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/), e.g. `feat: add crawl depth limit`.
- **Dependencies:** add a one-line justification in the PR description.

## Security-sensitive areas

Changes to these get extra scrutiny and must include tests:

- SSRF protection (private IP and metadata endpoint blocking, redirect handling)
- robots.txt handling
- Authentication and API keys
- Storage path handling (path traversal)

Found a vulnerability? Do not open a public issue. See [SECURITY.md](SECURITY.md).

## Adding a storage backend

1. Implement the `Storage` interface in `app/services/storage/`.
2. Register it in the backend factory with a config key.
3. Add tests against a fake or local emulator (e.g. MinIO for S3).
4. Document the config options in the README.

## Pull request checklist

- [ ] Tests added or updated
- [ ] `ruff`, `mypy`, and `pytest` pass locally
- [ ] Docs and README updated if behavior changed
- [ ] `ROADMAP.md` ticked for completed items
- [ ] Commit messages follow Conventional Commits
- [ ] No secrets, `.env` files, or scraped data committed

## Reporting bugs

Open an issue with what you expected vs. what happened, a minimal reproduction, your Distill version, OS, and Python version, and relevant logs (redact secrets).

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
