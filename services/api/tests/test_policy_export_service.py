import json
import zipfile

import pytest
from sqlalchemy import select

from app.db.config import settings
from app.db.models import Export
from app.repositories.exports import get_export
from app.repositories.policies import create_policy
from app.repositories.policy_sections import create_policy_sections
from app.repositories.policy_versions import create_policy_version
from app.schemas.common import PolicyOriginalExportRequest
from app.services import policy_export_service
from app.services.policy_export_service import (
    PolicyExportCurrentVersionError,
    PolicyExportNotFoundError,
    PolicyExportValidationError,
    create_policy_original_export,
)


def create_policy_record(db_session, *, title: str = "Clean Energy Policy"):
    policy = create_policy(
        db_session,
        {
            "title": title,
            "issuer": "National Energy Office",
            "jurisdiction": "China",
            "policy_type": "notice",
            "status": "active",
            "source_url": "https://example.gov/policy",
            "sha256": "d" * 64,
        },
    )
    version = create_policy_version(
        db_session,
        {
            "policy_id": policy.id,
            "version_label": "current",
            "normalized_text": "Article 1\n\nSupport clean energy.",
            "sha256": "a" * 64,
            "is_current": True,
            "metadata": {"source_document_id": "doc_1"},
        },
    )
    sections = create_policy_sections(
        db_session,
        [
            {
                "policy_id": policy.id,
                "version_id": version.id,
                "section_path": "Article 1",
                "heading": "Article 1",
                "content": "Support clean energy.",
                "order_index": 0,
                "token_count": 12,
                "metadata": {"source_chunk_index": 0},
            }
        ],
    )
    return policy, version, sections


def read_zip_json(zip_path, member: str):
    with zipfile.ZipFile(zip_path) as bundle:
        return json.loads(bundle.read(member).decode("utf-8"))


