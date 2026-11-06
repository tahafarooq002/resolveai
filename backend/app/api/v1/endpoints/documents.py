import logging
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_user_organization_id
from app.models.user import User
from app.schemas.document import KnowledgeDocumentResponse
from app.services import document as document_service
from app.services.rag import index_document_chunks

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=KnowledgeDocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    organization_id: Annotated[UUID, Depends(get_user_organization_id)] = None,
):
    """
    Upload a knowledge document (PDF, DOCX, TXT, MD, CSV).
    Automatically extracts text, chunks it, and stores in DB.
    Optionally indexes into Qdrant if configured.
    """
    doc = await document_service.save_and_process_document(
        db=db,
        organization_id=organization_id,
        file=file,
        title=title,
    )

    # Try to index into Qdrant (non-blocking for MVP)
    try:
        index_document_chunks(db, organization_id, doc.id)
    except (ConnectionError, TimeoutError) as exc:
        logger.warning("Document %s was stored but vector indexing was unavailable: %s", doc.id, exc)

    return doc


@router.get("", response_model=List[KnowledgeDocumentResponse])
def list_documents(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    organization_id: Annotated[UUID, Depends(get_user_organization_id)],
):
    """List all knowledge documents for the current organization."""
    return document_service.list_documents(db, organization_id)


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    organization_id: Annotated[UUID, Depends(get_user_organization_id)],
):
    """Delete a document and its chunks."""
    document_service.delete_document(db, document_id, organization_id)
    return None
