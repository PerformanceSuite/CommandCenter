# Repository Guidelines

## Project Structure & Module Organization
CommandCenter is split across Python services, web clients, and hub simulators. Core FastAPI code lives in `backend/app/`, with Alembic migrations in `backend/alembic/` and CLI utilities in `backend/cli/`. The React + Vite console ships from `frontend/src/`, while hub experiments and monitoring dashboards stay under `hub/`. Shared contract assets—schemas, fixtures, and snapshots—sit in `schemas/`, `fixtures/`, and `snapshots/`. End-to-end Playwright specs are in `e2e/`, reusable packages in `libs/`, and operational scripts in `scripts/`. Consult `docs/` for design notes and runbooks before proposing structural changes.

## Build, Test, and Development Commands
Use `make setup` on first run to copy `.env.template` and permission scripts, then `make start` (or `make dev` for live reload) to launch Docker stacks. `make test` runs backend `pytest` and frontend `vitest`, while `make test-e2e` executes Playwright flows in `e2e/`. Reach for `make lint` / `make format` to enforce style, `make migrate` to apply database upgrades, and `make logs-backend` or `make logs-frontend` when triaging services. Run `make check-ports` before starting if local ports are shared.

## Coding Style & Naming Conventions
Backend Python follows Black (line length 100) and Flake8; prefer 4-space indents, snake_case modules, and PascalCase SQLAlchemy models. Keep async endpoints in `app/routers/` with `*_router.py` naming, and align service abstractions under `app/services/`. Frontend TypeScript relies on ESLint + Prettier defaults via `npm run lint`; components live in `frontend/src/features/<Domain>`, using PascalCase for components and kebab-case for file names when exporting single components. Type hints are encouraged in new Python code and should pass `mypy` (`backend/mypy.ini`).

## Testing Guidelines
Unit tests belong in `tests/` mirrors of the source (e.g., `backend/tests/services/test_scheduler.py`), following the `test_*.py` pattern required by `pytest.ini`. Maintain ≥80% backend coverage and mark slow or integration cases with the predefined markers (`@pytest.mark.integration`, etc.). Frontend unit tests stay alongside components or in `frontend/src/__tests__/`, using Vitest and Testing Library helpers. Playwright journeys sit under `e2e/tests/` and can be exercised with `npm run test:chromium` for a focused run. Always attach failing artifacts (e.g., `playwright-report/`) when sharing defects.

## Commit & Pull Request Guidelines
Match the existing Conventional Commit style visible in `git log` (`feat:`, `docs:`, `test:`, `chore:`). Scope messages narrowly and describe observable behavior or intent (“fix: guard hub stream reconnects”). Pull requests should summarize impact, link relevant issues, note schema or migration changes, and list validation commands run (`make test`, `make lint`, etc.). Include screenshots or terminal captures when UI or CLI output changes. Ensure CI is green and request reviews from the owning sub-team (backend, frontend, or hub) before merge.
