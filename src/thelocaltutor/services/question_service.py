"""Business logic for generating and managing questions."""

from __future__ import annotations

import logging
import random

from thelocaltutor.core import config
from thelocaltutor.domain.models import Question
from thelocaltutor.infrastructure.ai import ollama_provider
from thelocaltutor.infrastructure.database.repositories import material_repo, question_repo

log = logging.getLogger(__name__)


def generate_for_material(
    material_id: int,
    count: int,
    question_types: list[str],
    difficulty: str,
    model: str | None = None,
) -> list[Question]:
    """Generate questions from a material's chunks, persist, and return them."""
    max_chunks = config.get("max_chunks_per_generation")
    chunks = material_repo.get_chunks(material_id)
    if not chunks:
        raise ValueError("Material has no content chunks. Re-import and reprocess it.")

    # Sample chunks distributed across the document
    if len(chunks) > max_chunks:
        step = len(chunks) / max_chunks
        selected = [chunks[int(i * step)] for i in range(max_chunks)]
    else:
        selected = chunks

    content = "\n\n---\n\n".join(c.content for c in selected)

    log.info(
        "Generating %d questions for material %d using %d chunks",
        count, material_id, len(selected),
    )
    questions = ollama_provider.generate_questions(
        material_id=material_id,
        content=content,
        count=count,
        question_types=question_types,
        difficulty=difficulty,
        model=model,
    )

    ids = question_repo.insert_many(material_id, questions)
    saved = question_repo.get_by_ids(ids)
    log.info("Saved %d questions for material %d", len(saved), material_id)
    return saved


def list_questions(material_id: int) -> list[Question]:
    return question_repo.list_for_material(material_id)


def delete_questions(material_id: int) -> int:
    return question_repo.delete_for_material(material_id)


def ai_available() -> bool:
    return ollama_provider.is_available()


def available_models() -> list[str]:
    return ollama_provider.list_models()


def grade_short_answer(user_answer: str, correct_answer: str) -> bool:
    """Simple keyword-overlap grading for short-answer questions."""
    def tokens(s: str) -> set[str]:
        import re
        words = re.findall(r"[a-z0-9]+", s.lower())
        stopwords = {"the", "a", "an", "is", "it", "in", "of", "and", "or", "to", "be", "are", "was", "for"}
        return {w for w in words if w not in stopwords}

    answer_tokens = tokens(user_answer)
    correct_tokens = tokens(correct_answer)
    if not correct_tokens:
        return bool(user_answer.strip())
    overlap = len(answer_tokens & correct_tokens)
    return overlap / len(correct_tokens) >= 0.5
