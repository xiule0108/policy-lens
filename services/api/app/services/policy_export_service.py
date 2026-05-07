from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import html
import json
from pathlib import Path
from uuid import UUID
import zipfile

from sqlalchemy.orm import Session

from app.db.config import settings
from app.db.models import Policy, PolicySection, PolicyVersion
from app.repositories.exports import create_export, update_export_status
from app.repositories.policies import get_policy
from app.repositories.policy_sections import get_policy_section, list_policy_sections
from app.repositories.policy_versions import get_current_policy_version, get_policy_version
from app.schemas.common import EvidenceItem, PolicyOriginalExportRequest, ExportResponse
from app.services.storage_service import ensure_child_path


POLICY_FILE_MODES = {"single_policy_full_text", "related_policy_bundle"}
CHECKSUM_PATH = "checksums/sha256.txt"


class PolicyExportError(Exception):
    """Base class for policy export failures."""


class PolicyExportValidationError(PolicyExportError):
    """Raised when an export request is internally inconsistent."""


class PolicyExportNotFoundError(PolicyExportError):
    """Raised when a requested policy, version, or section does not exist."""


class PolicyExportCurrentVersionError(PolicyExportError):
    """Raised when a policy has no current version."""


@dataclass(frozen=True)
class ExportPolicyRecord:
    policy: Policy
    version: PolicyVersion
    sections: list[PolicySection]


@dataclass(frozen=True)
class PolicyExportResult:
    export_id: str
    storage_key: str
    absolute_path: Path
    manifest: dict
    status: str


def create_policy_original_export(
    session: Session,
    payload: PolicyOriginalExportRequest,
) -> ExportResponse:
    validate_export_request(payload)
    db_export = create_export(
        session,
        {
            "project_id": payload.project_id,
            "export_type": "policy_originals",
            "status": "running",
            "formats": list(payload.formats),
            "manifest": {
                "mode": payload.mode,
                "policy_ids": [str(policy_id) for policy_id in payload.policy_ids],
                "cited_section_ids": [str(section_id) for section_id in payload.cited_section_ids],
            },
        },
    )
    try:
        policy_records, cited_sections = collect_export_data(session, payload)
        result = write_policy_export_bundle(
            export_id=str(db_export.id),
            storage_root=Path(settings.storage_dir),
            payload=payload,
            policy_records=policy_records,
            cited_sections=cited_sections,
        )
    except Exception as exc:
        update_export_status(
            session,
            db_export.id,
            "failed",
            manifest={
                **(db_export.manifest or {}),
                "error": {
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                },
            },
        )
        raise

    db_export = update_export_status(
        session,
        db_export.id,
        "completed",
        storage_key=result.storage_key,
        manifest=result.manifest,
    )
    return ExportResponse(
        export_id=str(db_export.id),
        status=db_export.status,
        mode=payload.mode,
        bundle_path=result.storage_key,
        manifest=result.manifest,
        evidence=[
            EvidenceItem(
                id=f"{db_export.id}_manifest",
                source_type="policy_export_manifest",
                summary="Policy original export bundle generated from policy library records.",
                confidence=1.0,
            )
        ],
    )


def validate_export_request(payload: PolicyOriginalExportRequest) -> None:
    has_policy_ids = bool(payload.policy_ids)
    has_section_ids = bool(payload.cited_section_ids)
    if not has_policy_ids and not has_section_ids:
        raise PolicyExportValidationError("policy_ids or cited_section_ids must be provided.")
    if payload.mode == "single_policy_full_text":
        if len(payload.policy_ids) != 1:
            raise PolicyExportValidationError("single_policy_full_text requires exactly one policy_id.")
        if has_section_ids:
            raise PolicyExportValidationError("single_policy_full_text does not accept cited_section_ids.")
        if not payload.formats:
            raise PolicyExportValidationError("single_policy_full_text requires at least one format.")
    if payload.mode == "related_policy_bundle":
        if not has_policy_ids:
            raise PolicyExportValidationError("related_policy_bundle requires policy_ids.")
        if not payload.formats:
            raise PolicyExportValidationError("related_policy_bundle requires at least one format.")
    if payload.mode == "cited_sections_only":
        if not has_section_ids:
            raise PolicyExportValidationError("cited_sections_only requires cited_section_ids.")
        if has_policy_ids:
            raise PolicyExportValidationError("cited_sections_only does not accept policy_ids.")


