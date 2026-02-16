import re

import structlog
import tiktoken
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from watchdog.config import settings
from watchdog.database import async_session_factory
from watchdog.models.document import Chunk, Document

log = structlog.get_logger()

_encoder = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_encoder.encode(text))


def split_into_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs, preserving structure."""
    # Split on double newlines (paragraph boundaries)
    paragraphs = re.split(r"\n\s*\n", text)
    # Filter empty paragraphs and strip whitespace
    return [p.strip() for p in paragraphs if p.strip()]


def chunk_text(
    text: str,
    max_tokens: int = settings.chunk_size_tokens,
    overlap_tokens: int = settings.chunk_overlap_tokens,
) -> list[dict]:
    """Split text into semantic-aware chunks with overlap.

    Returns list of dicts with keys: text, token_count, char_start, char_end
    """
    paragraphs = split_into_paragraphs(text)
    if not paragraphs:
        return []

    chunks = []
    current_paragraphs: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)

        # If single paragraph exceeds max, split by sentences
        if para_tokens > max_tokens:
            # Flush current buffer first
            if current_paragraphs:
                chunk_text_str = "\n\n".join(current_paragraphs)
                chunks.append({
                    "text": chunk_text_str,
                    "token_count": count_tokens(chunk_text_str),
                })
                current_paragraphs = []
                current_tokens = 0

            # Split long paragraph by sentences
            sentences = re.split(r"(?<=[.!?])\s+", para)
            sent_buffer: list[str] = []
            sent_tokens = 0
            for sent in sentences:
                st = count_tokens(sent)
                if sent_tokens + st > max_tokens and sent_buffer:
                    chunk_text_str = " ".join(sent_buffer)
                    chunks.append({
                        "text": chunk_text_str,
                        "token_count": count_tokens(chunk_text_str),
                    })
                    # Overlap: keep last few sentences
                    overlap_buf: list[str] = []
                    overlap_t = 0
                    for s in reversed(sent_buffer):
                        t = count_tokens(s)
                        if overlap_t + t > overlap_tokens:
                            break
                        overlap_buf.insert(0, s)
                        overlap_t += t
                    sent_buffer = overlap_buf
                    sent_tokens = overlap_t

                sent_buffer.append(sent)
                sent_tokens += st

            if sent_buffer:
                chunk_text_str = " ".join(sent_buffer)
                chunks.append({
                    "text": chunk_text_str,
                    "token_count": count_tokens(chunk_text_str),
                })
            continue

        # Would adding this paragraph exceed the limit?
        if current_tokens + para_tokens > max_tokens and current_paragraphs:
            chunk_text_str = "\n\n".join(current_paragraphs)
            chunks.append({
                "text": chunk_text_str,
                "token_count": count_tokens(chunk_text_str),
            })

            # Overlap: keep trailing paragraphs that fit within overlap budget
            overlap_paras: list[str] = []
            overlap_t = 0
            for p in reversed(current_paragraphs):
                t = count_tokens(p)
                if overlap_t + t > overlap_tokens:
                    break
                overlap_paras.insert(0, p)
                overlap_t += t
            current_paragraphs = overlap_paras
            current_tokens = overlap_t

        current_paragraphs.append(para)
        current_tokens += para_tokens

    # Flush remaining
    if current_paragraphs:
        chunk_text_str = "\n\n".join(current_paragraphs)
        chunks.append({
            "text": chunk_text_str,
            "token_count": count_tokens(chunk_text_str),
        })

    return chunks


def estimate_page(char_offset: int, text: str, page_count: int) -> int:
    """Rough page estimation based on character position."""
    if page_count <= 1:
        return 1
    total_chars = len(text)
    if total_chars == 0:
        return 1
    return min(max(1, int((char_offset / total_chars) * page_count) + 1), page_count)


async def run_chunking(limit: int | None = None) -> int:
    """Chunk all OCR'd documents that haven't been chunked yet."""
    async with async_session_factory() as session:
        query = select(Document).where(Document.status == "ocr_done")
        if limit:
            query = query.limit(limit)

        result = await session.execute(query)
        documents = result.scalars().all()

        total_chunks = 0
        for doc in documents:
            if not doc.ocr_text:
                log.warning("no_ocr_text", document_id=doc.id)
                continue

            # Check if already chunked
            existing = await session.execute(
                select(Chunk).where(Chunk.document_id == doc.id).limit(1)
            )
            if existing.scalar_one_or_none():
                log.info("already_chunked", document_id=doc.id)
                doc.status = "chunked"
                continue

            chunks = chunk_text(doc.ocr_text)
            page_count = doc.page_count or 1
            char_offset = 0

            for i, chunk_data in enumerate(chunks):
                page_start = estimate_page(char_offset, doc.ocr_text, page_count)
                char_offset += len(chunk_data["text"])
                page_end = estimate_page(char_offset, doc.ocr_text, page_count)

                chunk = Chunk(
                    document_id=doc.id,
                    chunk_index=i,
                    text=chunk_data["text"],
                    token_count=chunk_data["token_count"],
                    page_start=page_start,
                    page_end=page_end,
                )
                session.add(chunk)

            doc.status = "chunked"
            total_chunks += len(chunks)
            log.info("document_chunked", document_id=doc.id, chunks=len(chunks))

        await session.commit()

    log.info("chunking_complete", total_chunks=total_chunks)
    return total_chunks
