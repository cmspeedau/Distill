# Contributing to Distill

Thanks for helping make Distill better. This guide covers setup, conventions, and how to get a change merged.

## Ground rules

- Be kind and constructive. Assume good intent.
- For anything larger than a small fix, **open an issue first** so we can agree on the approach before you invest time.
- Keep pull requests focused. One logical change per PR.

## Development setup

**Requirements:** Python 3.12+, [uv](https://docs.astral.sh/uv/), Node 22+ (for the UI), Docker (optional).

```bash
git clone https://github.com/YOUR_USER/distill.git
cd distill

# Backend
uv sync --all-extras --dev
cp .env.example .env

# Frontend (from Phase 2 onward)
cd web && npm ci && cd ..
```

Run the app:

```bash
uv run distill serve        # API on :8000
cd web && npm run dev       # UI on :5173
```

Or run everything with Docker:

```bash
docker compose up --build
```

## Project layout

```
distill/
  services/    # business logic (scraping, extraction, storage, ledger)
  api/         # FastAPI routes, thin wrappers over services
  cli/         # CLI commands, thin wrappers over services
  mcp/         # MCP server, thin wrapper over services
web/           # React dashboard
tests/
```

Put logic in `services/`. The API, CLI, and MCP layers should only translate inputs and outputs.

## Before you open a PR

Run the same checks CI runs:

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy --strict distill
uv run pytest

# Frontend
cd web && npm run lint && npx tsc --noEmit && npm test -- --run
```

Auto-fix formatting with `uv run ruff format .` and `uv run ruff check --fix .`.

## Code conventions

- **Python:** fully typed (`mypy --strict`), formatted with ruff, async where I/O is involved.
- **TypeScript:** strict mode, no `any` unless justified in a comment.
- **Tests:** every bug fix gets a regression test; every new feature gets tests for the happy path and key failure cases. Mock the network, never hit live sites in tests.
- **Commits:** use [Conventional Commits](https://www.conventionalcommits.org/), e.g. `feat: add crawl depth limit` or `fix: block link-local IPs in SSRF check`.

## Security-sensitive areas

Changes to the following get extra scrutiny and must include tests:

- SSRF protection (private IP and metadata endpoint blocking, redirect handling)
- robots.txt handling
- Authentication and API keys
- Storage path handling (path traversal)

If you find a vulnerability, **do not open a public issue**. See [SECURITY.md](SECURITY.md) or email the maintainer directly.

## Adding a storage backend

Storage is pluggable. To add one (S3, GCS, etc.):

1. Implement the `StorageBackend` interface in `distill/services/storage/`.
2. Register it in the backend factory with a config key.
3. Add tests against a fake or local emulator (e.g. MinIO for S3).
4. Document the config options in the README.

## Pull request checklist

- [ ] Tests added or updated
- [ ] `ruff`, `mypy`, and `pytest` pass locally
- [ ] Docs and README updated if behavior changed
- [ ] Commit messages follow Conventional Commits
- [ ] No secrets, `.env` files, or scraped data committed

## Reporting bugs

Open an issue with:

- What you expected vs. what happened
- The URL type or a minimal reproduction (avoid sharing private sites)
- Distill version, OS, and Python version
- Relevant logs (redact API keys)

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
