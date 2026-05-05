from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import hashlib
import json


ExportMode = Literal[
    "single_policy_full_text",
    "related_policy_bundle",
    "cited_sections_only",
    "evidence_bundle",
    "machine_readable_json",
]

EXPORT_MODES: tuple[str, ...] = (
    "single_policy_full_text",
    "related_policy_bundle",
    "cited_sections_only",
    "evidence_bundle",
    "machine_readable_json",
)

BUNDLE_STRUCTURE: list[str] = [
    "manifest.json",
    "policies/",
    "cited_sections/",
    "snapshots/",
    "mappings/",
    "checksums/",
]


@dataclass(frozen=True)
class MockPolicyExportResult:
    bundle_path: Path
    manifest: dict


def create_mock_policy_export_bundle(
    *,
    export_id: str,
    mode: ExportMode,
    policy_ids: list[str],
    cited_section_ids: list[str],
    output_root: Path,
    include_snapshots: bool,
) -> MockPolicyExportResult:
    """Create a traceable skeleton bundle directory for policy originals.

    v0.1 intentionally does not fetch or package real policy originals. It only
    creates the manifest and directory contract that future exporters must keep.
    """
    if mode not in EXPORT_MODES:
        raise ValueError(f"Unsupported export mode: {mode}")

    generated_at = datetime.now(timezone.utc).isoformat()
    bundle_path = output_root / "exports" / export_id / "policy_export_bundle"
    for child in ["policies", "cited_sections", "snapshots", "mappings", "checksums"]:
        (bundle_path / child).mkdir(parents=True, exist_ok=True)

    manifest = {
        "export_id": export_id,
        "mode": mode,
        "generated_at": generated_at,
        "bundle_structure": BUNDLE_STRUCTURE,
        "policy_ids": policy_ids,
        "cited_section_ids": cited_section_ids,
        "include_snapshots": include_snapshots,
        "policies": [
            {
                "policy_id": policy_id,
                "source": None,
                "retrieved_at": generated_at,
                "published_at": None,
                "sha256": _mock_checksum(export_id, policy_id),
                "path": f"policies/{policy_id}.txt",
                "status": "reserved_mock",
            }
            for policy_id in policy_ids
        ],
        "checksums": {
            "algorithm": "sha256",
            "manifest_sha256": "",
        },
    }
    manifest["checksums"]["manifest_sha256"] = _manifest_checksum(manifest)

    manifest_path = bundle_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return MockPolicyExportResult(bundle_path=bundle_path, manifest=manifest)


def _mock_checksum(export_id: str, value: str) -> str:
    return hashlib.sha256(f"{export_id}:{value}".encode("utf-8")).hexdigest()


def _manifest_checksum(manifest: dict) -> str:
    checksum_manifest = dict(manifest)
    checksum_manifest["checksums"] = dict(manifest["checksums"])
    checksum_manifest["checksums"]["manifest_sha256"] = ""
    encoded = json.dumps(checksum_manifest, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
