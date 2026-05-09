# PolicyLens / 政研透镜

**PolicyLens is an open-source policy and market research analysis workbench.** It helps researchers upload articles, ingest local policy originals, run a deterministic research workflow, inspect evidence chains, build a basic impact matrix, draft Markdown reports, and export auditable ZIP bundles.

Current version:

```text
v0.1.0-alpha
```

PolicyLens is currently a v0.1 engineering scaffold and alpha release candidate. The v0.1 target is a runnable minimum research loop, not a production policy intelligence platform.

## Use Cases

- Policy research and policy impact review
- Industry and market research notes
- Energy, power market, storage, green power, and similar domain demos
- Citation-aware evidence workflows for internal research
- OpenAI-compatible LLM Provider configuration experiments

## Core Features

- Project creation and API-backed Web workbench
- Real document upload to local storage
- Basic parsing for text, Markdown, HTML, DOCX, and searchable PDF files
- `document_chunks` persistence
- Parsed policy document ingestion into `policies`, `policy_versions`, and `policy_sections`
- Policy original viewing and ZIP export
- Synchronous Research Plan execution engine
- Deterministic claim extraction and policy section matching
- `claims`, `policy_matches`, evidence map, and factual boundaries
- Deterministic impact matrix and Markdown report draft
- Report ZIP export with manifest and checksums
- OpenAI-compatible LLM Provider gateway with China provider presets, custom provider, and local provider support

## v0.1.0-alpha Capability List

The alpha can run this end-to-end loop:

```text
create project
upload policy file
parse policy file
ingest policy
upload research article
parse research article
run analysis
inspect claims, matches, evidence, impact matrix, and report
export report bundle
export policy original bundle
```

Current analysis and reporting are deterministic rule-based drafts. They are research aids only and require human review.

## Architecture Overview

```text
Web workbench
  -> FastAPI API
      -> PostgreSQL metadata
      -> local filesystem storage
      -> deterministic parser / research steps
      -> ZIP exporters
      -> OpenAI-compatible LLM Gateway

Reserved for later:
  -> worker runtime
  -> Qdrant vector retrieval
  -> MinIO/object storage
```

## Tech Stack

- Monorepo
- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Backend: FastAPI, Python
- Database: PostgreSQL
- Object storage: local filesystem in v0.1, MinIO reserved
- Vector database: Qdrant reserved
- Worker: Python worker skeleton
- LLM Gateway: OpenAI-compatible HTTP adapter
- Deployment: Docker Compose

## Quick Start With Docker Compose

```bash
git clone https://github.com/xiule0108/policy-lens.git
cd policy-lens
cp .env.example .env
docker compose up --build
docker compose exec api alembic upgrade head
```

Open:

- Web: http://localhost:3000
- API health: http://localhost:8000/api/health
- API docs: http://localhost:8000/docs

Useful Compose commands:

```bash
docker compose ps
docker compose logs api
docker compose logs web
docker compose down
```

## Run The Demo Workflow

With the API running:

```bash
python3 scripts/e2e_demo.py
```

The script uses fictional files in `examples/` and runs project creation, uploads, parsing, policy ingestion, analysis, report export, and policy original export. It does not call external LLMs and does not download ZIPs into the repository.

You can also follow:

- `docs/v0.1-demo-workflow.md`
- `examples/demo-workflow.http`

## Local Development

Backend:

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd apps/web
npm install
export NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev
```

`NEXT_PUBLIC_API_BASE_URL` is read by browser-side pages. If it is omitted, the web app defaults to `http://localhost:8000`. The Next.js production build does not require the backend to be running.

## Database Migration

Local API directory:

