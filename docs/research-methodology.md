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
- The executor writes one `analysis_results` row with summary, claims, related policies, impact matrix, Markdown report, and `report_json`.

Default steps:

1. `parse_document_if_needed`
2. `collect_document_context`
3. `extract_article_signals`
4. `extract_claims`
5. `retrieve_policy_candidates`
6. `match_policy_sections`
7. `build_evidence_map`
8. `build_impact_matrix`
9. `summarize_findings`
10. `draft_markdown_report`

The current policy retrieval is SQL-backed keyword matching over local `policies` and `policy_sections`. It is not vector retrieval, embedding search, reranking, or RAG.

LLM use is optional and not required by the default path. CI tests must not call external model providers.

## Claim And Evidence Matching

Task 09 adds the first deterministic evidence chain:

```text
document_chunks -> claims -> policy_sections -> policy_matches -> analysis_results.report_json
```

Claims are extracted from article chunks with sentence and keyword rules. Policy matching scores claim keywords against current policy titles, issuers, jurisdictions, section headings, paths, and section content. Each `policy_match.evidence` preserves the claim quote, source chunk ids, policy section id, policy quote, matched terms, score components, and `fact_boundary=retrieved_fact`.

The evidence API exposes:

- `GET /api/analysis/jobs/{job_id}/claims`
- `GET /api/analysis/jobs/{job_id}/policy-matches`
- `GET /api/analysis/jobs/{job_id}/evidence`

This matching is not legal interpretation, RAG, embedding retrieval, or LLM reasoning. `model_reasoning` remains empty in the deterministic path.

## Impact Matrix And Report Draft

Task 10 adds deterministic impact matrix and Markdown report generation. Impact items are derived from claims, policy matches, and evidence maps, then persisted to `impact_items` with citations that include claim ids, policy match ids, source chunk ids, policy section ids, policy quotes, and matched terms.

The Markdown report draft is saved to `analysis_results.report_markdown`. Its outline is saved to `analysis_results.report_json.report_outline` with `generation_method=deterministic_rule_based` and `llm_used=false`.

The report and impact matrix are research aids only. They are not formal investment advice, legal advice, or a substitute for human policy review.

## v0.1 Scope

The current repository now supports upload, deterministic parsing, chunk storage, policy library ingestion, policy original export, LLM provider gateway configuration, synchronous Research Plan execution, a basic claim-policy evidence chain, deterministic impact matrix generation, and a Markdown report draft. Formal report export, LLM review, and richer impact modeling are future tasks.
