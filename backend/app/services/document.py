import os
import re
import uuid
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import KnowledgeDocument, DocumentChunk

# Supported extractors
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def extract_text_from_file(file_path: Path, file_type: str) -> str:
    """Extract plain text from uploaded file."""
    if file_type == ".pdf":
        if fitz is None:
            raise HTTPException(status_code=500, detail="PyMuPDF not installed")
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text

    elif file_type == ".docx":
        if DocxDocument is None:
            raise HTTPException(status_code=500, detail="python-docx not installed")
        doc = DocxDocument(file_path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

    elif file_type in [".txt", ".md", ".csv"]:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    elif file_type in [".html", ".htm"]:
        html = file_path.read_text(encoding="utf-8", errors="ignore")
        return re.sub(r"<[^>]+>", " ", html)

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
    """Simple overlapping character-based chunking."""
    if not text or not text.strip():
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
        if start >= text_len:
            break

    return chunks


async def save_and_process_document(
    db: Session,
    organization_id: UUID,
    file: UploadFile,
    title: Optional[str] = None,
) -> KnowledgeDocument:
    """Save uploaded file, extract text, create chunks, and store in DB."""

    # Validate extension
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext} not allowed. Allowed: {settings.ALLOWED_DOCUMENT_TYPES}",
        )

    # Check size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB} MB",
        )

    # Save file to disk
    org_dir = UPLOAD_DIR / str(organization_id)
    org_dir.mkdir(parents=True, exist_ok=True)
    file_id = str(uuid.uuid4())
    saved_path = org_dir / f"{file_id}{ext}"
    saved_path.write_bytes(content)

    # Create DB record
    doc = KnowledgeDocument(
        organization_id=organization_id,
        title=title or filename,
        filename=filename,
        file_type=ext,
        file_size=len(content),
        status="processing",
    )
    db.add(doc)
    db.flush()

    try:
        # Extract + chunk
        text = extract_text_from_file(saved_path, ext)
        chunks = chunk_text(
            text,
            chunk_size=settings.RAG_CHUNK_SIZE,
            overlap=settings.RAG_CHUNK_OVERLAP,
        )

        for idx, chunk_content in enumerate(chunks):
            chunk = DocumentChunk(
                document_id=doc.id,
                organization_id=organization_id,
                content=chunk_content,
                chunk_index=idx,
                token_count=len(chunk_content.split()),
            )
            db.add(chunk)

        doc.status = "ready"
        db.commit()
        db.refresh(doc)
        return doc

    except HTTPException:
        db.rollback()
        raise
    except (OSError, UnicodeError, ValueError) as e:
        doc.status = "failed"
        doc.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


def list_documents(db: Session, organization_id: UUID) -> List[KnowledgeDocument]:
    return (
        db.query(KnowledgeDocument)
        .filter(KnowledgeDocument.organization_id == organization_id)
        .order_by(KnowledgeDocument.created_at.desc())
        .all()
    )


def delete_document(db: Session, document_id: UUID, organization_id: UUID) -> None:
    doc = (
        db.query(KnowledgeDocument)
        .filter(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.organization_id == organization_id,
        )
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file from disk if exists
    # (simplified – in production also remove from Qdrant)

    db.delete(doc)
    db.commit()
