"""Repository for Material and DocumentChunk persistence."""

from __future__ import annotations

import logging
from datetime import datetime

from thelocaltutor.domain.models import (
    DocumentChunk,
    FileType,
    Material,
    MaterialStatus,
)
from thelocaltutor.infrastructure.database.connection import get_connection, transaction

log = logging.getLogger(__name__)


def _row_to_material(row) -> Material:
    return Material(
        id=row["id"],
        name=row["name"],
        file_path=row["file_path"],
        file_type=FileType(row["file_type"]),
        date_added=datetime.fromisoformat(row["date_added"]),
        page_count=row["page_count"],
        status=MaterialStatus(row["status"]),
        course=row["course"],
        error_message=row["error_message"],
        chunk_count=row["chunk_count"],
    )


def list_all() -> list[Material]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT m.*, (SELECT COUNT(*) FROM questions WHERE material_id = m.id) AS question_count "
        "FROM materials m ORDER BY date_added DESC"
    ).fetchall()
    materials = []
    for row in rows:
        m = _row_to_material(row)
        m.question_count = row["question_count"]
        materials.append(m)
    return materials


def get_by_id(material_id: int) -> Material | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT m.*, (SELECT COUNT(*) FROM questions WHERE material_id = m.id) AS question_count "
        "FROM materials m WHERE m.id = ?",
        (material_id,),
    ).fetchone()
    if not row:
        return None
    m = _row_to_material(row)
    m.question_count = row["question_count"]
    return m


def insert(
    name: str,
    file_path: str,
    file_type: FileType,
    page_count: int = 0,
    course: str = "",
) -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO materials (name, file_path, file_type, date_added, page_count, status, course) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, file_path, file_type.value, datetime.now().isoformat(), page_count, MaterialStatus.PENDING.value, course),
        )
        return cur.lastrowid  # type: ignore[return-value]


def update_status(material_id: int, status: MaterialStatus, error_message: str = "") -> None:
    with transaction() as conn:
        conn.execute(
            "UPDATE materials SET status=?, error_message=? WHERE id=?",
            (status.value, error_message, material_id),
        )


def update_after_processing(material_id: int, page_count: int, chunk_count: int) -> None:
    with transaction() as conn:
        conn.execute(
            "UPDATE materials SET page_count=?, chunk_count=?, status=? WHERE id=?",
            (page_count, chunk_count, MaterialStatus.READY.value, material_id),
        )


def delete(material_id: int) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM materials WHERE id=?", (material_id,))


def insert_chunks(material_id: int, chunks: list[DocumentChunk]) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM document_chunks WHERE material_id=?", (material_id,))
        conn.executemany(
            "INSERT INTO document_chunks (material_id, page_number, chunk_index, content) VALUES (?,?,?,?)",
            [(material_id, c.page_number, c.chunk_index, c.content) for c in chunks],
        )


def get_chunks(material_id: int, limit: int = 0) -> list[DocumentChunk]:
    conn = get_connection()
    sql = "SELECT * FROM document_chunks WHERE material_id=? ORDER BY chunk_index"
    params: tuple = (material_id,)
    if limit > 0:
        sql += " LIMIT ?"
        params = (material_id, limit)
    rows = conn.execute(sql, params).fetchall()
    return [
        DocumentChunk(
            id=r["id"],
            material_id=r["material_id"],
            page_number=r["page_number"],
            chunk_index=r["chunk_index"],
            content=r["content"],
        )
        for r in rows
    ]


def get_stats() -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS total, "
        "SUM(CASE WHEN status='ready' THEN 1 ELSE 0 END) AS ready "
        "FROM materials"
    ).fetchone()
    return {"total": row["total"] or 0, "ready": row["ready"] or 0}