def collect_export_data(
    session: Session,
    payload: PolicyOriginalExportRequest,
) -> tuple[list[ExportPolicyRecord], list[PolicySection]]:
    policy_records: dict[str, ExportPolicyRecord] = {}
    cited_sections: list[PolicySection] = []

    for policy_id in dedupe_ids(payload.policy_ids):
        record = load_policy_record(session, policy_id)
        policy_records[str(record.policy.id)] = record

    for section_id in dedupe_ids(payload.cited_section_ids):
        section = get_policy_section(session, section_id)
        if section is None:
            raise PolicyExportNotFoundError(f"Policy section not found: {section_id}")
        cited_sections.append(section)
        policy_key = str(section.policy_id)
        if policy_key not in policy_records:
            policy = get_policy(session, section.policy_id)
            version = get_policy_version(session, section.version_id)
            if policy is None or version is None:
                raise PolicyExportNotFoundError("Policy or version for cited section was not found.")
            sections = list_policy_sections(session, policy.id, version_id=version.id, limit=100_000)
            policy_records[policy_key] = ExportPolicyRecord(policy=policy, version=version, sections=sections)

    return list(policy_records.values()), cited_sections


def load_policy_record(session: Session, policy_id: UUID | str) -> ExportPolicyRecord:
    policy = get_policy(session, policy_id)
    if policy is None:
        raise PolicyExportNotFoundError(f"Policy not found: {policy_id}")
    version = get_current_policy_version(session, policy.id)
    if version is None:
        raise PolicyExportCurrentVersionError(f"Policy has no current version: {policy_id}")
    sections = list_policy_sections(session, policy.id, version_id=version.id, limit=100_000)
    return ExportPolicyRecord(policy=policy, version=version, sections=sections)


def write_policy_export_bundle(
    *,
    export_id: str,
    storage_root: Path,
    payload: PolicyOriginalExportRequest,
    policy_records: list[ExportPolicyRecord],
    cited_sections: list[PolicySection],
) -> PolicyExportResult:
    generated_at = datetime.now(timezone.utc).isoformat()
    files: dict[str, bytes] = {}
    policy_paths: dict[str, dict[str, str]] = {}

    if payload.mode in POLICY_FILE_MODES:
        for record in policy_records:
            paths = build_policy_files(record, payload.formats, payload.include_sections)
            policy_paths[str(record.policy.id)] = {format_name: path for format_name, path, _content in paths}
            for _format_name, path, content in paths:
                files[path] = content

    if payload.mode == "cited_sections_only" or cited_sections:
        files["cited_sections/cited_sections.json"] = json_bytes(build_sections_payload(cited_sections))
        files["cited_sections/cited_sections.md"] = markdown_bytes(render_cited_sections_markdown(cited_sections))

    if payload.mode == "evidence_bundle":
        evidence_payload = build_evidence_payload(policy_records, cited_sections, generated_at)
        files["evidence/evidence_bundle.json"] = json_bytes(evidence_payload)
        files["evidence/evidence_bundle.md"] = markdown_bytes(render_evidence_markdown(evidence_payload))

    if payload.mode == "machine_readable_json":
        machine_payload = build_machine_readable_payload(policy_records)
        files["machine_readable/policies.json"] = json_bytes(machine_payload["policies"])
        files["machine_readable/versions.json"] = json_bytes(machine_payload["versions"])
        files["machine_readable/sections.json"] = json_bytes(machine_payload["sections"])

    manifest = build_manifest(
        export_id=export_id,
        payload=payload,
        generated_at=generated_at,
        policy_records=policy_records,
        cited_sections=cited_sections,
        policy_paths=policy_paths,
    )
    files["manifest.json"] = json_bytes(manifest)

    if payload.include_checksums:
        files[CHECKSUM_PATH] = render_checksums(files)

    absolute_path, storage_key = write_zip_file(storage_root, export_id, files)
    return PolicyExportResult(
        export_id=export_id,
        storage_key=storage_key,
        absolute_path=absolute_path,
        manifest=manifest,
        status="completed",
    )


