# Contributing

Thanks for helping build PolicyLens / 政研透镜.

## Development Principles

- Keep v0.1 changes small, explicit, and verifiable.
- Prefer stable interfaces over speculative abstractions.
- Keep citations, source metadata, evidence IDs, and timestamps in every business object that carries facts.
- Do not submit real API keys, `.env` files, private policy datasets, or user documents.
- Do not hard-code model names. Provider configuration should accept user-supplied model IDs.
- New API routes must include request and response schemas.
- Demo policy data must be clearly marked as fictional unless it is sourced and verified as a real public policy document.

## Local Setup

```bash
cd policy-lens
cp .env.example .env
docker compose up --build
```

For focused frontend work:

```bash
cd apps/web
npm install
npm run dev
```

For focused backend work:

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

## Pull Request Checklist

- API schemas are updated for any route change.
- Mock data remains realistic enough to guide future implementation.
- Documentation is updated when behavior or setup changes.
- No secrets are committed.
- Export-related changes preserve source, timestamp, and checksum fields.
- LLM output separates original facts, retrieved facts, and model reasoning.
- `bash scripts/check.sh` passes locally when the change affects backend, frontend, docs release artifacts, or API contracts.

## Extension Contributions

- Provider contributions should use environment-variable based credentials only.
- Parser contributions should include deterministic tests and clear unsupported-format errors.
- Exporter contributions should include `manifest.json`, relative paths, and checksum tests.
- Policy source contributions should preserve source URL, retrieval timestamp, content timestamp when available, and sha256 checksum.

## Reporting Issues

When filing an issue, include:

- Expected behavior
- Actual behavior
- Local environment or Docker Compose details
- Screenshots or API responses when useful
- Whether real policy data or mock data was used
