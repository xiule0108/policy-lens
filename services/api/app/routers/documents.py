from __future__ import annotations

from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.config import settings
from app.db.models import Document as DocumentModel
from app.db.models import DocumentChunk as DocumentChunkModel
from app.db.session import get_session
from app.repositories.document_chunks import count_document_chunks, list_document_chunks
from app.repositories.documents import create_document, get_document, list_documents
from app.repositories.projects import get_project
from app.schemas.common import (
    DocumentChunkListResponse,
    DocumentChunkResponse,
    DocumentListResponse,
    DocumentParseResponse,
    DocumentResponse,
    DocumentRole,
)
from app.services.document_parse_service import (
    DocumentFileNotFoundError,
    DocumentNotFoundError,
    parse_document_by_id,
)
from app.services.document_parser import DocumentParserError, EmptyParsedDocumentError, UnsupportedDocumentTypeError
from app.services.storage_service import (
    EmptyUploadError,
    StorageError,
    UploadExtensionError,
    UploadTooLargeError,
    delete_stored_file,
    resolve_storage_path,
    save_upload_file,
)

router = APIRouter()


def document_to_response(document: DocumentModel) -> DocumentResponse:
    metadata = document.metadata_ or {}
    return DocumentResponse(
        id=str(document.id),
        project_id=str(document.project_id),
        document_role=document.document_role,
        title=document.title,
        file_name=document.file_name,
        file_type=document.file_type,
        file_size=document.file_size,
        content_type=metadata.get("content_type"),
        storage_key=document.storage_key,
        language=document.language,
        page_count=document.page_count,
        parse_status=document.parse_status,
        source_url=document.source_url,
        sha256=document.sha256,
        metadata=metadata,
        created_at=document.created_at,
        updated_at=document.updated_at,
        evidence=[],
    )


def chunk_to_response(chunk: DocumentChunkModel) -> DocumentChunkResponse:
    return DocumentChunkResponse(
        id=str(chunk.id),
        document_id=str(chunk.document_id),
        project_id=str(chunk.project_id),
        chunk_index=chunk.chunk_index,
        page_start=chunk.page_start,
        page_end=chunk.page_end,
        section_title=chunk.section_title,
        content=chunk.content,
        content_type=chunk.content_type,
        token_count=chunk.token_count,
        metadata=chunk.metadata_ or {},
        created_at=chunk.created_at,
    )


@router.get("", response_model=DocumentListResponse)
def list_document_records(
    project_id: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: Session = Depends(get_session),
) -> DocumentListResponse:
    documents = list_documents(session, project_id=project_id, limit=limit, offset=offset)
    return DocumentListResponse(items=[document_to_response(document) for document in documents])


@router.post("/upload", response_model=DocumentResponse, status_code=201)
def upload_document(
    project_id: Annotated[UUID, Form()],
    document_role: Annotated[DocumentRole, Form()] = "research_article",
    title: Annotated[str | None, Form()] = None,
    source_url: Annotated[str | None, Form()] = None,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> DocumentResponse:
    if get_project(session, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    document_id = uuid4()
    storage_root = Path(settings.storage_dir)
    try:
        stored_file = save_upload_file(
            upload_file=file,
            storage_root=storage_root,
            project_id=str(project_id),
            document_id=str(document_id),
            max_size_bytes=settings.max_upload_size_bytes,
            allowed_extensions=settings.allowed_upload_extension_set,
        )
    except EmptyUploadError as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.") from exc
    except UploadExtensionError as exc:
        raise HTTPException(status_code=400, detail="Unsupported upload file extension.") from exc
    except UploadTooLargeError as exc:
        raise HTTPException(status_code=413, detail="Uploaded file exceeds the configured size limit.") from exc
    except StorageError as exc:
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.") from exc

    try:
        document = create_document(
            session,
            {
                "id": document_id,
                "project_id": project_id,
                "document_role": document_role,
                "title": title,
                "file_name": stored_file.file_name,
                "file_type": stored_file.file_type,
                "file_size": stored_file.file_size,
                "storage_key": stored_file.storage_key,
                "parse_status": "pending",
                "source_url": source_url,
                "sha256": stored_file.sha256,
                "metadata": {
                    "content_type": stored_file.content_type,
                    "original_filename": stored_file.original_filename,
                    "safe_filename": stored_file.file_name,
                },
            },
        )
    except Exception as exc:
        session.rollback()
        delete_stored_file(stored_file.absolute_path, storage_root)
        raise HTTPException(status_code=500, detail="Failed to create document record.") from exc

    return document_to_response(document)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document_record(
    document_id: UUID,
    session: Session = Depends(get_session),
) -> DocumentResponse:
    document = get_document(session, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document_to_response(document)


@router.post("/{document_id}/parse", response_model=DocumentParseResponse)
def parse_document(
    document_id: UUID,
    session: Session = Depends(get_session),
) -> DocumentParseResponse:
    try:
        result = parse_document_by_id(session, document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document not found.") from exc
    except DocumentFileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document file not found.") from exc
    except UnsupportedDocumentTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except EmptyParsedDocumentError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except DocumentParserError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to parse document.") from exc

    return DocumentParseResponse(
        document_id=result.document_id,
        parse_status=result.parse_status,
        chunk_count=result.chunk_count,
        page_count=result.page_count,
        language=result.language,
        title=result.title,
        error=result.error,
    )


@router.get("/{document_id}/chunks", response_model=DocumentChunkListResponse)
def get_document_chunks(
    document_id: UUID,
    limit: Annotated[int, Query(ge=1, le=200)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: Session = Depends(get_session),
) -> DocumentChunkListResponse:
    document = get_document(session, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    chunks = list_document_chunks(session, document_id, limit=limit, offset=offset)
    total = count_document_chunks(session, document_id)
    return DocumentChunkListResponse(items=[chunk_to_response(chunk) for chunk in chunks], total=total)


@router.get("/{document_id}/download")
def download_document(
    document_id: UUID,
    session: Session = Depends(get_session),
) -> FileResponse:
    document = get_document(session, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    if not document.storage_key:
        raise HTTPException(status_code=404, detail="Document file not found.")

    try:
        file_path = resolve_storage_path(Path(settings.storage_dir), document.storage_key)
    except StorageError as exc:
        raise HTTPException(status_code=404, detail="Document file not found.") from exc
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Document file not found.")

    metadata = document.metadata_ or {}
    return FileResponse(
        path=file_path,
        media_type=metadata.get("content_type") or "application/octet-stream",
        filename=document.file_name,
    )
