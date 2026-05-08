# Installation Draft

This document covers v0.1 local setup for PolicyLens / 政研透镜.

## Requirements

- Docker and Docker Compose for full local stack
- Node.js 22 or newer for frontend development
- Python 3.11 or newer for backend development

## Environment

Create a local environment file when needed:

```bash
cp .env.example .env
```

Do not put real credentials into committed files. API keys should stay in local `.env`, a secret manager, or deployment-specific secret storage.

Upload-related environment defaults:

```bash
STORAGE_DIR=./storage
MAX_UPLOAD_SIZE_MB=50
ALLOWED_UPLOAD_EXTENSIONS=.pdf,.docx,.txt,.md,.markdown,.html,.htm
CHUNK_MAX_CHARS=2000
```

LLM Provider secrets are also environment-based. Keep real values in local `.env` or secret storage, never in committed files:

```bash
DEEPSEEK_API_KEY=
CUSTOM_LLM_API_KEY=
```

## API Setup

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
PYTHONPATH=../..:. uvicorn app.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/api/health
```

## Web Setup

```bash
cd apps/web
npm install
export NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev
```

Open http://localhost:3000.

`NEXT_PUBLIC_API_BASE_URL` is read by client-side pages. If it is omitted, the web app defaults to `http://localhost:8000`. The Next.js build does not require the backend to be running.

## Worker Setup

```bash
cd services/worker
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m app.main
```

The worker is a placeholder loop in v0.1.

## Database URL

For local PostgreSQL development, set:

```bash
export DATABASE_URL=postgresql://policylens:policylens@localhost:5432/policylens
```

The API normalizes `postgresql://` to SQLAlchemy's `postgresql+psycopg://` driver internally.

## Upload Storage

Document uploads are stored on the local filesystem for v0.1. The API writes files below `STORAGE_DIR` and stores only relative keys in the database:

```text
documents/{project_id}/{document_id}/{safe_filename}
```

`POST /api/documents/upload` creates records with `parse_status=pending`. Run `POST /api/documents/{document_id}/parse` to parse uploaded `.txt`, `.md`, `.markdown`, `.html`, `.htm`, `.docx`, or searchable `.pdf` files and write `document_chunks`.

The v0.1 basic parser does not run OCR. Scanned PDFs or files with no extractable text move to `parse_status=failed` and store a short error summary in `metadata.parse_error`.

## Policy Library

To ingest a policy into the local policy library:

1. Upload a document with `document_role=policy`.
2. Parse it with `POST /api/documents/{document_id}/parse`.
3. Ingest it with `POST /api/policies/from-document`.

The ingestion step writes `policies`, `policy_versions`, and `policy_sections`. It requires parsed chunks and does not crawl remote policy sources, run policy association analysis, or call LLMs.

Use `GET /api/policies/{policy_id}/original` to view current normalized policy text.

## LLM Gateway

Provider configs are managed through:

```bash
curl -X POST http://localhost:8000/api/llm/providers \
  -H "Content-Type: application/json" \
  -d '{
    "provider_id": "openai_compatible_custom",
    "display_name": "Custom Gateway",
    "provider_family": "openai_compatible",
    "base_url": "https://example.com/v1",
    "api_key_env": "CUSTOM_LLM_API_KEY",
    "model_name": "<user-configured-model>",
    "enabled": true
  }'
```

The database stores only `api_key_env`, not the secret value. `POST /api/llm/providers/{provider_id}/test` and `POST /api/llm/chat` make real OpenAI-compatible `/chat/completions` calls when the provider is configured. CI tests mock these calls and do not require real API keys.

## Research Plan

After uploading a research article, run the synchronous v0.1 Research Plan engine with:

```bash
curl -X POST http://localhost:8000/api/analysis/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "<project_id>",
    "document_ids": ["<document_id>"],
    "analysis_types": ["policy_deep_dive"],
    "model_profile": "china_balanced"
  }'
```

Inspect execution state and evidence boundaries with:

```bash
curl http://localhost:8000/api/analysis/jobs/<job_id>
curl http://localhost:8000/api/analysis/jobs/<job_id>/steps
curl http://localhost:8000/api/analysis/jobs/<job_id>/plan
curl http://localhost:8000/api/analysis/jobs/<job_id>/result
curl http://localhost:8000/api/analysis/jobs/<job_id>/claims
curl http://localhost:8000/api/analysis/jobs/<job_id>/policy-matches
curl http://localhost:8000/api/analysis/jobs/<job_id>/evidence
curl http://localhost:8000/api/analysis/jobs/<job_id>/impact-matrix
curl http://localhost:8000/api/analysis/jobs/<job_id>/report
```

The current engine runs deterministic steps and does not require LLM credentials. It can parse pending documents, collect chunks, extract simple signals, extract basic claims, retrieve local policy candidates with SQL keyword matching, match claims to policy sections, write `policy_matches`, persist an evidence map, generate `impact_items`, and draft `analysis_results.report_markdown`. It does not run Qdrant, embeddings, RAG, complex policy reasoning, LLM judgment, formal investment advice, or formal report writing.

List historical jobs for a project:

```bash
curl "http://localhost:8000/api/analysis/jobs?project_id=<project_id>"
```

## Policy Export

After a policy has been ingested, create a ZIP export with:

```bash
curl -X POST http://localhost:8000/api/exports/policy-originals \
  -H "Content-Type: application/json" \
  -d '{
    "policy_ids": ["<policy_id>"],
    "mode": "single_policy_full_text",
    "formats": ["markdown", "txt", "html", "json"]
  }'
```

The API writes the ZIP below `STORAGE_DIR` and stores only a relative key:

```text
exports/{export_id}/policy_export_bundle.zip
```

Inspect the export with:

```bash
curl http://localhost:8000/api/exports/<export_id>
```

Download it with:

```bash
curl -OJ http://localhost:8000/api/exports/<export_id>/download
```

Supported modes are `single_policy_full_text`, `related_policy_bundle`, `cited_sections_only`, `evidence_bundle`, and `machine_readable_json`. The v0.1 exporter does not include raw web or PDF snapshots.

## Report Export

After a Research Plan job has completed, create a report bundle with:

```bash
curl -X POST http://localhost:8000/api/exports/report \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "<job_id>",
    "formats": ["markdown", "json", "html"],
    "include_evidence_bundle": true,
    "include_impact_matrix": true,
    "include_policy_matches": true
  }'
```

The API writes:

```text
exports/{export_id}/report_export_bundle.zip
```

The ZIP contains `manifest.json`, `reports/report.md`, `reports/report.json`, optional `reports/report.html`, evidence JSON, impact matrix JSON, policy matches JSON, and `checksums/sha256.txt`.

Download it with the shared export download endpoint:

```bash
curl -OJ http://localhost:8000/api/exports/<export_id>/download
```

Report export supports only `markdown`, `json`, and `html`. PPT, DOCX, and PDF report exports are not supported in v0.1.

## Migration Checks

From `services/api`, run:

```bash
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

For a quick migration smoke test without PostgreSQL:

```bash
DATABASE_URL=sqlite+pysqlite:///./.check.db alembic upgrade head
DATABASE_URL=sqlite+pysqlite:///./.check.db alembic downgrade -1
DATABASE_URL=sqlite+pysqlite:///./.check.db alembic upgrade head
```