```bash
cd services/api
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

Docker Compose:

```bash
docker compose exec api alembic upgrade head
```

Do not run destructive resets as part of normal startup.

## Development Checks

Run the full local check:

```bash
bash scripts/check.sh
```

Or use Make:

```bash
make check
make backend-test
make frontend-build
make compose-config
```

The check script runs backend tests, SQLite migration smoke checks, frontend typecheck, and frontend production build. GitHub Actions also validates PostgreSQL migrations.

## Web Workbench

- `/projects`: database-backed project list
- `/projects/new`: project creation
- `/projects/{projectId}`: upload, parse, policy ingestion, analysis execution, steps, plan, result, claims, matches, evidence, impact matrix, Markdown report, report export, and policy original export
- `/policy-library`: database policy list/search, original text, sections, and policy export
- `/settings/models`: Provider list, upsert, and connection test

The workbench is intentionally operational and compact in v0.1. It does not include permissions, team collaboration, complex charts, or a report editor.

## Model Provider Configuration

Provider records store only public configuration and API key environment variable names. They never store API key values.

Example:

```bash
export DEEPSEEK_API_KEY=...
```

The API and settings page can configure:

- DashScope
- Qianfan
- Hunyuan
- VolcArk
- Zhipu
- DeepSeek
- Kimi
- MiniMax
- Spark
- OpenAI-compatible custom providers
- Local OpenAI-compatible providers such as Ollama or vLLM

Provider tests make real model calls only when explicitly triggered and configured. CI tests mock this path.

## Policy Original Export

`POST /api/exports/policy-originals` writes:

```text
exports/{export_id}/policy_export_bundle.zip
```

The ZIP can include:

```text
manifest.json
policies/
cited_sections/
evidence/
machine_readable/
checksums/sha256.txt
```

The exporter packages normalized policy text and sections from the database. It does not copy uploaded source files and does not include raw web/PDF snapshots in v0.1.

## Report Export

`POST /api/exports/report` writes:

```text
exports/{export_id}/report_export_bundle.zip
```

Bundle structure:

```text
manifest.json
reports/report.md
reports/report.html
reports/report.json
evidence/evidence.json
impact_matrix/impact_matrix.json
policy_matches/policy_matches.json
checksums/sha256.txt
```

Supported report formats are `markdown`, `json`, and `html`. PPT, DOCX, and PDF report exports are not supported in v0.1.

## Directory Structure

```text
policy-lens/
  apps/web/                 Next.js frontend
  services/api/             FastAPI service
  services/worker/          Python worker skeleton
  packages/core/            shared research and citation primitives
  packages/parsers/         parser package placeholders
  packages/retrievers/      search and vector retrieval placeholders
  packages/connectors/      LLM, policy source, and storage placeholders
  packages/exporters/       exporter placeholders
  docs/                     project documentation
  examples/                 fictional demo data
  scripts/                  validation and demo scripts
```

## Developer Guide

Read:

- `CONTRIBUTING.md`
- `AGENTS.md`
- `docs/plugin-development.md`
- `docs/model-providers.md`
- `docs/api.md`

Contribution areas:

- Provider presets and OpenAI-compatible gateway adapters
- Parsers for additional deterministic formats
- Exporters for additional machine-readable evidence formats
- Policy source connectors with clear source, timestamp, and checksum preservation
- Frontend review surfaces for evidence, impact matrix, and reports

## Roadmap

Near-term:

- Manual Docker Compose release validation
- v0.1.0-alpha tag and GitHub Release
- Better workbench tables for policy matches and evidence
- Optional LLM review layer
- Stronger policy matching and section-level scoring

Later:

- Qdrant, embedding, reranking, and RAG
- Policy source ingestion and official-source sync
- OCR pipeline
- Authentication and authorization
- Background worker execution
- DOCX/PDF/PPT report exports
- Production observability and audit logging

## Security And Privacy

- Never commit `.env`, API keys, tokens, private documents, local storage, databases, or generated ZIP bundles.
- `.env.example` documents variable names only.
- Uploaded files and exports are stored under `STORAGE_DIR`.
- LLM Provider responses never expose API key values.
- Demo policy files in `examples/` are fictional and are not official policies.

## Disclaimer

PolicyLens is a research aid, not legal, investment, policy compliance, or financial advice. Generated analysis, policy matches, impact matrices, and Markdown reports must be reviewed by qualified humans. Policy sources, citations, timestamps, and checksums should be preserved so downstream users can verify conclusions against source materials.

## Contributing

Contributions are welcome. Please read `CONTRIBUTING.md` and `AGENTS.md` before opening issues, pull requests, or AI-agent generated changes.

## License

MIT. See `LICENSE`.
