import fitz  # PyMuPDF
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from watchdog.database import async_session_factory
from watchdog.models.document import Document

log = structlog.get_logger()


def extract_text_pymupdf(file_path: str) -> tuple[str, int]:
    """Extract text from PDF using PyMuPDF. Returns (text, page_count)."""
    doc = fitz.open(file_path)
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n\n".join(pages), len(pages)


def extract_text_tesseract(file_path: str) -> tuple[str, int]:
    """Fallback: OCR scanned PDF pages with Tesseract."""
    import pytesseract
    from PIL import Image as PILImage

    doc = fitz.open(file_path)
    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        # Render page to image at 300 DPI
        pix = page.get_pixmap(dpi=300)
        img = PILImage.frombytes("RGB", (pix.width, pix.height), pix.samples)
        text = pytesseract.image_to_string(img)
        pages.append(text)
    doc.close()
    return "\n\n".join(pages), len(pages)


def ocr_document(file_path: str) -> tuple[str, int, str]:
    """OCR a document. Try PyMuPDF first, fall back to Tesseract.

    Returns (text, page_count, method).
    """
    if file_path.endswith(".txt"):
        with open(file_path, encoding="utf-8") as f:
            text = f.read()
        return text, 1, "plain_text"

    # Try PyMuPDF text extraction first
    text, page_count = extract_text_pymupdf(file_path)

    # If we got meaningful text, use it
    if len(text.strip()) > 100:
        return text, page_count, "pymupdf"

    # Fallback to Tesseract for scanned PDFs
    log.info("pymupdf_insufficient_text", file_path=file_path, text_len=len(text.strip()))
    try:
        text, page_count = extract_text_tesseract(file_path)
        return text, page_count, "tesseract"
    except Exception as e:
        log.warning("tesseract_failed", file_path=file_path, error=str(e))
        # Return whatever PyMuPDF got
        return text, page_count, "pymupdf_fallback"


async def run_ocr(limit: int | None = None) -> int:
    """Run OCR on all downloaded documents that haven't been OCR'd yet."""
    async with async_session_factory() as session:
        query = select(Document).where(Document.status == "downloaded")
        if limit:
            query = query.limit(limit)

        result = await session.execute(query)
        documents = result.scalars().all()

        processed = 0
        for doc in documents:
            if not doc.file_path:
                log.warning("no_file_path", document_id=doc.id)
                continue

            try:
                text, page_count, method = ocr_document(doc.file_path)
                doc.ocr_text = text
                doc.page_count = page_count
                doc.ocr_method = method
                doc.status = "ocr_done"
                processed += 1
                log.info(
                    "ocr_complete",
                    document_id=doc.id,
                    method=method,
                    pages=page_count,
                    text_len=len(text),
                )
            except Exception as e:
                log.error("ocr_failed", document_id=doc.id, error=str(e))
                doc.status = "ocr_failed"

        await session.commit()

    log.info("ocr_batch_complete", processed=processed)
    return processed
