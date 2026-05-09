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

## Phase B Final Validation

Date: 2026-05-09 12:06:40 CST
Commit: 2b81a68a00f24221a55cd7b12fffa274ded368ff

### Local Checks

- `bash scripts/check.sh`: passed
- Backend pytest: 132 passed
- Frontend typecheck: passed
- Frontend build: passed
- SQLite migration smoke: passed

The command completed with `==> Local validation finished`.

### Docker Compose Final Validation

- Docker runtime: Docker CLI and Docker Compose with a Colima-backed local Docker daemon
- `docker compose config`: passed
- `docker compose up --build -d`: passed
- `docker compose ps`: passed. The `api`, `postgres`, `qdrant`, `web`, and `worker` services were all up.
- `docker compose exec -T api alembic upgrade head`: passed
- `/api/health`: passed

Health response summary:

```json
{
  "status": "ok",
  "service": "policy-lens-api",
  "version": "0.1.0-alpha",
  "dependencies": {
    "database": {"status": "configured", "mode": "sqlalchemy"},
    "vector_store": {"status": "not_connected", "mode": "v0.1_mock"},
    "storage": {"status": "configured", "mode": "local_filesystem"}
  }
}
```

- `POLICYLENS_API_BASE_URL=http://localhost:8000 python3 scripts/e2e_demo.py`: passed
- Compose API logs: no application errors observed in the checked log tail. The API served the expected health, upload, parse, policy ingestion, analysis, evidence, impact matrix, report, export, and download requests with successful 2xx responses.
- Compose web logs: no application errors observed in the checked log tail. The web service started successfully with Next.js and served the validated routes.
- `docker compose down`: completed after validation

HTTP E2E demo output:

```text
PolicyLens v0.1 demo workflow completed successfully.
Project ID: 5c335695-390b-477a-af9c-e77aea1fbe89
Policy ID: 0d75007f-dd8f-4e8f-a692-1fa3308d93c0
Analysis Job ID: e39821bc-aa3b-47e7-a977-3dadbab93208
Report Export ID: 3599203c-d982-46fa-b598-32e1e909c79f
Policy Export ID: 33865506-889b-4a1b-9d66-011018017a02
```

### Web Workbench Final Click-through

Runtime:

- Frontend: Docker Compose web service at `http://localhost:3000`
- Backend: Docker Compose API service at `http://localhost:8000`
- Browser: Chrome Incognito window

Validation project:

- Project ID: `acf51939-301b-4ebc-9e9f-2389e50af432`
- Analysis Job ID: `f953e711-1945-45bb-bae8-9ab209af9efd`
- Analysis Result ID: `167ff4bd-9ca8-4ca1-8575-de2e51822134`
- Report Export ID: `99969807-5294-4889-b921-f13789ced772`
- Policy Export ID: `d12cfacd-e53d-41b4-91ce-2844e0984607`

Results:

- Home: passed. The home page opened and displayed `v0.1.0-alpha`.
- Projects: passed. The projects route opened successfully.
- New project: passed. A new project named `v0.1 final validation project` was created from the web form.
- Project workbench: passed. The project workbench opened and loaded real project data.
- Upload policy: passed. `examples/demo-policy-notice.txt` was selected through the browser file picker and uploaded with role `policy`.
- Parse policy: passed. The policy document moved to `parsed`.
- Ingest policy: passed. The policy document was ingested from the workbench, and the policy count updated.
- Upload research article: API-assisted. Reopening the file picker in this automation environment repeatedly triggered a Chrome remote debugging permission prompt. The prompt was not allowed. The research article was uploaded and parsed through the same local API, then the workbench was reloaded and showed the parsed article in the document list. The policy file upload already validated the workbench file input path.
- Parse research article: passed through local API, and the workbench displayed the research article as `parsed`.
- Run analysis: passed from the workbench. The selected research article produced a completed analysis job.
- Steps: passed. The workbench displayed the persisted steps, including `research_plan`, `parse_document_if_needed`, `collect_document_context`, `extract_article_signals`, `extract_claims`, `retrieve_policy_candidates`, `match_policy_sections`, `build_evidence_map`, `build_impact_matrix`, `summarize_findings`, and `draft_markdown_report`.
- Plan / result: passed. The workbench loaded plan and result-backed summary data.
- Claims: passed. The evidence tab displayed 10 deterministic claims.
- Policy matches: passed. The policy association tab showed 2 candidate policies and 50 section matches.
- Evidence: passed. The evidence tab displayed the claim-policy evidence map and fact boundaries.
- Impact matrix: passed. The impact matrix tab displayed rule-based impact items with subject, direction, horizon, mechanism, market variable, confidence, and explanation columns.
- Markdown report: passed. The report tab displayed a generated Markdown report beginning with `# 政策与市场研究解析报告`.
- Report export: passed. The workbench created a completed report export and displayed a download link.
- Report export download: passed through the download endpoint. The downloaded ZIP was saved to `/tmp` for validation and contained `manifest.json`, `reports/report.md`, `reports/report.json`, `reports/report.html`, `evidence/evidence.json`, `impact_matrix/impact_matrix.json`, `policy_matches/policy_matches.json`, and `checksums/sha256.txt`.
- Policy original export: passed. The workbench created a completed policy original export and displayed a download link.
- Policy original export download: passed through the download endpoint. The downloaded ZIP was saved to `/tmp` for validation and contained policy Markdown/JSON files, `manifest.json`, and `checksums/sha256.txt`.
- Policy library: passed. `/policy-library` displayed policies from the database. `查看原文` loaded normalized policy text and sections.
- Model settings: passed. `/settings/models` displayed provider presets, env var names, `missing env` status, local provider metadata, and did not ask for real API key values.

Notes:

- A normal Chrome window showed a hydration mismatch overlay caused by the Immersive Translate extension adding an attribute to the `<html>` element. The final click-through used Chrome Incognito, where the page loaded cleanly.
- Chrome displayed a remote debugging permission prompt during file picker automation. The prompt was not granted. This was treated as an automation environment constraint rather than an app behavior failure.
- Screenshots were not committed to the repository.

### Security / Repository Hygiene

- `.env` was created from `.env.example` for Compose validation and removed after validation.
- `storage/` and `services/api/storage/` remained ignored local runtime artifacts and were not committed.
- Export ZIP downloads were written to `/tmp` for validation and removed before commit.
- No real API keys were entered in the browser, written to `.env`, or committed.
- Demo policy data remained clearly marked as fictional example data.

### Final Release Recommendation

Ready for tag/release: yes.

Reason: local checks, Docker Compose startup, PostgreSQL migration, Compose API health, HTTP E2E demo, core Web workbench flow, policy library, model settings, report export, and policy original export all passed. The only observed limitations were automation-environment issues around Chrome extension behavior and file picker remote debugging prompts; neither indicates a release-blocking application bug.
