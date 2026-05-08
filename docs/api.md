# API Reference

The FastAPI service is mounted under `/api`.

Current release candidate: `v0.1.0-alpha`.

## Health

- `GET /api/health`

Returns service status, API version, and dependency status summaries.

## Projects

- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{project_id}`

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

`POST /api/policies/search` searches database policies by keyword. `jurisdictions` and `policy_types` are applied in the database query before `limit`, so filtered results are not dropped by an earlier broad keyword cap. This is a simple SQL-backed search surface for v0.1, not RAG, embeddings, Qdrant, or reranking.

`GET /api/policies/{policy_id}` returns policy metadata plus `current_version_id`.

`GET /api/policies/{policy_id}/versions` returns policy versions ordered by capture time descending.

`GET /api/policies/{policy_id}/sections` returns the current version's sections by default. Pass `version_id` to inspect a specific version.

`GET /api/policies/{policy_id}/original` returns the current version's normalized policy text and metadata for viewing. Use `POST /api/exports/policy-originals` when a ZIP bundle is needed.

This task does not crawl policies, judge policy legal validity, or perform policy relevance analysis.

## Analysis

- `POST /api/analysis/jobs`
- `GET /api/analysis/jobs`
- `GET /api/analysis/jobs/{job_id}`
- `GET /api/analysis/jobs/{job_id}/steps`
- `GET /api/analysis/jobs/{job_id}/plan`
- `GET /api/analysis/jobs/{job_id}/result`
- `GET /api/analysis/jobs/{job_id}/claims`
- `GET /api/analysis/jobs/{job_id}/policy-matches`
- `GET /api/analysis/jobs/{job_id}/evidence`
- `GET /api/analysis/jobs/{job_id}/impact-matrix`
- `GET /api/analysis/jobs/{job_id}/report`

`POST /api/analysis/jobs` creates an `analysis_jobs` row, builds a Research Plan, and executes it synchronously in v0.1. The request requires a project UUID and at least one document UUID. The current implementation uses the first document only.

Request fields:

- `project_id`: project UUID
- `document_ids`: at least one document UUID
- `analysis_types`: defaults to `policy_deep_dive`
- `model_profile`: defaults to `china_balanced`
- `use_llm`, `provider_id`, `model`: reserved for optional LLM summary paths; deterministic execution is the default

The default plan runs:

- `parse_document_if_needed`
- `collect_document_context`
- `extract_article_signals`
- `extract_claims`
- `retrieve_policy_candidates`
- `match_policy_sections`
- `build_evidence_map`
- `build_impact_matrix`
- `summarize_findings`
- `draft_markdown_report`

The executor records a `research_plan` step, then records each step as `running`, `done`, `skipped`, or `failed`. Jobs move through `queued`, `running`, `completed`, or `failed`. Failed jobs store a short error summary without a traceback.

`GET /api/analysis/jobs?project_id={project_id}&limit=50&offset=0` lists jobs. If `project_id` is supplied, it must be a valid project UUID and must exist. If it is omitted, the API returns recent jobs. Each job response includes `result_id` when an analysis result exists.

Analysis job route parameters are UUIDs. Malformed job IDs return `422`; well-formed but unknown job IDs return `404`.

`GET /api/analysis/jobs/{job_id}/steps` returns persisted `analysis_steps`.

`GET /api/analysis/jobs/{job_id}/plan` returns the plan stored in the `research_plan` step.

`GET /api/analysis/jobs/{job_id}/result` returns the latest `analysis_results` row for the job.

`GET /api/analysis/jobs/{job_id}/claims` returns deterministic claims persisted in the `claims` table for the job document.

`GET /api/analysis/jobs/{job_id}/policy-matches` returns `policy_matches` tied to the job's `analysis_results` row.

`GET /api/analysis/jobs/{job_id}/evidence` returns `report_json.claim_policy_map` and `report_json.fact_boundaries`.

`GET /api/analysis/jobs/{job_id}/impact-matrix` returns persisted `impact_items` tied to the job's `analysis_results` row.
Each impact item citation keeps the evidence chain identifiers: `claim_id`, `policy_match_id`, `policy_section_id`, `source_chunk_ids`, and `policy_quote` when available.

`GET /api/analysis/jobs/{job_id}/report` returns `analysis_results.report_markdown`, `report_json.report_outline`, and factual boundaries.

Analysis results keep factual boundaries:

- original facts from uploaded article
- retrieved facts from policy evidence
- model reasoning

The v0.1 evidence chain is rule based:

```text
document chunk -> claim -> policy section -> policy_match -> evidence map
```

It uses deterministic sentence and keyword rules plus SQL-backed policy section matching. Impact matrix and Markdown report generation are also rule based. They are not Qdrant, embedding retrieval, RAG, reranking, LLM judgment, legal advice, or investment advice. `model_reasoning` stays empty in the default path.

## Exports

- `POST /api/exports/policy-originals`
- `POST /api/exports/report`
- `GET /api/exports/{export_id}`
- `GET /api/exports/{export_id}/download`

`POST /api/exports/policy-originals` creates a real local ZIP bundle from policy library records. It supports these modes:

- `single_policy_full_text`
- `related_policy_bundle`
- `cited_sections_only`
- `evidence_bundle`
- `machine_readable_json`

Request fields:

- `project_id`: optional project UUID for export tracking
- `policy_ids`: policy UUIDs to export
- `cited_section_ids`: policy section UUIDs to export
- `mode`: export mode
- `formats`: any of `markdown`, `txt`, `html`, `json`
- `include_snapshots`: records snapshot intent in `manifest.json`; raw snapshots are not available in v0.1
- `include_sections`: includes section text in policy files
- `include_checksums`: writes `checksums/sha256.txt`

Mode-specific request rules:

- `single_policy_full_text`: exactly one `policy_id`, no `cited_section_ids`, and at least one format
- `related_policy_bundle`: at least one `policy_id` and at least one format
- `cited_sections_only`: at least one `cited_section_id` and no `policy_ids`
- `evidence_bundle`: at least one `policy_id` or `cited_section_id`
- `machine_readable_json`: at least one `policy_id` or `cited_section_id`

Created exports move through `running`, `completed`, or `failed`. Successful records store only the relative ZIP key, for example `exports/{export_id}/policy_export_bundle.zip`.

`GET /api/exports/{export_id}` returns the export record, formats, storage key, manifest, timestamps, and status.

`POST /api/exports/report` creates a real local ZIP bundle from an existing `analysis_results` row. Use either `analysis_id` or `job_id`; `analysis_id` takes priority when both are present.

Request fields:

- `project_id`: optional project UUID for export tracking
- `job_id`: optional analysis job UUID
- `analysis_id`: optional analysis result UUID
- `formats`: any of `markdown`, `json`, `html`
- `report_format`: legacy single-format field, converted to `formats` when `formats` is omitted
- `include_evidence_bundle`: include `evidence/evidence.json`
- `include_impact_matrix`: include `impact_matrix/impact_matrix.json`
- `include_policy_matches`: include `policy_matches/policy_matches.json`

Unsupported formats such as `docx`, `pdf`, or `ppt` return `422`. An empty or missing source returns `422`; missing jobs or analysis results return `404`; an analysis result without `report_markdown` returns `422`.

Report export bundle structure:

```text
report_export_bundle.zip
  manifest.json
  reports/
    report.md
    report.html
    report.json
  evidence/
    evidence.json
  impact_matrix/
    impact_matrix.json
  policy_matches/
    policy_matches.json
  checksums/
    sha256.txt
