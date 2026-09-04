"""Repository for Question and QuestionOption persistence."""

from __future__ import annotations

import logging
from datetime import datetime

from thelocaltutor.domain.models import Difficulty, Question, QuestionOption, QuestionType
from thelocaltutor.infrastructure.database.connection import get_connection, transaction

log = logging.getLogger(__name__)


def _load_options(conn, question_id: int) -> list[QuestionOption]:
    rows = conn.execute(
        "SELECT * FROM question_options WHERE question_id=? ORDER BY letter",
        (question_id,),
    ).fetchall()
    return [QuestionOption(letter=r["letter"], text=r["option_text"], is_correct=bool(r["is_correct"])) for r in rows]


def _row_to_question(row, options: list[QuestionOption]) -> Question:
    return Question(
        id=row["id"],
        material_id=row["material_id"],
        question_type=QuestionType(row["question_type"]),
        difficulty=Difficulty(row["difficulty"]),
        question_text=row["question_text"],
        correct_answer=row["correct_answer"],
        explanation=row["explanation"],
        topic=row["topic"],
        source_page=row["source_page"],
        date_created=datetime.fromisoformat(row["date_created"]),
        options=options,
    )


def list_for_material(material_id: int) -> list[Question]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM questions WHERE material_id=? ORDER BY date_created DESC",
        (material_id,),
    ).fetchall()
    questions = []
    for row in rows:
        opts = _load_options(conn, row["id"])
        questions.append(_row_to_question(row, opts))
    return questions


def get_by_ids(question_ids: list[int]) -> list[Question]:
    if not question_ids:
        return []
    conn = get_connection()
    placeholders = ",".join("?" * len(question_ids))
    rows = conn.execute(
        f"SELECT * FROM questions WHERE id IN ({placeholders})",
        question_ids,
    ).fetchall()
    result = []
    for row in rows:
        opts = _load_options(conn, row["id"])
        result.append(_row_to_question(row, opts))
    # Preserve requested order
    id_order = {qid: i for i, qid in enumerate(question_ids)}
    result.sort(key=lambda q: id_order.get(q.id, 999))
    return result


def get_by_id(question_id: int) -> Question | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM questions WHERE id=?", (question_id,)).fetchone()
    if not row:
        return None
    opts = _load_options(conn, question_id)
    return _row_to_question(row, opts)


def insert_many(material_id: int, questions: list[Question]) -> list[int]:
    ids: list[int] = []
    with transaction() as conn:
        for q in questions:
            cur = conn.execute(
                "INSERT INTO questions (material_id, question_type, difficulty, question_text, "
                "correct_answer, explanation, topic, source_page, date_created) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    material_id,
                    q.question_type.value,
                    q.difficulty.value,
                    q.question_text,
                    q.correct_answer,
                    q.explanation,
                    q.topic,
                    q.source_page,
                    datetime.now().isoformat(),
                ),
            )
            qid = cur.lastrowid
            ids.append(qid)  # type: ignore[arg-type]
            if q.options:
                conn.executemany(
                    "INSERT INTO question_options (question_id, letter, option_text, is_correct) VALUES (?,?,?,?)",
                    [(qid, opt.letter, opt.text, int(opt.is_correct)) for opt in q.options],
                )
    return ids


def delete_for_material(material_id: int) -> int:
    with transaction() as conn:
        cur = conn.execute("DELETE FROM questions WHERE material_id=?", (material_id,))
        return cur.rowcount


def count_for_material(material_id: int) -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS c FROM questions WHERE material_id=?", (material_id,)).fetchone()
    return row["c"]


def count_all() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS c FROM questions").fetchone()
    return row["c"]
