"""Repository for StudySession and Attempt persistence."""

from __future__ import annotations

import logging
from datetime import datetime

from thelocaltutor.domain.models import Attempt, SessionMode, StudySession
from thelocaltutor.infrastructure.database.connection import get_connection, transaction

log = logging.getLogger(__name__)


def _row_to_session(row) -> StudySession:
    return StudySession(
        id=row["id"],
        material_id=row["material_id"],
        mode=SessionMode(row["mode"]),
        started_at=datetime.fromisoformat(row["started_at"]),
        ended_at=datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else None,
        total_questions=row["total_questions"],
        correct_count=row["correct_count"],
        score_percent=row["score_percent"],
    )


def create_session(material_id: int, mode: SessionMode, question_ids: list[int]) -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO study_sessions (material_id, mode, started_at, total_questions) VALUES (?,?,?,?)",
            (material_id, mode.value, datetime.now().isoformat(), len(question_ids)),
        )
        session_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO session_questions (session_id, question_id, position) VALUES (?,?,?)",
            [(session_id, qid, i) for i, qid in enumerate(question_ids)],
        )
    return session_id  # type: ignore[return-value]


def complete_session(session_id: int) -> None:
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS total, SUM(is_correct) AS correct FROM attempts WHERE session_id=?",
        (session_id,),
    ).fetchone()
    total = row["total"] or 0
    correct = int(row["correct"] or 0)
    score = round(correct / total * 100, 1) if total else 0.0
    with transaction() as conn2:
        conn2.execute(
            "UPDATE study_sessions SET ended_at=?, correct_count=?, score_percent=? WHERE id=?",
            (datetime.now().isoformat(), correct, score, session_id),
        )


def record_attempt(
    session_id: int,
    question_id: int,
    user_answer: str,
    is_correct: bool,
    time_taken: int = 0,
) -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO attempts (session_id, question_id, user_answer, is_correct, time_taken_seconds, timestamp) "
            "VALUES (?,?,?,?,?,?)",
            (session_id, question_id, user_answer, int(is_correct), time_taken, datetime.now().isoformat()),
        )
        return cur.lastrowid  # type: ignore[return-value]


def get_session(session_id: int) -> StudySession | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM study_sessions WHERE id=?", (session_id,)).fetchone()
    if not row:
        return None
    session = _row_to_session(row)
    qrows = conn.execute(
        "SELECT question_id FROM session_questions WHERE session_id=? ORDER BY position",
        (session_id,),
    ).fetchall()
    session.question_ids = [r["question_id"] for r in qrows]
    return session


def get_attempts_for_session(session_id: int) -> list[Attempt]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM attempts WHERE session_id=? ORDER BY timestamp",
        (session_id,),
    ).fetchall()
    return [
        Attempt(
            id=r["id"],
            session_id=r["session_id"],
            question_id=r["question_id"],
            user_answer=r["user_answer"],
            is_correct=bool(r["is_correct"]),
            time_taken_seconds=r["time_taken_seconds"],
            timestamp=datetime.fromisoformat(r["timestamp"]),
        )
        for r in rows
    ]


def list_sessions_for_material(material_id: int) -> list[StudySession]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM study_sessions WHERE material_id=? ORDER BY started_at DESC",
        (material_id,),
    ).fetchall()
    return [_row_to_session(r) for r in rows]


def count_all() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS c FROM study_sessions WHERE ended_at IS NOT NULL").fetchone()
    return row["c"]


def get_global_stats() -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS total, SUM(is_correct) AS correct FROM attempts"
    ).fetchone()
    return {
        "total_attempted": row["total"] or 0,
        "total_correct": int(row["correct"] or 0),
    }