```

The database stores only the relative ZIP key, for example `exports/{export_id}/report_export_bundle.zip`.

`GET /api/exports/{export_id}/download` streams completed ZIP exports. Download filenames are based on export type:

- `policy_originals`: `policy_export_{export_id}.zip`
- `report`: `report_export_{export_id}.zip`
- other export types: `export_{export_id}.zip`

The download endpoint returns `409` if the export is not completed and never exposes the server absolute path.

The v0.1 report exporter is deterministic and does not produce PPT, DOCX, or PDF files.

## LLM

- `GET /api/llm/providers`
- `POST /api/llm/providers`
- `POST /api/llm/providers/{provider_id}/test`
- `POST /api/llm/chat`

Provider listing returns built-in presets plus user providers stored in the database. Responses include `api_key_env` and `api_key_configured`, but never include API key values.

When a database provider overrides a built-in preset and does not set `api_key_env`, the preset env var is inherited. For example, a `deepseek` config with only `base_url` and `model_name` still uses `DEEPSEEK_API_KEY`.

`POST /api/llm/providers` upserts a provider config. Store only:

- `provider_id`
- `display_name`
- `provider_family`
- `base_url`
- `api_key_env`
- `model_name`
- `enabled`
- `openai_compatible`
- `local_provider`

`POST /api/llm/providers/{provider_id}/test` makes a real OpenAI-compatible `/chat/completions` call when the provider is configured. If `model` is omitted, the API uses `provider.config.model_name`. Missing `base_url`, missing model, or missing API key environment variable returns `422`. Upstream HTTP and response format errors return `502`. CI tests mock this path and do not call external models.

`POST /api/llm/chat` accepts:

- `provider_id`
- optional `model`
- `messages` with `system`, `user`, or `assistant` roles
- `temperature`
- optional `max_tokens`
- `timeout_seconds`
- optional `job_id`

If `job_id` is provided and `log_step=true`, the API validates the analysis job before calling the model, then writes a lightweight `analysis_steps` record after a successful call. An unknown `job_id` returns `404` and does not call the model. Without `job_id`, or with `log_step=false`, the API returns token usage and latency without writing a log row.

## Database-Backed Surfaces

The following API surfaces have light database integration:

- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{project_id}`
- `GET /api/llm/providers`
- `POST /api/llm/providers`
- `POST /api/exports/policy-originals`
- `POST /api/exports/report`
- `GET /api/exports/{export_id}`
- `GET /api/exports/{export_id}/download`
- `POST /api/analysis/jobs`
- `GET /api/analysis/jobs`
- `GET /api/analysis/jobs/{job_id}`
- `GET /api/analysis/jobs/{job_id}/steps`
- `GET /api/analysis/jobs/{job_id}/plan`
- `GET /api/analysis/jobs/{job_id}/result`
- `GET /api/analysis/jobs/{job_id}/claims`
- `GET /api/analysis/jobs/{job_id}/policy-matches`
- `GET /api/analysis/jobs/{job_id}/evidence`
- `GET /api/analysis/jobs/{job_id}/impact-matrix`
- `GET /api/analysis/jobs/{job_id}/report`
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
