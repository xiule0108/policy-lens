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
- `POST /api/documents/{document_id}/parse`
- `GET /api/documents/{document_id}/chunks`
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

The `documents` table stores `document_role`, `title`, `file_name`, `file_type`, `file_size`, `storage_key`, `source_url`, `sha256`, content type metadata, and `parse_status=pending`.

Uploads support Unicode filenames, including Chinese policy filenames. The service stores a safe filename for the filesystem and preserves `metadata.original_filename` and `metadata.safe_filename` on the document record.

`GET /api/documents` lists database-backed document records and accepts optional `project_id`, `limit`, and `offset` query parameters. `GET /api/documents/{document_id}/download` streams the original file without exposing the server absolute path.

`POST /api/documents/{document_id}/parse` synchronously runs the basic parser and replaces old chunks for the document. Supported formats are `.txt`, `.md`, `.markdown`, `.html`, `.htm`, `.docx`, and searchable `.pdf`. OCR is not supported; scanned PDFs or files with no extractable text return `422` and set `parse_status=failed`.

Parser status values:

- `pending`: uploaded but not parsed
- `parsing`: parser is currently running
- `parsed`: chunks were written to `document_chunks`
- `failed`: parsing failed and `metadata.parse_error` contains a short error summary

Successful parsing updates `documents.language`, `documents.page_count`, and `metadata.parse_summary`, and clears any previous `metadata.parse_error`. Failed parsing records a short `metadata.parse_error` summary. The basic language detector only distinguishes likely `zh-CN`, likely `en`, or unknown.

`GET /api/documents/{document_id}/chunks?limit=200&offset=0` returns:

- `items`: chunk records ordered by `chunk_index`
- `total`: total chunk count for the document

Chunking uses deterministic block order, filters empty text, splits long blocks by `CHUNK_MAX_CHARS` with a default of `2000`, preserves page and section metadata, and stores a rough `token_count` estimate.

## Policies

- `POST /api/policies/from-document`
- `GET /api/policies`
- `POST /api/policies/search`
- `GET /api/policies/{policy_id}`
- `GET /api/policies/{policy_id}/versions`
- `GET /api/policies/{policy_id}/sections`
- `GET /api/policies/{policy_id}/original`

`POST /api/policies/from-document` creates local policy library records from a parsed policy document. Requirements:

- source document exists
- `document_role=policy`
- `parse_status=parsed`
- `storage_key` is present
- at least one `document_chunks` row exists

The request accepts policy metadata such as `title`, `issuer`, `issuer_level`, `jurisdiction`, `policy_type`, policy dates, `status`, `version_label`, optional target `policy_id`, and `force_new_version`.

Behavior:

- Without `policy_id`, ingestion creates a new `policies` row, one current `policy_versions` row, and `policy_sections` copied from document chunks.
- With `policy_id`, ingestion creates a new current version for the existing policy and marks older versions as not current.
- If the same document has already been ingested, the API returns the existing ingestion result by default.
- If `force_new_version=true`, the API creates a new current version for the same policy.

`GET /api/policies` returns database policies and supports `query`, `jurisdiction`, `issuer`, `policy_type`, `status`, `limit`, and `offset`.

`POST /api/policies/search` searches database policies by keyword. This is a simple SQL-backed search surface for v0.1, not RAG, embeddings, Qdrant, or reranking.

`GET /api/policies/{policy_id}` returns policy metadata plus `current_version_id`.

`GET /api/policies/{policy_id}/versions` returns policy versions ordered by capture time descending.

`GET /api/policies/{policy_id}/sections` returns the current version's sections by default. Pass `version_id` to inspect a specific version.

`GET /api/policies/{policy_id}/original` returns the current version's normalized policy text and metadata for viewing. It does not create a ZIP export bundle.

This task does not crawl policies, judge policy legal validity, perform policy relevance analysis, or export original policy ZIP files.

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
- `GET /api/policies`
- `POST /api/policies/from-document`
- `POST /api/policies/search`
- `GET /api/policies/{policy_id}`
- `GET /api/policies/{policy_id}/versions`
- `GET /api/policies/{policy_id}/sections`
- `GET /api/policies/{policy_id}/original`
- `GET /api/documents`
- `POST /api/documents/upload`
- `GET /api/documents/{document_id}`
- `POST /api/documents/{document_id}/parse`
- `GET /api/documents/{document_id}/chunks`
- `GET /api/documents/{document_id}/download`

Other endpoints may still return mock contracts while their downstream workflows are built.
