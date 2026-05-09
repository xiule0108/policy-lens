# Plugin Development

PolicyLens will support extensions for parsers, retrievers, policy sources, exporters, and model providers.

## Extension Points

- `packages/parsers`
- `packages/retrievers`
- `packages/connectors/policy_sources`
- `packages/connectors/llm`
- `packages/connectors/storage`
- `packages/exporters`
- `services/api/app/services`

## v0.1 Rule

Plugins should be plain Python packages or TypeScript packages with explicit contracts. Do not add runtime plugin loading until a stable interface exists.

For v0.1.0-alpha, contributors should extend existing service boundaries before adding dynamic plugin loading:

- Parser contributions should preserve source filename, content type, parse status, page/section metadata, and deterministic failure errors.
- Provider contributions should use OpenAI-compatible configuration where possible and store only `api_key_env`, never API key values.
- Exporter contributions should write manifest files, relative paths, and checksums.
- Policy source contributions should clearly separate real official sources from demo or fixture data.

## Metadata

Future plugins should declare:

- name
- version
- supported input and output schemas
- external permissions
- network behavior
- secret requirements
- citation and evidence behavior

## Safety

Plugins must not bypass source, citation, and evidence preservation. Any plugin that downloads policy originals must write source URL, retrieval timestamp, and sha256 checksum.

Third-party plugin code should document network behavior, required secrets, and whether it may persist user documents.
