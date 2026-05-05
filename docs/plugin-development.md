# Plugin Development Draft

PolicyLens will support extensions for parsers, retrievers, policy sources, exporters, and model providers.

## Extension Points

- `packages/parsers`
- `packages/retrievers`
- `packages/connectors/policy_sources`
- `packages/connectors/llm`
- `packages/connectors/storage`
- `packages/exporters`

## v0.1 Rule

Plugins should be plain Python packages or TypeScript packages with explicit contracts. Do not add runtime plugin loading until a stable interface exists.

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
