"""Business logic for importing and managing study materials."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from thelocaltutor.core import config
from thelocaltutor.core.exceptions import UnsupportedFormatError
from thelocaltutor.domain.models import DocumentChunk, FileType, Material, MaterialStatus
from thelocaltutor.infrastructure.database.repositories import material_repo
from thelocaltutor.infrastructure.document.base_parser import ParsedPage
from thelocaltutor.infrastructure.document.pdf_parser import PdfParser
from thelocaltutor.infrastructure.document.pptx_parser import PptxParser

log = logging.getLogger(__name__)

_PARSERS = [PdfParser(), PptxParser()]
_SUPPORTED = {".pdf": FileType.PDF, ".pptx": FileType.PPTX}


def import_file(source_path: str, course: str = "") -> int:
    """Copy file into managed storage, create DB record, return material_id."""
    src = Path(source_path)
    suffix = src.suffix.lower()
    if suffix not in _SUPPORTED:
        raise UnsupportedFormatError(f"Unsupported file format: {suffix}")

    config.MATERIALS_DIR.mkdir(parents=True, exist_ok=True)
    dest = config.MATERIALS_DIR / src.name
    # Avoid name collisions
    counter = 1
    while dest.exists():
        dest = config.MATERIALS_DIR / f"{src.stem}_{counter}{src.suffix}"
        counter += 1

    shutil.copy2(src, dest)
    file_type = _SUPPORTED[suffix]
    material_id = material_repo.insert(
        name=src.stem,
        file_path=str(dest),
        file_type=file_type,
        course=course,
    )
    log.info("Imported material id=%d from %s", material_id, source_path)
    return material_id


def process_material(material_id: int) -> Material:
    """Parse document, split into chunks, persist. Returns updated material."""
    material = material_repo.get_by_id(material_id)
    if not material:
        raise ValueError(f"Material {material_id} not found")

    material_repo.update_status(material_id, MaterialStatus.PROCESSING)

    try:
        pages = _parse(material.file_path)
        chunks = _chunk_pages(pages, material_id)
        material_repo.insert_chunks(material_id, chunks)
        material_repo.update_after_processing(material_id, len(pages), len(chunks))
        log.info("Processed material %d: %d pages → %d chunks", material_id, len(pages), len(chunks))
    except Exception as exc:
        material_repo.update_status(material_id, MaterialStatus.ERROR, str(exc))
        raise

    return material_repo.get_by_id(material_id)  # type: ignore[return-value]


def _parse(file_path: str) -> list[ParsedPage]:
    for parser in _PARSERS:
        if parser.supports(file_path):
            return parser.parse(file_path)
    raise UnsupportedFormatError(f"No parser for {file_path}")


def _chunk_pages(pages: list[ParsedPage], material_id: int) -> list[DocumentChunk]:
    chunk_size = config.get("chunk_size")
    overlap = config.get("chunk_overlap")
    chunks: list[DocumentChunk] = []
    idx = 0

    for page in pages:
        text = page.text
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    DocumentChunk(
                        id=0,
                        material_id=material_id,
                        page_number=page.page_number,
                        chunk_index=idx,
                        content=chunk_text,
                    )
                )
                idx += 1
            start = end - overlap if end < len(text) else len(text)

    return chunks


def delete_material(material_id: int) -> None:
    material = material_repo.get_by_id(material_id)
    if material:
        try:
            Path(material.file_path).unlink(missing_ok=True)
        except Exception:
            pass
        material_repo.delete(material_id)


def list_materials() -> list[Material]:
    return material_repo.list_all()


def get_material(material_id: int) -> Material | None:
    return material_repo.get_by_id(material_id)