def build_policy_files(
    record: ExportPolicyRecord,
    formats: list[str],
    include_sections: bool,
) -> list[tuple[str, str, bytes]]:
    base_path = f"policies/{record.policy.id}"
    files = []
    for format_name in formats:
        if format_name == "markdown":
            files.append((format_name, f"{base_path}/policy.md", markdown_bytes(render_policy_markdown(record, include_sections))))
        elif format_name == "txt":
            files.append((format_name, f"{base_path}/policy.txt", text_bytes(render_policy_text(record, include_sections))))
        elif format_name == "html":
            files.append((format_name, f"{base_path}/policy.html", text_bytes(render_policy_html(record, include_sections))))
        elif format_name == "json":
            files.append((format_name, f"{base_path}/policy.json", json_bytes(policy_record_payload(record, include_sections))))
    return files


def build_manifest(
    *,
    export_id: str,
    payload: PolicyOriginalExportRequest,
    generated_at: str,
    policy_records: list[ExportPolicyRecord],
    cited_sections: list[PolicySection],
    policy_paths: dict[str, dict[str, str]],
) -> dict:
    section_count = count_manifest_sections(payload.mode, policy_records, cited_sections)
    manifest = {
        "export_id": export_id,
        "export_type": "policy_originals",
        "mode": payload.mode,
        "generated_at": generated_at,
        "project_id": str(payload.project_id) if payload.project_id else None,
        "formats": list(payload.formats),
        "policy_count": len(policy_records),
        "section_count": section_count,
        "policies": [
            {
                "policy_id": str(record.policy.id),
                "version_id": str(record.version.id),
                "title": record.policy.title,
                "source_url": record.version.source_url or record.policy.source_url,
                "sha256": record.version.sha256,
                "paths": policy_paths.get(str(record.policy.id), {}),
            }
            for record in policy_records
        ],
        "cited_sections": [
            {
                "section_id": str(section.id),
                "policy_id": str(section.policy_id),
                "version_id": str(section.version_id),
                "heading": section.heading,
                "section_path": section.section_path,
                "order_index": section.order_index,
                "metadata": to_jsonable(section.metadata_ or {}),
            }
            for section in cited_sections
        ],
        "checksums": {
            "algorithm": "sha256",
            "path": CHECKSUM_PATH if payload.include_checksums else None,
        },
        "snapshot_status": "not_available_in_v0.1" if payload.include_snapshots else "not_requested",
    }
    return manifest


def count_manifest_sections(
    mode: str,
    policy_records: list[ExportPolicyRecord],
    cited_sections: list[PolicySection],
) -> int:
    if mode == "cited_sections_only":
        return len(cited_sections)
    if mode == "evidence_bundle" and cited_sections:
        return len(cited_sections)
    return sum(len(record.sections) for record in policy_records)


