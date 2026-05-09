# v0.1.0-alpha Release Validation

Date: 2026-05-09 10:23:12 CST
Commit: 4ac1618dfb71649f871c8162290f8254cdb0d546
Branch: task-13-v0.1-release-validation

## Summary

Phase A release validation was performed on the v0.1.0-alpha release candidate. The backend checks, frontend typecheck/build, SQLite migration smoke test, and HTTP E2E demo workflow passed locally.

Docker Compose validation was not run on this machine because the Docker CLI is unavailable. Web workbench validation was partially run with the Next.js dev server and a real temporary API backend; route loading and API-backed workbench data endpoints were verified, but full browser click-through automation was not completed because this machine did not have browser automation permissions and Playwright is not installed.

No release-blocking issue was found in the checks that were actually run. Before creating the final tag, a human browser click-through on a machine with browser permissions is still recommended.

## Local Checks

- `bash scripts/check.sh`: passed
- Backend pytest: 132 passed
- Frontend typecheck: passed
- Frontend build: passed
- SQLite migration smoke: passed

Notes:

- The local check ran backend tests, frontend typecheck/build, and SQLite Alembic upgrade/downgrade/upgrade smoke validation.
- The command completed with `==> Local validation finished`.

## HTTP E2E Demo

- Command: `POLICYLENS_API_BASE_URL=http://127.0.0.1:8013 python3 scripts/e2e_demo.py`
- Backend runtime: temporary SQLite database and temporary storage directory under `/tmp`
- Result: passed
- Project ID: `a81e8be5-6fe4-42ba-b119-bc8224f4a067`
- Policy ID: `7a141f97-d5ef-49b4-b521-66cf87c53f05`
- Analysis Job ID: `bf309d51-f439-4207-be05-9ad910de0129`
- Report Export ID: `ae93ac7d-edc5-40be-a8c9-6e9b64a287f2`
- Policy Export ID: `243bedf8-94e5-4f1b-b3c5-e1cba637d0db`

The script completed with:

```text
PolicyLens v0.1 demo workflow completed successfully.
```

The demo covered health check, project creation, policy upload, policy parsing, policy ingestion, research article upload, article parsing, analysis execution, evidence retrieval, impact matrix retrieval, Markdown report retrieval, report export creation, and policy original export creation.

## Docker Compose Validation

- `docker compose config`: not run locally
- `docker compose up --build`: not run locally
- `docker compose exec api alembic upgrade head`: not run locally
- `/api/health` against Compose API: not run locally
- `e2e_demo.py` against Compose API: not run locally
- Notes: Docker is unavailable on this machine. Running `docker --version` returned `command not found`.

GitHub CI coverage:

- Docker Compose Config: passed in GitHub CI for the merged Task 12 PR
- PostgreSQL Migration: passed in GitHub CI for the merged Task 12 PR

## Web Workbench Validation

- Home page: route smoke passed with HTTP 200 at `http://127.0.0.1:3013/`
- Projects page: route smoke passed with HTTP 200 at `http://127.0.0.1:3013/projects`
- New project page: route smoke passed with HTTP 200 at `http://127.0.0.1:3013/projects/new`
- Project workbench: API-backed data endpoints were verified against the demo project and completed analysis job
- Policy library: route smoke passed with HTTP 200 at `http://127.0.0.1:3013/policy-library`
- Model settings: route smoke passed with HTTP 200 at `http://127.0.0.1:3013/settings/models`

Runtime used:

- Backend API: temporary local API at `http://127.0.0.1:8013`
- Frontend: `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8013 npm run dev -- --port 3013`

Verified API-backed workbench data endpoints:

- `GET /api/analysis/jobs/{job_id}/steps`: returned 11 steps
- `GET /api/analysis/jobs/{job_id}/plan`: returned the persisted research plan
- `GET /api/analysis/jobs/{job_id}/result`: returned the analysis result
- `GET /api/analysis/jobs/{job_id}/claims`: returned 10 claims
- `GET /api/analysis/jobs/{job_id}/policy-matches`: returned 50 policy matches
- `GET /api/analysis/jobs/{job_id}/evidence`: returned claim-policy evidence and fact boundaries
- `GET /api/analysis/jobs/{job_id}/impact-matrix`: returned 50 impact items
- `GET /api/analysis/jobs/{job_id}/report`: returned Markdown report payload

Notes:

- Full browser click-through was not completed on this machine.
- Python Playwright is not installed in the local environment.
- Computer Use browser permissions were not granted, so browser UI automation could not inspect or click the running web app.
- The frontend was still started successfully, and all major public routes returned HTTP 200.

## Security / Repository Hygiene

- `.env` not committed: verified
- `storage/` not committed: verified
- export ZIP files not committed: verified
- no real API keys committed: verified by release artifact review and `.env.example` usage
- examples are fictional: verified. The demo policy file clearly states it is fictional sample data and not a real policy document.

Local notes:

- `scripts/check.sh` created `services/api/.check.db`; this file is a local ignored check artifact and should not be committed.
- HTTP E2E generated files only under a temporary `/tmp` storage directory.

## Known Limitations

- Deterministic analysis requires human review.
- No Qdrant, embedding, or RAG integration yet.
- No OCR.
- No production authentication or permission system.
- No PPT, DOCX, or PDF report export.
- No policy crawler.
- LLM Provider Gateway exists, but the demo workflow does not require real external LLM calls.

## Release Recommendation

Ready for Phase A validation PR: yes.

Reason: backend, frontend, migration, and HTTP E2E checks passed locally, release artifacts are present, and no release-blocking issue was found in the validations that were actually run.

Recommended before tag/release: run one final human browser click-through and Docker Compose validation on a machine with Docker and browser automation or manual browser access available.
