# PolicyLens v0.1.0-alpha Release Notes

PolicyLens / 政研透镜 is an open-source policy and market research workbench for parsing research articles, managing a local policy library, building auditable evidence chains, and exporting policy originals and research draft bundles.

## What This Alpha Can Do

- Create research projects in the Web workbench or through the API.
- Upload research articles, policy files, and appendices.
- Parse `.txt`, `.md`, `.markdown`, `.html`, `.htm`, `.docx`, and searchable `.pdf` files into `document_chunks`.
- Ingest parsed policy documents into `policies`, `policy_versions`, and `policy_sections`.
- Run a synchronous deterministic Research Plan over a research article.
- Extract basic claims, match them to policy sections, and persist `policy_matches`.
- Build an evidence map, impact matrix, and Markdown report draft.
- Export policy original ZIP bundles with manifest and SHA-256 checksums.
- Export report ZIP bundles with Markdown, JSON, HTML, evidence, impact matrix, policy matches, manifest, and checksums.
- Configure OpenAI-compatible LLM providers without storing API key values.

## Quick Start

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

## Demo Workflow

With the API running, execute:

```bash
python3 scripts/e2e_demo.py
```

The script creates a demo project, uploads a fictional policy and research article, parses both files, ingests the policy, runs analysis, inspects evidence and impact matrix outputs, and creates both report and policy original exports.

## Current Limits

- No OCR for scanned PDFs.
- No Qdrant, embedding, reranking, or RAG yet.
- No policy crawler or official-source sync.
- No production authentication, authorization, billing, audit, or team workflow.
- No streaming model calls.
- No PPT, DOCX, or PDF report export.
- The analysis, impact matrix, and report draft are deterministic and require human review.

## Security And Privacy

- Do not commit `.env` files or API keys.
- LLM Provider records store environment variable names only, never secret values.
- Uploaded files and export bundles are stored under `STORAGE_DIR`.
- Demo policy data in `examples/` is fictional and is not an official policy source.

## Roadmap

Next planned work includes manual v0.1.0-alpha release validation, screenshots, release tagging, richer front-end review surfaces, optional LLM review, better policy matching, RAG/embedding integration, report export enhancements, and production hardening.
