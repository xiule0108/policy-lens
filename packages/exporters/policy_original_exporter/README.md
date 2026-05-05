# Policy Original Exporter

This package reserves the policy original export surface for v0.1.

Supported export modes:

- `single_policy_full_text`
- `related_policy_bundle`
- `cited_sections_only`
- `evidence_bundle`
- `machine_readable_json`

Target bundle:

```text
policy_export_bundle.zip
  manifest.json
  policies/
  cited_sections/
  snapshots/
  mappings/
  checksums/
```

Every real exporter implementation must preserve source, retrieval timestamp, content timestamp when available, and sha256 checksum.
