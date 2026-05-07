# Policy Export

PolicyLens exports normalized policy originals and evidence data from the local policy library. The exporter reads `policies`, `policy_versions`, and `policy_sections`; it does not crawl remote policy sources or copy uploaded source files into the bundle.

## API

- `POST /api/exports/policy-originals`
- `GET /api/exports/{export_id}`
- `GET /api/exports/{export_id}/download`

Exports are synchronous in the v0.1 API process. The export record is created as `running`, then moves to `completed` or `failed`. Failed records keep a short error summary in `manifest.error`; tracebacks are not stored.

## Export Modes

- `single_policy_full_text`: one policy current version, full normalized text, sections, metadata
- `related_policy_bundle`: multiple policy current versions in one bundle
- `cited_sections_only`: only requested `policy_sections`
- `evidence_bundle`: policy, version, section, source, timestamp, and sha256 evidence data
- `machine_readable_json`: structured `policies.json`, `versions.json`, and `sections.json`

Supported policy file formats are `markdown`, `txt`, `html`, and `json`.

Mode-specific request rules:

- `single_policy_full_text`: exactly one `policy_id`, no `cited_section_ids`, and at least one format
- `related_policy_bundle`: at least one `policy_id` and at least one format
- `cited_sections_only`: at least one `cited_section_id` and no `policy_ids`
- `evidence_bundle`: at least one `policy_id` or `cited_section_id`
- `machine_readable_json`: at least one `policy_id` or `cited_section_id`

## Bundle Structure

```text
policy_export_bundle.zip
  manifest.json

  policies/
    {policy_id}/
      policy.md
      policy.txt
      policy.html
      policy.json

  cited_sections/
    cited_sections.md
    cited_sections.json

  evidence/
    evidence_bundle.md
    evidence_bundle.json

  machine_readable/
    policies.json
    versions.json
    sections.json

  checksums/
    sha256.txt
```

Only files required by the selected mode and formats are written. `snapshots/` is not generated in v0.1 because the database does not yet store raw web or PDF snapshots. When requested, `manifest.json` records `snapshot_status=not_available_in_v0.1`.

## Manifest

`manifest.json` includes:

- `export_id`
- `export_type`
- `mode`
- `generated_at`
- `project_id`
- `formats`
- `policy_count`
- `section_count`
- `policies`
- `cited_sections`
- `checksums`
- `snapshot_status`

Each policy manifest entry records `policy_id`, `version_id`, `title`, `source_url`, `sha256`, and generated file paths. Each cited section entry records section, policy, version, heading, order, and source metadata.

## Checksums

`checksums/sha256.txt` contains one SHA-256 line for each generated file except `sha256.txt` itself:

```text
<sha256>  manifest.json
<sha256>  policies/{policy_id}/policy.md
```

The checksum file uses relative ZIP paths only.

## Storage

The ZIP is written below `STORAGE_DIR`:

```text
{STORAGE_DIR}/exports/{export_id}/policy_export_bundle.zip
```

The database stores only this relative key:

```text
exports/{export_id}/policy_export_bundle.zip
```

## Current Limits

The exporter does not generate DOCX, PDF, PPT, or research reports. It does not run RAG, embeddings, LLMs, policy association analysis, or legal validity checks.
