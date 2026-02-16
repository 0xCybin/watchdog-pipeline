from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from watchdog.api.deps import DbSession
from watchdog.models.document import Chunk, Document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
async def list_documents(
    db: DbSession,
    status: str | None = None,
    sort: str = Query(default="created_at", enum=["created_at", "priority"]),
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    order = Document.priority_score.desc().nulls_last() if sort == "priority" else Document.created_at.desc()
    query = select(Document).offset(offset).limit(limit).order_by(order)
    if status:
        query = query.where(Document.status == status)

    result = await db.execute(query)
    docs = result.scalars().all()

    count_query = select(func.count(Document.id))
    if status:
        count_query = count_query.where(Document.status == status)
    total = (await db.execute(count_query)).scalar()

    return {
        "total": total,
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "source_type": d.source_type,
                "status": d.status,
                "page_count": d.page_count,
                "priority_score": d.priority_score,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ],
    }


@router.get("/{document_id}")
async def get_document(document_id: str, db: DbSession):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunk_result = await db.execute(
        select(Chunk)
        .where(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index)
    )
    chunks = chunk_result.scalars().all()

    return {
        "id": doc.id,
        "filename": doc.filename,
        "source_type": doc.source_type,
        "source_url": doc.source_url,
        "status": doc.status,
        "page_count": doc.page_count,
        "ocr_method": doc.ocr_method,
        "priority_score": doc.priority_score,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "chunks": [
            {
                "id": c.id,
                "chunk_index": c.chunk_index,
                "text": c.filtered_text or c.text,
                "token_count": c.token_count,
                "page_start": c.page_start,
                "page_end": c.page_end,
            }
            for c in chunks
        ],
    }
