# Research Methodology Draft

PolicyLens should support research workflows that remain auditable.

## Fact Boundaries

All generated analysis should keep three categories separate:

- original facts from uploaded documents
- retrieved facts from policy search and external evidence
- model reasoning and interpretation

## Evidence Chain

Every material claim should point to evidence:

- source article section
- policy original section
- retrieved policy metadata
- export bundle mapping
- checksum when source files are exported

## Policy Impact Matrix

The impact matrix should connect:

- policy instrument
- affected market variable
- direction of impact
- expected intensity
- confidence
- evidence IDs

## Market Transmission Chain

Transmission chain analysis should preserve:

- policy action
- institutional channel
- enterprise behavior
- supply and demand response
- market price or quantity effect
- risk and uncertainty factors

## Research Plan Engine

Task 08 introduces a synchronous Research Plan execution engine. It is intentionally deterministic and auditable:

- `POST /api/analysis/jobs` creates an `analysis_jobs` row.
- The plan builder writes a `research_plan` step with the full plan JSON.
- The executor runs each step in order and persists `analysis_steps`.
- The executor writes one `analysis_results` row with summary, claims, related policies, empty impact matrix, and `report_json`.

Default steps:

1. `parse_document_if_needed`
2. `collect_document_context`
3. `extract_article_signals`
4. `retrieve_policy_candidates`
5. `summarize_findings`

The current policy retrieval is SQL-backed keyword matching over local `policies` and `policy_sections`. It is not vector retrieval, embedding search, reranking, or RAG.

LLM use is optional and not required by the default path. CI tests must not call external model providers.

## v0.1 Scope

The current repository now supports upload, deterministic parsing, chunk storage, policy library ingestion, policy original export, LLM provider gateway configuration, and a synchronous Research Plan execution skeleton. Full policy matching, impact matrix generation, and formal report generation are future tasks.
