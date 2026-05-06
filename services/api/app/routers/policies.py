from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.db.models import Policy as PolicyModel
from app.db.models import PolicySection as PolicySectionModel
from app.db.models import PolicyVersion as PolicyVersionModel
from app.db.session import get_session
from app.repositories.policies import get_policy, list_policies, search_policies_by_keyword
from app.repositories.policy_sections import count_policy_sections, list_policy_sections
from app.repositories.policy_versions import get_current_policy_version, get_policy_version, list_policy_versions
from app.schemas.common import (
    PolicyCreateFromDocumentRequest,
    PolicyCreateFromDocumentResponse,
    PolicyDetailResponse,
    PolicyListResponse,
    PolicyOriginalResponse,
    PolicyResponse,
    PolicySearchRequest,
    PolicySearchResponse,
    PolicySectionListResponse,
    PolicySectionResponse,
    PolicyVersionListResponse,
    PolicyVersionResponse,
)
from app.services.policy_ingestion_service import (
    PolicyDocumentNoChunksError,
    PolicyDocumentNotFoundError,
    PolicyDocumentNotParsedError,
    PolicyDocumentRoleError,
    PolicyDocumentStorageError,
    PolicyNotFoundError,
    ingest_policy_from_document,
)

router = APIRouter()


def policy_to_response(policy: PolicyModel) -> PolicyResponse:
    return PolicyResponse(
        id=str(policy.id),
        title=policy.title,
        normalized_title=policy.normalized_title,
        issuer=policy.issuer,
        issuer_level=policy.issuer_level,
        jurisdiction=policy.jurisdiction,
        policy_type=policy.policy_type,
        publish_date=policy.publish_date,
        effective_date=policy.effective_date,
        expiry_date=policy.expiry_date,
        status=policy.status,
        source_url=policy.source_url,
        sha256=policy.sha256,
        metadata=policy.metadata_ or {},
        created_at=policy.created_at,
        updated_at=policy.updated_at,
        evidence=[],
    )


def policy_to_detail_response(policy: PolicyModel, current_version_id: str | None) -> PolicyDetailResponse:
    base = policy_to_response(policy).model_dump()
    return PolicyDetailResponse(**base, current_version_id=current_version_id)


def version_to_response(version: PolicyVersionModel) -> PolicyVersionResponse:
    return PolicyVersionResponse(
        id=str(version.id),
        policy_id=str(version.policy_id),
        version_label=version.version_label,
        source_url=version.source_url,
        captured_at=version.captured_at,
        sha256=version.sha256,
        is_current=version.is_current,
        metadata=version.metadata_ or {},
        created_at=version.created_at,
    )


def section_to_response(section: PolicySectionModel) -> PolicySectionResponse:
    return PolicySectionResponse(
        id=str(section.id),
        policy_id=str(section.policy_id),
        version_id=str(section.version_id),
        section_path=section.section_path,
        heading=section.heading,
        content=section.content,
        order_index=section.order_index,
        token_count=section.token_count,
        metadata=section.metadata_ or {},
        created_at=section.created_at,
    )


