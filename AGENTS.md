# AGENTS.md

This file gives Codex and other AI coding agents durable project rules for PolicyLens / 政研透镜.

## Project Goal

PolicyLens is an open-source policy and market research analysis workbench. It helps users parse research articles, retrieve related policies, inspect and export original policy text, generate policy impact matrices, and draft research reports with citation-aware evidence.

## Technical Stack

- Monorepo with `apps/`, `services/`, `packages/`, `infra/`, and `docs/`
- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Backend: FastAPI and Python
- Database: PostgreSQL
- Vector database: Qdrant
- Object storage: local filesystem for v0.1, MinIO reserved
- Worker: Python worker skeleton
- LLM Gateway: LiteLLM / OpenAI-compatible Provider Adapter reserved
- Deployment: Docker Compose

## Code Style

- Keep v0.1 code small, typed, and easy to replace.
- Prefer explicit schemas and plain service boundaries.
- Use realistic mock data when real integrations are not implemented.
- Do not introduce large business workflows before the API and data contracts are stable.
- Preserve existing public interfaces unless a task explicitly changes them.

## Security And Secrets

- Never hard-code API keys, access tokens, private endpoints, cookies, or credentials.
- Never commit `.env` or files derived from private local environments.
- Use `.env.example` for documented variable names only.
- Provider model names must be user-configurable, not hard-coded as product defaults.

## API Rules

- Every new API route must have request and response schemas.
- Business objects should include `citation`, `source`, or `evidence` fields when they carry factual claims.
- Routes may return mock data in v0.1, but the shape should be close to the intended production contract.

## Evidence And Citation Rules

- All business workflows must preserve citation, source, and evidence fields.
- Policy original export must preserve source, retrieval timestamp, content timestamp when available, and sha256 checksum.
- Export bundles should include manifest, policy files, cited sections, snapshots, mappings, and checksums.

## LLM Output Rules

LLM outputs must separate:

- Original facts from the uploaded source article
- Retrieved facts from policy search or external evidence
- Model reasoning and interpretation

Do not mix these categories into a single untraceable answer.

## Scope Guard

For v0.1 tasks, do not implement full parsing, production retrieval, model orchestration, user auth, billing, or policy crawling unless explicitly requested. Keep changes focused on the requested skeleton and contracts.
