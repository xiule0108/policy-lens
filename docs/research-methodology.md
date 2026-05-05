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

## v0.1 Scope

The current repository only supplies layout, API contracts, and mock data. Research logic will be implemented after parsers, retrievers, and evidence schemas are stable.