@router.post("/from-document", response_model=PolicyCreateFromDocumentResponse, status_code=201)
def create_policy_from_document(
    payload: PolicyCreateFromDocumentRequest,
    response: Response,
    session: Session = Depends(get_session),
) -> PolicyCreateFromDocumentResponse:
    try:
        result = ingest_policy_from_document(session, payload)
    except PolicyDocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document not found.") from exc
    except PolicyDocumentRoleError as exc:
        raise HTTPException(status_code=409, detail="Document role must be policy.") from exc
    except PolicyDocumentNotParsedError as exc:
        raise HTTPException(status_code=409, detail="Policy document must be parsed before ingestion.") from exc
    except (PolicyDocumentNoChunksError, PolicyDocumentStorageError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PolicyNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Policy not found.") from exc

    if result.already_ingested:
        response.status_code = 200
    return PolicyCreateFromDocumentResponse(
        policy_id=result.policy_id,
        version_id=result.version_id,
        section_count=result.section_count,
        title=result.title,
        status=result.status,
        already_ingested=result.already_ingested,
    )


@router.get("", response_model=PolicyListResponse)
def list_policy_records(
    query: str | None = None,
    jurisdiction: str | None = None,
    issuer: str | None = None,
    policy_type: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: Session = Depends(get_session),
) -> PolicyListResponse:
    policies = list_policies(
        session,
        query=query,
        jurisdiction=jurisdiction,
        issuer=issuer,
        policy_type=policy_type,
        status=status,
        limit=limit,
        offset=offset,
    )
    return PolicyListResponse(items=[policy_to_response(policy) for policy in policies])


@router.post("/search", response_model=PolicySearchResponse)
def search_policies(payload: PolicySearchRequest, session: Session = Depends(get_session)) -> PolicySearchResponse:
    policies = search_policies_by_keyword(session, payload.query, limit=payload.limit)
    if payload.jurisdictions:
        policies = [policy for policy in policies if policy.jurisdiction in payload.jurisdictions]
    if payload.policy_types:
        policies = [policy for policy in policies if policy.policy_type in payload.policy_types]
    return PolicySearchResponse(
        query=payload.query,
        total=len(policies),
        items=[policy_to_response(policy) for policy in policies],
        evidence=[],
    )


@router.get("/{policy_id}", response_model=PolicyDetailResponse)
def get_policy_record(policy_id: UUID, session: Session = Depends(get_session)) -> PolicyDetailResponse:
    policy = get_policy(session, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    current_version = get_current_policy_version(session, policy.id)
    return policy_to_detail_response(policy, str(current_version.id) if current_version else None)


@router.get("/{policy_id}/versions", response_model=PolicyVersionListResponse)
def get_policy_versions(
    policy_id: UUID,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: Session = Depends(get_session),
) -> PolicyVersionListResponse:
    policy = get_policy(session, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    versions = list_policy_versions(session, policy_id, limit=limit, offset=offset)
    return PolicyVersionListResponse(items=[version_to_response(version) for version in versions])


@router.get("/{policy_id}/sections", response_model=PolicySectionListResponse)
def get_policy_sections(
    policy_id: UUID,
    version_id: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: Session = Depends(get_session),
) -> PolicySectionListResponse:
    policy = get_policy(session, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    if version_id is None:
        current_version = get_current_policy_version(session, policy_id)
        if current_version is None:
            raise HTTPException(status_code=404, detail="Policy version not found.")
        version_id = current_version.id
    else:
        version = get_policy_version(session, version_id)
        if version is None or version.policy_id != policy.id:
            raise HTTPException(status_code=404, detail="Policy version not found.")
    sections = list_policy_sections(session, policy_id, version_id=version_id, limit=limit, offset=offset)
    total = count_policy_sections(session, policy_id, version_id=version_id)
    return PolicySectionListResponse(items=[section_to_response(section) for section in sections], total=total)


@router.get("/{policy_id}/original", response_model=PolicyOriginalResponse)
def get_policy_original(
    policy_id: UUID,
    version_id: UUID | None = None,
    session: Session = Depends(get_session),
) -> PolicyOriginalResponse:
    policy = get_policy(session, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    version = get_policy_version(session, version_id) if version_id else get_current_policy_version(session, policy_id)
    if version is None or version.policy_id != policy.id:
        raise HTTPException(status_code=404, detail="Policy version not found.")
    sections_count = count_policy_sections(session, policy_id, version_id=version.id)
    return PolicyOriginalResponse(
        policy_id=str(policy.id),
        version_id=str(version.id),
        title=policy.title,
        source_url=version.source_url or policy.source_url,
        captured_at=version.captured_at,
        sha256=version.sha256,
        normalized_text=version.normalized_text or "",
        sections_count=sections_count,
        metadata=version.metadata_ or {},
    )