def test_single_policy_export_creates_zip_manifest_and_checksums(db_session, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    policy, version, _sections = create_policy_record(db_session)

    response = create_policy_original_export(
        db_session,
        PolicyOriginalExportRequest(
            policy_ids=[policy.id],
            mode="single_policy_full_text",
            formats=["markdown", "txt", "html", "json"],
        ),
    )

    export = get_export(db_session, response.export_id)
    assert export is not None
    assert export.status == "completed"
    assert export.storage_key == f"exports/{response.export_id}/policy_export_bundle.zip"
    assert not response.bundle_path.startswith(str(tmp_path))

    zip_path = tmp_path / export.storage_key
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as bundle:
        names = set(bundle.namelist())
        assert "manifest.json" in names
        assert f"policies/{policy.id}/policy.md" in names
        assert f"policies/{policy.id}/policy.txt" in names
        assert f"policies/{policy.id}/policy.html" in names
        assert f"policies/{policy.id}/policy.json" in names
        assert "checksums/sha256.txt" in names
        markdown = bundle.read(f"policies/{policy.id}/policy.md").decode("utf-8")
        checksums = bundle.read("checksums/sha256.txt").decode("utf-8")

    manifest = read_zip_json(zip_path, "manifest.json")
    assert manifest["export_id"] == response.export_id
    assert manifest["mode"] == "single_policy_full_text"
    assert manifest["policy_count"] == 1
    assert manifest["section_count"] == 1
    assert manifest["policies"][0]["version_id"] == str(version.id)
    assert manifest["snapshot_status"] == "not_available_in_v0.1"
    assert "Support clean energy." in markdown
    assert "manifest.json" in checksums
    assert f"policies/{policy.id}/policy.md" in checksums


def test_export_modes_write_expected_members(db_session, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    first_policy, _first_version, first_sections = create_policy_record(db_session, title="First Energy Policy")
    second_policy, _second_version, _second_sections = create_policy_record(db_session, title="Second Energy Policy")

    related = create_policy_original_export(
        db_session,
        PolicyOriginalExportRequest(policy_ids=[first_policy.id, second_policy.id], mode="related_policy_bundle"),
    )
    cited = create_policy_original_export(
        db_session,
        PolicyOriginalExportRequest(
            cited_section_ids=[first_sections[0].id],
            mode="cited_sections_only",
            formats=["json"],
        ),
    )
    evidence = create_policy_original_export(
        db_session,
        PolicyOriginalExportRequest(policy_ids=[first_policy.id], mode="evidence_bundle"),
    )
    machine = create_policy_original_export(
        db_session,
        PolicyOriginalExportRequest(policy_ids=[first_policy.id], mode="machine_readable_json", formats=["json"]),
    )

    with zipfile.ZipFile(tmp_path / get_export(db_session, related.export_id).storage_key) as bundle:
        assert f"policies/{first_policy.id}/policy.md" in bundle.namelist()
        assert f"policies/{second_policy.id}/policy.json" in bundle.namelist()
    with zipfile.ZipFile(tmp_path / get_export(db_session, cited.export_id).storage_key) as bundle:
        assert "cited_sections/cited_sections.json" in bundle.namelist()
        assert "cited_sections/cited_sections.md" in bundle.namelist()
    with zipfile.ZipFile(tmp_path / get_export(db_session, evidence.export_id).storage_key) as bundle:
        assert "evidence/evidence_bundle.json" in bundle.namelist()
        assert "evidence/evidence_bundle.md" in bundle.namelist()
    with zipfile.ZipFile(tmp_path / get_export(db_session, machine.export_id).storage_key) as bundle:
        assert "machine_readable/policies.json" in bundle.namelist()
        assert "machine_readable/versions.json" in bundle.namelist()
        assert "machine_readable/sections.json" in bundle.namelist()


def test_policy_export_validation_and_lookup_errors(db_session) -> None:
    policy_without_version = create_policy(db_session, {"title": "No version policy"})

    with pytest.raises(PolicyExportValidationError):
        create_policy_original_export(db_session, PolicyOriginalExportRequest(mode="related_policy_bundle"))
    with pytest.raises(PolicyExportValidationError):
        create_policy_original_export(
            db_session,
            PolicyOriginalExportRequest(
                policy_ids=[policy_without_version.id, "11111111-1111-4111-8111-111111111111"],
                mode="single_policy_full_text",
            ),
        )
    with pytest.raises(PolicyExportValidationError):
        create_policy_original_export(
            db_session,
            PolicyOriginalExportRequest(policy_ids=[policy_without_version.id], mode="cited_sections_only"),
        )
    with pytest.raises(PolicyExportCurrentVersionError):
        create_policy_original_export(
            db_session,
            PolicyOriginalExportRequest(policy_ids=[policy_without_version.id], mode="related_policy_bundle"),
        )
    with pytest.raises(PolicyExportNotFoundError):
        create_policy_original_export(
            db_session,
            PolicyOriginalExportRequest(
                policy_ids=["11111111-1111-4111-8111-111111111111"],
                mode="related_policy_bundle",
            ),
        )
    with pytest.raises(PolicyExportNotFoundError):
        create_policy_original_export(
            db_session,
            PolicyOriginalExportRequest(
                cited_section_ids=["22222222-2222-4222-8222-222222222222"],
                mode="cited_sections_only",
            ),
        )


def test_policy_export_mode_combinations_are_validated(db_session) -> None:
    policy, _version, sections = create_policy_record(db_session)

    invalid_payloads = [
        PolicyOriginalExportRequest(
            policy_ids=[policy.id],
            cited_section_ids=[sections[0].id],
            mode="single_policy_full_text",
        ),
        PolicyOriginalExportRequest(
            cited_section_ids=[sections[0].id],
            mode="related_policy_bundle",
        ),
        PolicyOriginalExportRequest(
            policy_ids=[policy.id],
            cited_section_ids=[sections[0].id],
            mode="cited_sections_only",
        ),
        PolicyOriginalExportRequest(
            policy_ids=[policy.id],
            mode="single_policy_full_text",
            formats=[],
        ),
        PolicyOriginalExportRequest(
            policy_ids=[policy.id],
            mode="related_policy_bundle",
            formats=[],
        ),
    ]

    for payload in invalid_payloads:
        with pytest.raises(PolicyExportValidationError):
            create_policy_original_export(db_session, payload)


def test_policy_export_marks_export_failed_when_bundle_writer_errors(db_session, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    policy, _version, _sections = create_policy_record(db_session)

    def raise_write_error(*args, **kwargs):
        raise RuntimeError("zip write failed")

    monkeypatch.setattr(policy_export_service, "write_policy_export_bundle", raise_write_error)

    with pytest.raises(RuntimeError, match="zip write failed"):
        create_policy_original_export(
            db_session,
            PolicyOriginalExportRequest(policy_ids=[policy.id], mode="single_policy_full_text"),
        )

    export_ids = db_session.scalars(select(Export.id)).all()
    assert len(export_ids) == 1
    export = get_export(db_session, export_ids[0])
    assert export is not None
    assert export.status == "failed"
    assert export.finished_at is not None
    assert export.manifest["error"]["type"] == "RuntimeError"
    assert export.manifest["error"]["message"] == "zip write failed"
