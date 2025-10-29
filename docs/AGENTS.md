# Repository Guidelines

## Project Structure & Module Organization
CommandCenter is split into service folders: `backend/app` (FastAPI API, Alembic migrations, CLI), `frontend/src` (React + Vite UI), and `hub/**` for the multi-tenant portal. Shared Python packages live under `libs/knowledgebeast`, while automation and ops scripts sit in `scripts/`, `monitoring/`, and `traefik/`. Tests mirror the code: `backend/tests` for pytest suites, `frontend/src/__tests__` and `src/hooks/__tests__` for Vitest, and `e2e/tests` for Playwright scenarios.

## Build, Test, and Development Commands
Use Docker-driven Make targets for consistency: `make setup` seeds `.env`, `make start` boots the stack, and `make dev` merges the dev overrides for hot reload. `make test` runs backend and frontend unit suites in containers; append `test-e2e` for Playwright. Lint via `make lint`; format with `make format`. During focused backend work, `docker-compose exec backend pytest tests/api/test_health.py` exercises a single file, while `npm --prefix frontend run build` verifies the UI bundle.

## Coding Style & Naming Conventions
Python modules follow Black defaults (88 chars, 4-space indent) with Flake8 enforcing import order and unused code checks. Prefer typed Pydantic schemas and route handlers returning JSONResponse helpers. React code is TypeScript-first: components in `PascalCase`, hooks prefixed with `use`, and test utilities in `camelCase`. Keep Tailwind utility classes grouped by layout → color → state, and avoid anonymous default exports so hot reload stays stable.

## Testing Guidelines
Target ≥80% backend coverage and ≥60% frontend coverage before merging, matching README metrics. Name Python tests `test_<feature>.py` and scope fixtures in `backend/tests/conftest.py`. Frontend specs belong in `*.test.tsx` or `__tests__` folders; keep Playwright journeys under `e2e/tests` with descriptive slugs (`technologies.spec.ts`). Capture updated artefacts from `playwright-report/` for UI regressions, and attach logs when `make test` fails.

## Commit & Pull Request Guidelines
Follow Conventional Commits (`feat(api): add repository sync (#123)`) for code work; weekly reporting entries may use the existing “Week N Track M” pattern. Squash noisy WIP commits. Each PR should include a concise summary, linked Linear/GitHub issue, screenshots or cURL output for UI/API changes, and confirmation that `make lint` and the targeted tests passed. Update `docs/` or in-app copy alongside behavioural changes.

## Security & Configuration Tips
Never reuse `.env` files across client deployments; set a unique `COMPOSE_PROJECT_NAME` per instance to isolate volumes. Store secrets via your team’s vault and avoid committing generated backups from `backups/`. Run `make check-ports` before starting services to prevent leaking data into another stack.
