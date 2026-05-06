from __future__ import annotations

from dataclasses import dataclass
from datetime import timezone
import hashlib
import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.db.models import Document, Policy
from app.repositories.document_chunks import count_document_chunks, list_document_chunks
from app.repositories.documents import get_document, update_document_after_parse
from app.repositories.policies import create_policy, get_policy, update_policy
from app.repositories.policy_sections import create_policy_sections
from app.repositories.policy_versions import create_policy_version, set_policy_versions_not_current
from app.schemas.common import PolicyCreateFromDocumentRequest


class PolicyIngestionError(Exception):
    """Base class for policy ingestion failures."""


class PolicyDocumentNotFoundError(PolicyIngestionError):
    """Raised when the source document does not exist."""


class PolicyDocumentRoleError(PolicyIngestionError):
    """Raised when the source document is not a policy document."""


class PolicyDocumentNotParsedError(PolicyIngestionError):
    """Raised when the source document has not been parsed."""


class PolicyDocumentNoChunksError(PolicyIngestionError):
    """Raised when a parsed document has no chunks."""


class PolicyDocumentStorageError(PolicyIngestionError):
    """Raised when a policy document has no storage key."""


class PolicyDocumentAlreadyIngestedConflictError(PolicyIngestionError):
    """Raised when an ingested document is requested for a different policy."""


class PolicyNotFoundError(PolicyIngestionError):
    """Raised when a requested target policy does not exist."""


@dataclass(frozen=True)
class PolicyIngestionResult:
    policy_id: str
    version_id: str
    section_count: int
    title: str
    status: str
    already_ingested: bool = False


def normalize_policy_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip().lower()


def choose_policy_title(document: Document, request: PolicyCreateFromDocumentRequest) -> str:
    metadata = document.metadata_ or {}
    for value in (
        request.title,
        document.title,
        metadata.get("original_filename"),
        document.file_name,
    ):
        if value and str(value).strip():
            return str(value).strip()
    return "Untitled Policy"


def build_normalized_text(chunks) -> str:
    return "\n\n".join(chunk.content.strip() for chunk in chunks if chunk.content and chunk.content.strip())


def get_existing_ingestion(document: Document) -> dict | None:
    ingestion = (document.metadata_ or {}).get("policy_ingestion")
    return ingestion if isinstance(ingestion, dict) else None


def ensure_existing_ingestion_policy_matches_request(
    existing_ingestion: dict | None,
    request: PolicyCreateFromDocumentRequest,
) -> None:
    existing_policy_id = (existing_ingestion or {}).get("policy_id")
    if existing_policy_id and request.policy_id and str(request.policy_id) != str(existing_policy_id):
        raise PolicyDocumentAlreadyIngestedConflictError(
            "Document has already been ingested into a different policy."
        )


def existing_ingestion_result(
    session: Session,
    document: Document,
    ingestion: dict,
) -> PolicyIngestionResult | None:
    policy_id = ingestion.get("policy_id")
    version_id = ingestion.get("version_id")
    if not policy_id or not version_id:
        return None
    policy = get_policy(session, policy_id)
    if policy is None:
        return None
    return PolicyIngestionResult(
        policy_id=str(policy.id),
        version_id=str(version_id),
        section_count=int(ingestion.get("section_count") or 0),
        title=policy.title,
        status=policy.status,
        already_ingested=True,
    )


def validate_policy_document(session: Session, document_id: UUID) -> tuple[Document, list]:
    document = get_document(session, document_id)
    if document is None:
        raise PolicyDocumentNotFoundError("Document not found.")
    if document.document_role != "policy":
        raise PolicyDocumentRoleError("Only documents with document_role=policy can be ingested.")
    if document.parse_status != "parsed":
        raise PolicyDocumentNotParsedError("Policy document must be parsed before ingestion.")
    if not document.storage_key:
        raise PolicyDocumentStorageError("Policy document has no storage key.")
    if count_document_chunks(session, document.id) <= 0:
        raise PolicyDocumentNoChunksError("Policy document has no chunks.")
    chunks = list_document_chunks(session, document.id, limit=10_000)
    if not chunks:
        raise PolicyDocumentNoChunksError("Policy document has no chunks.")
    return document, chunks


