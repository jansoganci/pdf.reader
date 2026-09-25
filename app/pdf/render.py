import shutil
from pathlib import Path

import fitz

from app.config import settings


class PdfRejected(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def render_pdf(data: bytes, work_dir: Path) -> list[tuple[int, bytes]]:
    if len(data) > settings.max_upload_bytes:
        raise PdfRejected("File was not accepted. The limit is 30 MB.")
    if not data.startswith(b"%PDF"):
        raise PdfRejected("File was not accepted. Upload one PDF.")
    try:
        document = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise PdfRejected("File could not be opened.") from exc
    if document.needs_pass or document.is_encrypted:
        document.close()
        raise PdfRejected("File was not accepted. Encrypted PDFs are not supported.")
    if document.page_count == 0:
        document.close()
        raise PdfRejected("File could not be opened.")
    if document.page_count > settings.max_pages:
        document.close()
        raise PdfRejected(f"File was not accepted. The limit is {settings.max_pages} pages.")
    work_dir.mkdir(parents=True, exist_ok=True)
    pages: list[tuple[int, bytes]] = []
    try:
        for index, page in enumerate(document, start=1):
            zoom = 150 / 72
            rect = page.rect
            long_edge = max(rect.width, rect.height) * zoom
            if long_edge > 2000:
                zoom *= 2000 / long_edge
            pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            image = pixmap.tobytes("jpeg", jpg_quality=80)
            if len(image) > 8 * 1024 * 1024:
                raise PdfRejected("File could not be opened. A page image is too large.")
            path = work_dir / f"page_{index}.jpg"
            path.write_bytes(image)
            pages.append((index, image))
    finally:
        document.close()
    return pages


def render_page_preview(data: bytes, page_number: int) -> bytes:
    document = fitz.open(stream=data, filetype="pdf")
    try:
        page = document[page_number - 1]
        zoom = 110 / 72
        return page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False).tobytes("jpeg", jpg_quality=70)
    finally:
        document.close()


def cleanup_renders(work_dir: Path) -> None:
    if work_dir.exists():
        shutil.rmtree(work_dir, ignore_errors=True)
