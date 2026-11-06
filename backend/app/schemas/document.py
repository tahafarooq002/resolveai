from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import IDSchema, TimestampSchema


class KnowledgeDocumentBase(BaseModel):
    title: str = Field(..., max_length=500)


class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    pass


class KnowledgeDocumentResponse(KnowledgeDocumentBase, IDSchema, TimestampSchema):
    organization_id: UUID
    filename: str
    file_type: str
    file_size: int
    status: str
    error_message: Optional[str] = None


class DocumentChunkResponse(IDSchema, TimestampSchema):
    document_id: UUID
    organization_id: UUID
    content: str
    chunk_index: int
    token_count: Optional[int] = None
