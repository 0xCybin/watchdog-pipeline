import numpy as np
import structlog
from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from watchdog.config import settings
from watchdog.database import async_session_factory
from watchdog.models.document import Chunk

log = structlog.get_logger()

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        log.info("loading_embedding_model", model=settings.embedding_model)
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def embed_texts(texts: list[str], batch_size: int = 64) -> list[list[float]]:
    """Encode texts into 384-dim embeddings."""
    model = get_model()
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.tolist()


async def run_embeddings(batch_size: int = 100) -> int:
    """Generate embeddings for all chunks that don't have them."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Chunk).where(Chunk.embedding.is_(None)).limit(10000)
        )
        chunks = result.scalars().all()

        if not chunks:
            log.info("no_chunks_need_embeddings")
            return 0

        total = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c.text for c in batch]
            embeddings = embed_texts(texts)

            for chunk, emb in zip(batch, embeddings):
                chunk.embedding = emb

            total += len(batch)
            log.info("embeddings_generated", batch=i // batch_size + 1, count=len(batch))

        await session.commit()

    log.info("embedding_complete", total=total)
    return total


async def search_similar(query: str, session: AsyncSession, limit: int = 10) -> list[dict]:
    """Semantic similarity search using pgvector cosine distance."""
    query_embedding = embed_texts([query])[0]

    # Use pgvector cosine distance operator
    result = await session.execute(
        select(Chunk)
        .where(Chunk.embedding.isnot(None))
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    chunks = result.scalars().all()

    return [
        {
            "chunk_id": c.id,
            "document_id": c.document_id,
            "text": c.filtered_text or c.text,
            "token_count": c.token_count,
            "page_start": c.page_start,
            "page_end": c.page_end,
            "score": float(1 - np.dot(query_embedding, c.embedding)) if c.embedding else 0,
        }
        for c in chunks
    ]