def create_or_update_policy(
    session: Session,
    document: Document,
    request: PolicyCreateFromDocumentRequest,
    existing_ingestion: dict | None,
) -> Policy:
    target_policy_id = request.policy_id or (existing_ingestion or {}).get("policy_id")
    title = choose_policy_title(document, request)
    new_policy_data = {
        "title": title,
        "normalized_title": normalize_policy_title(title),
        "issuer": request.issuer,
        "issuer_level": request.issuer_level,
        "jurisdiction": request.jurisdiction,
        "policy_type": request.policy_type,
        "publish_date": request.publish_date,
        "effective_date": request.effective_date,
        "expiry_date": request.expiry_date,
        "status": request.status,
        "source_url": document.source_url,
        "sha256": document.sha256,
        "metadata": {
            "source_document_id": str(document.id),
            "source_document_file_name": document.file_name,
        },
    }
    if target_policy_id:
        policy = get_policy(session, target_policy_id)
        if policy is None:
            raise PolicyNotFoundError("Policy not found.")
        update_data = {
            "source_url": document.source_url,
            "sha256": document.sha256,
            "metadata": new_policy_data["metadata"],
        }
        if "title" in request.model_fields_set and request.title:
            update_data["title"] = request.title
            update_data["normalized_title"] = normalize_policy_title(request.title)
        for key in (
            "issuer",
            "issuer_level",
            "jurisdiction",
            "policy_type",
            "publish_date",
            "effective_date",
            "expiry_date",
            "status",
        ):
            if key in request.model_fields_set:
                update_data[key] = getattr(request, key)
        updated = update_policy(session, policy.id, update_data)
        return updated or policy
    return create_policy(
        session,
        {
            **new_policy_data,
            "source_id": document.id,
        },
    )


def create_version_and_sections(
    session: Session,
    policy: Policy,
    document: Document,
    request: PolicyCreateFromDocumentRequest,
    chunks,
) -> tuple[str, int]:
    set_policy_versions_not_current(session, policy.id)
    normalized_text = build_normalized_text(chunks)
    version_sha256 = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
    version = create_policy_version(
        session,
        {
            "policy_id": policy.id,
            "version_label": request.version_label,
            "source_url": document.source_url,
            "normalized_text": normalized_text,
            "sha256": version_sha256,
            "is_current": True,
            "metadata": {
                "source_document_id": str(document.id),
                "source_document_sha256": document.sha256,
                "source_document_file_name": document.file_name,
                "source_document_storage_key": document.storage_key,
                "chunk_count": len(chunks),
            },
        },
    )
    sections = create_policy_sections(
        session,
        [
            {
                "policy_id": policy.id,
                "version_id": version.id,
                "section_path": chunk.section_title,
                "heading": chunk.section_title or (chunk.content if chunk.content_type == "heading" else None),
                "content": chunk.content,
                "order_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "metadata": {
                    "source_document_id": str(document.id),
                    "source_chunk_id": str(chunk.id),
                    "source_chunk_index": chunk.chunk_index,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "content_type": chunk.content_type,
                },
            }
            for chunk in chunks
        ],
    )
    return str(version.id), len(sections)


def update_document_policy_ingestion(
    session: Session,
    document: Document,
    *,
    policy_id: str,
    version_id: str,
    section_count: int,
    force_new_version: bool,
) -> None:
    update_document_after_parse(
        session,
        document.id,
        parse_status=document.parse_status,
        metadata_patch={
            "policy_ingestion": {
                "policy_id": policy_id,
                "version_id": version_id,
                "section_count": section_count,
                "ingested_at": utc_now().astimezone(timezone.utc).isoformat(),
                "force_new_version": force_new_version,
            }
        },
    )


def ingest_policy_from_document(
    session: Session,
    request: PolicyCreateFromDocumentRequest,
) -> PolicyIngestionResult:
    document, chunks = validate_policy_document(session, request.document_id)
    existing_ingestion = get_existing_ingestion(document)
    ensure_existing_ingestion_policy_matches_request(existing_ingestion, request)
    if existing_ingestion and not request.force_new_version:
        existing_result = existing_ingestion_result(session, document, existing_ingestion)
        if existing_result is not None:
            return existing_result

    policy = create_or_update_policy(session, document, request, existing_ingestion)
    version_id, section_count = create_version_and_sections(session, policy, document, request, chunks)
    update_document_policy_ingestion(
        session,
        document,
        policy_id=str(policy.id),
        version_id=version_id,
        section_count=section_count,
        force_new_version=request.force_new_version,
    )
    return PolicyIngestionResult(
        policy_id=str(policy.id),
        version_id=version_id,
        section_count=section_count,
        title=policy.title,
        status=policy.status,
        already_ingested=False,
    )
