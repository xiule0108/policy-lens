# Troubleshooting

## Docker Is Not Running

Symptom: `docker compose up` or `docker compose config` fails.

Check Docker Desktop is open, then run:

```bash
docker compose config
```

## Database Connection Failed

Symptom: API logs show database connection errors.

Check `DATABASE_URL` and whether PostgreSQL is running:

```bash
docker compose ps
docker compose logs postgres
```

For local backend development, use:

```bash
export DATABASE_URL=postgresql://policylens:policylens@localhost:5432/policylens
```

## Alembic Migration Error

Run migrations from the API service:

```bash
cd services/api
alembic current
alembic upgrade head
```

In Docker Compose:

```bash
docker compose exec api alembic upgrade head
```

Do not reset or delete production data to fix a migration without review.

## Frontend Cannot Connect To API

Set the browser-facing API base URL:

```bash
export NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

In Docker Compose, the default is already `http://localhost:8000`. In hosted deployments, this must be the public API origin reachable by the user's browser.

## File Upload Failed

Check:

- `MAX_UPLOAD_SIZE_MB`
- `ALLOWED_UPLOAD_EXTENSIONS`
- `STORAGE_DIR` exists and is writable
- `project_id` exists
- file is not empty

Supported default extensions are `.pdf,.docx,.txt,.md,.markdown,.html,.htm`.

## Document Parsing Failed

The v0.1 parser supports text-like documents, DOCX, HTML, Markdown, and searchable PDFs. OCR is not supported. Scanned PDFs may fail with no extractable text.

Inspect:

```bash
GET /api/documents/{document_id}
```

Look for `parse_status=failed` and `metadata.parse_error`.

## Policy Ingestion Failed

Policy ingestion requires:

- `document_role=policy`
- `parse_status=parsed`
- at least one `document_chunks` row
- a valid `storage_key`

Parse the document first:

```bash
POST /api/documents/{document_id}/parse
```

## Analysis Task Failed

Inspect:

```bash
GET /api/analysis/jobs/{job_id}
GET /api/analysis/jobs/{job_id}/steps
GET /api/analysis/jobs/{job_id}/plan
```

The failed job stores a short error message. Full tracebacks are not written to the database.

## Export Download Failed

Check export status:

```bash
GET /api/exports/{export_id}
```

Only `completed` exports can be downloaded. If the file is missing, confirm that `STORAGE_DIR` is persistent and has not been deleted.

## Provider Test Failed

Provider tests make real OpenAI-compatible calls. Check:

- `base_url`
- `model_name`
- `api_key_env`
- the environment variable named by `api_key_env` is set
- local providers use a running local OpenAI-compatible server

PolicyLens never stores or returns API key values.

## API Key Env Is Not Configured

Add the real key to local `.env` or deployment secrets:

```bash
DEEPSEEK_API_KEY=...
CUSTOM_LLM_API_KEY=...
```

Do not commit `.env`.
