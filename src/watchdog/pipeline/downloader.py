from pathlib import Path

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from watchdog.config import settings
from watchdog.database import async_session_factory
from watchdog.models.document import Document
from watchdog.utils.hashing import sha256_file

log = structlog.get_logger()

# File extensions to ingest from the local archive
DOCUMENT_EXTENSIONS = {
    ".pdf", ".txt", ".doc", ".docx",
    ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif",
    ".csv", ".xls", ".xlsx",
    ".html", ".htm",
    ".rtf",
}

# Extensions where we can read text directly (skip OCR)
TEXT_EXTENSIONS = {".txt", ".csv", ".html", ".htm", ".rtf"}


async def ingest_local_documents(
    session: AsyncSession,
    archive_dir: Path,
    limit: int = 100,
) -> list[Document]:
    """Scan a local archive directory and ingest document files into the DB.

    Files are referenced in-place (no copy). PDFs get status="downloaded"
    (need OCR), text files get status="ocr_done" (text read directly).
    Idempotent — skips files already in DB by SHA-256 hash.
    """
    if not archive_dir.exists():
        raise FileNotFoundError(f"Archive directory not found: {archive_dir}")

    log.info("scanning_archive", archive_dir=str(archive_dir))

    documents: list[Document] = []
    scanned = 0
    skipped_ext = 0
    skipped_dup = 0

    for file_path in sorted(archive_dir.rglob("*")):
        if len(documents) >= limit:
            break

        if not file_path.is_file():
            continue

        suffix = file_path.suffix.lower()
        if suffix not in DOCUMENT_EXTENSIONS:
            skipped_ext += 1
            continue

        scanned += 1

        # Compute hash for dedup
        file_hash = sha256_file(file_path)

        # Skip if already in DB
        existing = await session.execute(
            select(Document.id).where(Document.sha256 == file_hash)
        )
        if existing.scalar_one_or_none():
            skipped_dup += 1
            if scanned % 500 == 0:
                log.debug("scan_progress", scanned=scanned, ingested=len(documents), skipped_dup=skipped_dup)
            continue

        # Determine status based on file type
        if suffix in TEXT_EXTENSIONS:
            try:
                ocr_text = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                ocr_text = file_path.read_text(encoding="latin-1", errors="replace")
            status = "ocr_done"
            ocr_method = "direct_read"
        else:
            ocr_text = None
            status = "downloaded"
            ocr_method = None

        doc = Document(
            source_url=None,
            source_type="local_archive",
            filename=file_path.name,
            file_path=str(file_path),
            sha256=file_hash,
            ocr_text=ocr_text,
            ocr_method=ocr_method,
            status=status,
        )
        session.add(doc)
        documents.append(doc)

        if len(documents) % 100 == 0:
            await session.flush()
            log.info("ingest_progress", ingested=len(documents), scanned=scanned)

    await session.commit()
    log.info(
        "ingest_complete",
        ingested=len(documents),
        scanned=scanned,
        skipped_ext=skipped_ext,
        skipped_dup=skipped_dup,
    )
    return documents


async def run_download(limit: int = 100, archive_dir: Path | None = None) -> dict[str, int]:
    """Run the download/ingest step.

    If archive_dir is provided (or configured via ARCHIVE_DIR), ingests
    local files. Otherwise raises an error telling the user to configure it.
    """
    archive_dir = archive_dir or settings.archive_dir

    if archive_dir is None:
        raise ValueError(
            "No archive directory configured. Set ARCHIVE_DIR in .env or pass --archive-path."
        )

    async with async_session_factory() as session:
        docs = await ingest_local_documents(session, archive_dir=archive_dir, limit=limit)

    return {"local_archive": len(docs), "total": len(docs)}
