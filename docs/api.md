# API Draft

The FastAPI service is mounted under `/api`.

## Health

- `GET /api/health`

Returns service status and mock dependency states.

## Projects

- `GET /api/projects`
- `POST /api/projects`

Projects represent research workspaces. Projects are backed by the database. An empty database returns an empty list.

## Documents

- `GET /api/documents`
- `POST /api/documents/upload`
- `GET /api/documents/{document_id}`
- `GET /api/documents/{document_id}/download`

`POST /api/documents/upload` accepts `multipart/form-data`.

Form fields:

- `project_id`: UUID, required
- `document_role`: `research_article`, `policy`, or `appendix`; defaults to `research_article`
- `title`: optional
- `source_url`: optional
- `file`: uploaded file, required

Supported extensions are configured by `ALLOWED_UPLOAD_EXTENSIONS` and default to `.pdf,.docx,.txt,.md,.markdown,.html,.htm`. The maximum upload size is configured by `MAX_UPLOAD_SIZE_MB` and defaults to `50`.

Successful uploads write the original file under `STORAGE_DIR` with a relative key:

```text
documents/{project_id}/{document_id}/{safe_filename}
```

The `documents` table stores `document_role`, `title`, `file_name`, `file_type`, `file_size`, `storage_key`, `source_url`, `sha256`, content type metadata, and `parse_status=pending`. Full parsing is reserved for a later worker task.

Uploads support Unicode filenames, including Chinese policy filenames. The service stores a safe filename for the filesystem and preserves `metadata.original_filename` and `metadata.safe_filename` on the document record.

`GET /api/documents` lists database-backed document records and accepts optional `project_id`, `limit`, and `offset` query parameters. `GET /api/documents/{document_id}/download` streams the original file without exposing the server absolute path.

## Policies

- `GET /api/policies`
- `POST /api/policies/search`

Policy search returns mock policies with source and sha256 fields. Future implementation should combine keyword search, vector search, reranking, and policy source connectors.

## Analysis

- `POST /api/analysis/jobs`
- `GET /api/analysis/jobs/{job_id}`

Analysis jobs must keep factual boundaries:

- original facts from uploaded article
- retrieved facts from policy evidence
- model reasoning

## Exports

- `POST /api/exports/policy-originals`
- `POST /api/exports/report`

Policy original exports return a mock manifest and reserved bundle path.
Policy original export requests now create an `exports` table record before running the mock exporter. The mock exporter still writes only the reserved bundle structure and manifest.

## LLM

- `GET /api/llm/providers`
- `POST /api/llm/providers`
- `POST /api/llm/providers/{provider_id}/test`

Provider tests do not call external models in v0.1.
Provider listing returns built-in presets plus user providers stored in the database.

## Database-Backed Surfaces

The following API surfaces have light database integration:

- `GET /api/projects`
- `POST /api/projects`
- `GET /api/llm/providers`
- `POST /api/llm/providers`
- `POST /api/exports/policy-originals`
- `GET /api/documents`
- `POST /api/documents/upload`
- `GET /api/documents/{document_id}`
- `GET /api/documents/{document_id}/download`

Other endpoints may still return mock contracts while their downstream workflows are built.