def write_zip_file(storage_root: Path, export_id: str, files: dict[str, bytes]) -> tuple[Path, str]:
    storage_root = storage_root.resolve()
    storage_key = f"exports/{export_id}/policy_export_bundle.zip"
    target_path = ensure_child_path(storage_root, storage_root / storage_key)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_suffix(".zip.tmp")
    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for path, content in files.items():
                bundle.writestr(path, content)
        temp_path.replace(target_path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        if target_path.exists():
            target_path.unlink()
        raise
    return target_path, storage_key


def render_checksums(files: dict[str, bytes]) -> bytes:
    lines = []
    for path in sorted(files):
        if path == CHECKSUM_PATH:
            continue
        digest = hashlib.sha256(files[path]).hexdigest()
        lines.append(f"{digest}  {path}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def render_policy_markdown(record: ExportPolicyRecord, include_sections: bool) -> str:
    lines = [
        f"# {record.policy.title}",
        "",
        f"- Policy ID: {record.policy.id}",
        f"- Version ID: {record.version.id}",
        f"- Issuer: {record.policy.issuer or ''}",
        f"- Jurisdiction: {record.policy.jurisdiction or ''}",
        f"- Policy Type: {record.policy.policy_type or ''}",
        f"- Publish Date: {format_optional(record.policy.publish_date)}",
        f"- Effective Date: {format_optional(record.policy.effective_date)}",
        f"- Status: {record.policy.status}",
        f"- Source URL: {record.version.source_url or record.policy.source_url or ''}",
        f"- Captured At: {format_optional(record.version.captured_at)}",
        f"- SHA256: {record.version.sha256 or ''}",
        "",
        "## Policy Text",
        "",
        record.version.normalized_text or "",
    ]
    if include_sections:
        lines.extend(["", "## Sections", ""])
        for section in record.sections:
            title = section.heading or section.section_path or "Untitled Section"
            lines.extend([f"### Section {section.order_index}: {title}", "", section.content, ""])
    return "\n".join(lines).rstrip() + "\n"


def render_policy_text(record: ExportPolicyRecord, include_sections: bool) -> str:
    lines = [
        record.policy.title,
        "",
        f"Policy ID: {record.policy.id}",
        f"Version ID: {record.version.id}",
        f"Issuer: {record.policy.issuer or ''}",
        f"Jurisdiction: {record.policy.jurisdiction or ''}",
        f"Policy Type: {record.policy.policy_type or ''}",
        f"Status: {record.policy.status}",
        f"Source URL: {record.version.source_url or record.policy.source_url or ''}",
        f"Captured At: {format_optional(record.version.captured_at)}",
        f"SHA256: {record.version.sha256 or ''}",
        "",
        "Policy Text",
        "",
        record.version.normalized_text or "",
    ]
    if include_sections:
        lines.extend(["", "Sections", ""])
        for section in record.sections:
            title = section.heading or section.section_path or "Untitled Section"
            lines.extend([f"Section {section.order_index}: {title}", section.content, ""])
    return "\n".join(lines).rstrip() + "\n"


def render_policy_html(record: ExportPolicyRecord, include_sections: bool) -> str:
    section_html = ""
    if include_sections:
        section_html = "<h2>Sections</h2>" + "".join(
            (
                f"<h3>Section {section.order_index}: "
                f"{html.escape(section.heading or section.section_path or 'Untitled Section')}</h3>"
                f"<p>{html.escape(section.content).replace(chr(10), '<br>')}</p>"
            )
            for section in record.sections
        )
    return (
        "<!doctype html>\n"
        "<html><head><meta charset=\"utf-8\">"
        f"<title>{html.escape(record.policy.title)}</title></head><body>"
        f"<h1>{html.escape(record.policy.title)}</h1>"
        "<dl>"
        f"<dt>Policy ID</dt><dd>{record.policy.id}</dd>"
        f"<dt>Version ID</dt><dd>{record.version.id}</dd>"
        f"<dt>Issuer</dt><dd>{html.escape(record.policy.issuer or '')}</dd>"
        f"<dt>Jurisdiction</dt><dd>{html.escape(record.policy.jurisdiction or '')}</dd>"
        f"<dt>Policy Type</dt><dd>{html.escape(record.policy.policy_type or '')}</dd>"
        f"<dt>Status</dt><dd>{html.escape(record.policy.status)}</dd>"
        f"<dt>Source URL</dt><dd>{html.escape(record.version.source_url or record.policy.source_url or '')}</dd>"
        f"<dt>Captured At</dt><dd>{html.escape(format_optional(record.version.captured_at))}</dd>"
        f"<dt>SHA256</dt><dd>{html.escape(record.version.sha256 or '')}</dd>"
        "</dl>"
        "<h2>Policy Text</h2>"
        f"<p>{html.escape(record.version.normalized_text or '').replace(chr(10), '<br>')}</p>"
        f"{section_html}"
        "</body></html>\n"
    )


def render_cited_sections_markdown(sections: list[PolicySection]) -> str:
    lines = ["# Cited Sections", ""]
    for section in sections:
        title = section.heading or section.section_path or "Untitled Section"
        lines.extend(
            [
                f"## {title}",
                "",
                f"- Section ID: {section.id}",
                f"- Policy ID: {section.policy_id}",
                f"- Version ID: {section.version_id}",
                f"- Order Index: {section.order_index}",
                "",
                section.content,
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_evidence_markdown(payload: dict) -> str:
    lines = ["# Evidence Bundle", "", f"Generated At: {payload['generated_at']}", ""]
    for section in payload["sections"]:
        lines.extend(
            [
                f"## {section.get('heading') or section.get('section_path') or 'Untitled Section'}",
                "",
                f"- Policy ID: {section['policy_id']}",
                f"- Version ID: {section['version_id']}",
                f"- Section ID: {section['id']}",
                f"- SHA256: {section['sha256']}",
                "",
                section["content"],
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def build_sections_payload(sections: list[PolicySection]) -> list[dict]:
    return [section_payload(section) for section in sections]


def build_evidence_payload(
    policy_records: list[ExportPolicyRecord],
    cited_sections: list[PolicySection],
    generated_at: str,
) -> dict:
    sections = cited_sections or [section for record in policy_records for section in record.sections]
    return {
        "generated_at": generated_at,
        "policies": [policy_payload(record.policy) for record in policy_records],
        "versions": [version_payload(record.version) for record in policy_records],
        "sections": [section_payload(section) for section in sections],
    }


def build_machine_readable_payload(policy_records: list[ExportPolicyRecord]) -> dict:
    return {
        "policies": [policy_payload(record.policy) for record in policy_records],
        "versions": [version_payload(record.version) for record in policy_records],
        "sections": [section_payload(section) for record in policy_records for section in record.sections],
    }


def policy_record_payload(record: ExportPolicyRecord, include_sections: bool) -> dict:
    payload = {
        "policy": policy_payload(record.policy),
        "version": version_payload(record.version),
    }
    if include_sections:
        payload["sections"] = [section_payload(section) for section in record.sections]
    return payload


def policy_payload(policy: Policy) -> dict:
    return {
        "id": str(policy.id),
        "title": policy.title,
        "normalized_title": policy.normalized_title,
        "issuer": policy.issuer,
        "issuer_level": policy.issuer_level,
        "jurisdiction": policy.jurisdiction,
        "policy_type": policy.policy_type,
        "publish_date": format_optional(policy.publish_date),
        "effective_date": format_optional(policy.effective_date),
        "expiry_date": format_optional(policy.expiry_date),
        "status": policy.status,
        "source_url": policy.source_url,
        "sha256": policy.sha256,
        "metadata": to_jsonable(policy.metadata_ or {}),
        "created_at": format_optional(policy.created_at),
        "updated_at": format_optional(policy.updated_at),
    }


def version_payload(version: PolicyVersion) -> dict:
    return {
        "id": str(version.id),
        "policy_id": str(version.policy_id),
        "version_label": version.version_label,
        "source_url": version.source_url,
        "captured_at": format_optional(version.captured_at),
        "normalized_text": version.normalized_text,
        "sha256": version.sha256,
        "is_current": version.is_current,
        "metadata": to_jsonable(version.metadata_ or {}),
        "created_at": format_optional(version.created_at),
    }


def section_payload(section: PolicySection) -> dict:
    return {
        "id": str(section.id),
        "policy_id": str(section.policy_id),
        "version_id": str(section.version_id),
        "section_path": section.section_path,
        "heading": section.heading,
        "content": section.content,
        "order_index": section.order_index,
        "token_count": section.token_count,
        "metadata": to_jsonable(section.metadata_ or {}),
        "created_at": format_optional(section.created_at),
        "sha256": hashlib.sha256(section.content.encode("utf-8")).hexdigest(),
    }


def dedupe_ids(values: list[UUID]) -> list[UUID]:
    seen = set()
    result = []
    for value in values:
        key = str(value)
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def json_bytes(payload) -> bytes:
    return json.dumps(to_jsonable(payload), ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")


def markdown_bytes(value: str) -> bytes:
    return value.encode("utf-8")


def text_bytes(value: str) -> bytes:
    return value.encode("utf-8")


def format_optional(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def to_jsonable(value):
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    return value
