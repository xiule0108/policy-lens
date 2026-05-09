# v0.1.0-alpha Release Checklist

This checklist prepares a release candidate. It does not create a GitHub Release or git tag by itself.

## Pre-release Checklist

- Confirm `VERSION` contains `0.1.0-alpha`.
- Confirm `CHANGELOG.md` and `RELEASE_NOTES.md` describe the current alpha.
- Confirm examples are fictional and contain no private data.
- Confirm `.env`, storage files, database files, export bundles, and API keys are not committed.

## Local Checks

```bash
bash scripts/check.sh
```

Expected result:

- backend tests pass
- SQLite migration upgrade, downgrade, upgrade passes
- frontend typecheck passes
- frontend build passes

## Docker Checks

```bash
cp .env.example .env
docker compose up --build
docker compose ps
docker compose exec api alembic upgrade head
curl http://localhost:8000/api/health
docker compose logs api
docker compose logs web
docker compose down
```

The current Compose stack uses `/api/health` as the manual API health check.

## Backend Checks

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Frontend Checks

```bash
cd apps/web
npm install
npm run typecheck
npm run build
```

The build must not require a running backend service.

## E2E Checks

With the API running:

```bash
python3 scripts/e2e_demo.py
```

The script should print project, policy, analysis job, report export, and policy export IDs.

## Docs Checks

- README quick start works for Docker Compose.
- `docs/v0.1-demo-workflow.md` explains Web, API, and script paths.
- `docs/troubleshooting.md` covers common local failures.
- API docs mention report export and policy original export.

## Security Checks

- `git status --short` does not show `.env`, `storage/`, `.db`, `.zip`, `.venv`, or `node_modules`.
- `.env.example` contains variable names only.
- Example policy text is clearly fictional.
- No API key value appears in tests, docs, or frontend code.

## Tagging Guide

Only after manual acceptance:

```bash
git checkout main
git pull origin main
git tag -a v0.1.0-alpha -m "v0.1.0-alpha"
git push origin v0.1.0-alpha
```

Do not run these commands during Task 12 unless explicitly instructed.

## GitHub Release Guide

After tagging, create a GitHub Release from `v0.1.0-alpha` and use `RELEASE_NOTES.md` as the starting release description. Attach screenshots or demo notes only after manual verification.
