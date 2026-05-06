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
npm run dev
```

Open http://localhost:3000.

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
