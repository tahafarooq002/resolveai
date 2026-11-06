"""
Hybrid RAG service using Qdrant.
Supports dense (OpenAI embeddings) + keyword style retrieval.
Falls back to simple DB keyword search if Qdrant/OpenAI not configured.
"""

import re
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.config import settings
from app.models.document import DocumentChunk

# Optional imports
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def get_qdrant_client() -> Optional["QdrantClient"]:
    if not QDRANT_AVAILABLE:
        return None
    try:
        return QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
        )
    except (ConnectionError, TimeoutError, ValueError):
        return None


def get_embedding(text: str) -> Optional[List[float]]:
    """Get embedding using OpenAI (or return None)."""
    if not OPENAI_AVAILABLE or not settings.OPENAI_API_KEY:
        return None
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        resp = client.embeddings.create(
            model=settings.DEFAULT_EMBEDDING_MODEL,
            input=text[:8000],
        )
        return resp.data[0].embedding
    except (ConnectionError, TimeoutError, ValueError):
        return None


def ensure_collection(client: "QdrantClient", organization_id: UUID, vector_size: int = 1536):
    collection_name = f"{settings.QDRANT_COLLECTION_PREFIX}_{organization_id}"
    try:
        client.get_collection(collection_name)
    except (ConnectionError, TimeoutError, ValueError):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=qmodels.VectorParams(
                size=vector_size,
                distance=qmodels.Distance.COSINE,
            ),
        )
    return collection_name


def index_document_chunks(
    db: Session,
    organization_id: UUID,
    document_id: UUID,
) -> int:
    """Index all chunks of a document into Qdrant. Returns number of chunks indexed."""
    client = get_qdrant_client()
    if client is None:
        return 0

    chunks = (
        db.query(DocumentChunk)
        .filter(
            DocumentChunk.document_id == document_id,
            DocumentChunk.organization_id == organization_id,
        )
        .all()
    )
    if not chunks:
        return 0

    # Get embedding dimension from first successful embed
    sample_emb = get_embedding(chunks[0].content[:500])
    if sample_emb is None:
        return 0

    collection_name = ensure_collection(client, organization_id, len(sample_emb))

    points = []
    for chunk in chunks:
        emb = get_embedding(chunk.content)
        if emb is None:
            continue
        points.append(
            qmodels.PointStruct(
                id=str(chunk.id),
                vector=emb,
                payload={
                    "document_id": str(document_id),
                    "organization_id": str(organization_id),
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                },
            )
        )

    if points:
        client.upsert(collection_name=collection_name, points=points)
    return len(points)


def hybrid_search(
    db: Session,
    organization_id: UUID,
    query: str,
    top_k: int = 6,
) -> List[dict]:
    """
    Retrieve relevant chunks.
    Priority:
    1. Qdrant vector search (if available)
    2. Fallback: simple SQL ILIKE keyword search
    """
    client = get_qdrant_client()
    query_emb = get_embedding(query)

    # ---- Path 1: Qdrant ----
    if client and query_emb:
        collection_name = f"{settings.QDRANT_COLLECTION_PREFIX}_{organization_id}"
        try:
            results = client.search(
                collection_name=collection_name,
                query_vector=query_emb,
                limit=top_k,
                query_filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="organization_id",
                            match=qmodels.MatchValue(value=str(organization_id)),
                        )
                    ]
                ),
            )
            return [
                {
                    "content": hit.payload.get("content", ""),
                    "document_id": hit.payload.get("document_id"),
                    "score": hit.score,
                    "chunk_index": hit.payload.get("chunk_index"),
                }
                for hit in results
            ]
        except (ConnectionError, TimeoutError, ValueError):
            # The SQL keyword path remains available when the optional vector service is down.
            client = None

    # ---- Path 2: Simple keyword fallback ----
    keywords = [w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) > 3][:8]
    if not keywords:
        return []

    filters = [DocumentChunk.content.ilike(f"%{kw}%") for kw in keywords]
    chunks = (
        db.query(DocumentChunk)
        .filter(
            DocumentChunk.organization_id == organization_id,
            or_(*filters),
        )
        .limit(max(top_k * 4, 20))
        .all()
    )

    scored = []
    for chunk in chunks:
        content = chunk.content.lower()
        frequency = sum(content.count(keyword) for keyword in keywords)
        coverage = sum(keyword in content for keyword in keywords) / len(keywords)
        score = min(0.99, 0.35 + (0.08 * frequency) + (0.35 * coverage))
        scored.append(
            {
                "content": chunk.content,
                "document_id": str(chunk.document_id),
                "score": score,
                "chunk_index": chunk.chunk_index,
            }
        )
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]
