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

Other endpoints may still return mock contracts while their downstream workflows are built.
