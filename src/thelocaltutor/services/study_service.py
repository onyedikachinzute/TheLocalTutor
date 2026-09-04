"""Business logic for practice sessions and grading."""

from __future__ import annotations

import logging
import random

from thelocaltutor.domain.models import (
    AppStats,
    Question,
    QuestionType,
    SessionMode,
    SessionResult,
    StudySession,
)
from thelocaltutor.infrastructure.database.repositories import (
    material_repo,
    question_repo,
    session_repo,
)
from thelocaltutor.services.question_service import grade_short_answer

log = logging.getLogger(__name__)


def start_session(
    material_id: int,
    mode: SessionMode = SessionMode.PRACTICE,
    max_questions: int | None = None,
    question_type_filter: list[str] | None = None,
) -> tuple[int, list[Question]]:
    """Create a session, return (session_id, shuffled questions)."""
    all_questions = question_repo.list_for_material(material_id)
    if not all_questions:
        raise ValueError("No questions available for this material. Generate some first.")

    if question_type_filter:
        all_questions = [q for q in all_questions if q.question_type.value in question_type_filter]

    if not all_questions:
        raise ValueError("No questions match the selected filters.")

    random.shuffle(all_questions)
    if max_questions and max_questions < len(all_questions):
        all_questions = all_questions[:max_questions]

    question_ids = [q.id for q in all_questions]
    session_id = session_repo.create_session(material_id, mode, question_ids)
    log.info("Started session %d for material %d (%d questions)", session_id, material_id, len(all_questions))
    return session_id, all_questions


def submit_answer(
    session_id: int,
    question: Question,
    user_answer: str,
    time_taken: int = 0,
) -> bool:
    """Grade answer, persist attempt, return is_correct."""
    is_correct = _grade(question, user_answer)
    session_repo.record_attempt(session_id, question.id, user_answer, is_correct, time_taken)
    return is_correct


def finish_session(session_id: int) -> SessionResult:
    session_repo.complete_session(session_id)
    session = session_repo.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")
    attempts = session_repo.get_attempts_for_session(session_id)
    questions = question_repo.get_by_ids(session.question_ids)
    return SessionResult(session=session, attempts=attempts, questions=questions)


def get_result(session_id: int) -> SessionResult:
    session = session_repo.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")
    attempts = session_repo.get_attempts_for_session(session_id)
    questions = question_repo.get_by_ids(session.question_ids)
    return SessionResult(session=session, attempts=attempts, questions=questions)


def get_app_stats() -> AppStats:
    mat_stats = material_repo.get_stats()
    total_questions = question_repo.count_all()
    total_sessions = session_repo.count_all()
    global_stats = session_repo.get_global_stats()
    return AppStats(
        total_materials=mat_stats["total"],
        total_questions=total_questions,
        total_sessions=total_sessions,
        total_correct=global_stats["total_correct"],
        total_attempted=global_stats["total_attempted"],
    )


def _grade(question: Question, user_answer: str) -> bool:
    ua = user_answer.strip()
    ca = question.correct_answer.strip()

    if question.question_type == QuestionType.MCQ:
        return ua.upper() == ca.upper()

    if question.question_type == QuestionType.TRUE_FALSE:
        return ua.lower() in (ca.lower(), ca.lower()[0])

    if question.question_type == QuestionType.SHORT_ANSWER:
        return grade_short_answer(ua, ca)

    return ua.lower() == ca.lower()
