from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter

from app.schemas.common import Document, DocumentListResponse, DocumentUploadRequest
from app.services.mock_data import mock_documents

router = APIRouter()


@router.get("", response_model=DocumentListResponse)
def list_documents() -> DocumentListResponse:
    return DocumentListResponse(items=mock_documents())


@router.post("/upload", response_model=Document, status_code=201)
def upload_document(payload: DocumentUploadRequest) -> Document:
    return Document(
        id=f"doc_{uuid4().hex[:8]}",
        project_id=payload.project_id,
        filename=payload.filename,
        content_type=payload.content_type,
        status="queued_for_parsing",
        parser="mock_parser",
        uploaded_at=datetime.now(timezone.utc),
        source=payload.source,
        citations=[],
        evidence=[],
    )
