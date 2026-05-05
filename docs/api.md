# API Draft

The FastAPI service is mounted under `/api`.

## Health

- `GET /api/health`

Returns service status and mock dependency states.

## Projects

- `GET /api/projects`
- `POST /api/projects`

Projects represent research workspaces. v0.1 uses mock persistence.

## Documents

- `GET /api/documents`
- `POST /api/documents/upload`

The upload route accepts a JSON contract in v0.1. Future versions can replace the transport with multipart upload while preserving document, source, citation, and evidence fields.

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

## LLM

- `GET /api/llm/providers`
- `POST /api/llm/providers`
- `POST /api/llm/providers/{provider_id}/test`

Provider tests do not call external models in v0.1.
