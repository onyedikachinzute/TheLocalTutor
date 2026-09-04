"""PDF text extractor using PyMuPDF (fitz)."""

from __future__ import annotations

import logging

from thelocaltutor.core.exceptions import DocumentProcessingError
from thelocaltutor.infrastructure.document.base_parser import BaseParser, ParsedPage

log = logging.getLogger(__name__)


class PdfParser(BaseParser):
    def supports(self, file_path: str) -> bool:
        return file_path.lower().endswith(".pdf")

    def parse(self, file_path: str) -> list[ParsedPage]:
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:
            raise DocumentProcessingError("PyMuPDF is not installed. Run: pip install pymupdf") from exc

        pages: list[ParsedPage] = []
        try:
            doc = fitz.open(file_path)
            for i, page in enumerate(doc, start=1):
                text = page.get_text("text")  # type: ignore[attr-defined]
                cleaned = _clean(text)
                if cleaned:
                    pages.append(ParsedPage(page_number=i, text=cleaned))
            doc.close()
        except Exception as exc:
            raise DocumentProcessingError(f"Failed to parse PDF: {exc}") from exc

        log.info("PDF parsed: %d pages with text from %s", len(pages), file_path)
        return pages


def _clean(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    lines = [l for l in lines if l]
    return "\n".join(lines)
