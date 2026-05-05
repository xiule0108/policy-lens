# Policy Export Draft

PolicyLens policy original export preserves traceability for downstream review.

## Export Modes

- `single_policy_full_text`
- `related_policy_bundle`
- `cited_sections_only`
- `evidence_bundle`
- `machine_readable_json`

## Bundle Structure

```text
policy_export_bundle.zip
  manifest.json
  policies/
  cited_sections/
  snapshots/
  mappings/
  checksums/
```

## Manifest Fields

The manifest should include:

- export ID
- export mode
- generated timestamp
- policy IDs
- cited section IDs
- source URL or source identifier
- retrieved timestamp
- published or effective timestamp when available
- sha256 checksums
- mappings between report claims, policy sections, and source files

## v0.1 Behavior

The current exporter creates a skeleton bundle directory and manifest. It does not fetch policy originals, generate archives, or write real policy text.

## Required Guarantees

Any future implementation must keep:

- source
- timestamp
- sha256
- citation mapping
- evidence mapping
