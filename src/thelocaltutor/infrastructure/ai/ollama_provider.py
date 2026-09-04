"""Ollama REST API provider for question generation."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import requests

from thelocaltutor.core import config
from thelocaltutor.core.exceptions import AIConnectionError, AIParseError
from thelocaltutor.domain.models import Difficulty, Question, QuestionOption, QuestionType

log = logging.getLogger(__name__)

_GENERATE_TIMEOUT = 300  # seconds


def is_available() -> bool:
    try:
        url = config.get("ollama_base_url")
        resp = requests.get(f"{url}/api/tags", timeout=4)
        return resp.status_code == 200
    except Exception:
        return False


def list_models() -> list[str]:
    try:
        url = config.get("ollama_base_url")
        resp = requests.get(f"{url}/api/tags", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def generate_questions(
    material_id: int,
    content: str,
    count: int,
    question_types: list[str],
    difficulty: str,
    model: str | None = None,
) -> list[Question]:
    base_url = config.get("ollama_base_url")
    model_name = model or config.get("ollama_model")

    prompt = _build_prompt(content, count, question_types, difficulty)

    payload: dict[str, Any] = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.7,
            "num_predict": 4096,
        },
    }

    log.info("Requesting %d questions from Ollama model '%s'", count, model_name)
    try:
        resp = requests.post(
            f"{base_url}/api/generate",
            json=payload,
            timeout=_GENERATE_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.exceptions.ConnectionError as exc:
        raise AIConnectionError("Cannot connect to Ollama. Is it running?") from exc
    except requests.exceptions.Timeout as exc:
        raise AIConnectionError("Ollama request timed out.") from exc
    except requests.exceptions.HTTPError as exc:
        if resp.status_code == 404:
            raise AIConnectionError(
                f"Model '{model_name}' not found in Ollama. "
                f"Run: ollama pull {model_name}"
            ) from exc
        raise AIConnectionError(f"Ollama returned an error: {exc}") from exc

    raw = resp.json().get("response", "")
    return _parse_response(raw, material_id, difficulty)


def _build_prompt(content: str, count: int, question_types: list[str], difficulty: str) -> str:
    type_desc_map = {
        "mcq": "Multiple Choice (4 options, exactly one correct)",
        "true_false": "True/False",
        "short_answer": "Short Answer (1-3 sentence expected response)",
    }
    types_str = ", ".join(type_desc_map[t] for t in question_types if t in type_desc_map)
    diff_str = difficulty if difficulty != "mixed" else "a mix of easy, medium, and hard"

    return f"""You are an expert academic question generator. Generate exactly {count} study questions based on the provided material.

QUESTION TYPES TO INCLUDE: {types_str}
DIFFICULTY: {diff_str}

STRICT RULES:
1. Return ONLY valid JSON — no explanation, no markdown, no code fences.
2. Every question must be directly based on the material below.
3. For MCQ: provide exactly 4 options (A, B, C, D), only one correct.
4. For True/False: correct_answer must be exactly "True" or "False".
5. For Short Answer: correct_answer is a concise model answer.
6. The explanation field must explain why the answer is correct.

MATERIAL:
---
{content}
---

Return this exact JSON structure:
{{
  "questions": [
    {{
      "type": "mcq",
      "difficulty": "medium",
      "question": "Question text here?",
      "options": [
        {{"letter": "A", "text": "Option A text", "is_correct": false}},
        {{"letter": "B", "text": "Option B text", "is_correct": true}},
        {{"letter": "C", "text": "Option C text", "is_correct": false}},
        {{"letter": "D", "text": "Option D text", "is_correct": false}}
      ],
      "correct_answer": "B",
      "explanation": "Explanation why B is correct.",
      "topic": "Topic name from material"
    }},
    {{
      "type": "true_false",
      "difficulty": "easy",
      "question": "Statement to evaluate.",
      "options": [],
      "correct_answer": "True",
      "explanation": "Explanation.",
      "topic": "Topic name"
    }},
    {{
      "type": "short_answer",
      "difficulty": "hard",
      "question": "Question requiring a written answer?",
      "options": [],
      "correct_answer": "Model answer here.",
      "explanation": "Explanation.",
      "topic": "Topic name"
    }}
  ]
}}"""


def _parse_response(raw: str, material_id: int, difficulty: str) -> list[Question]:
    raw = raw.strip()
    # Extract JSON block if there is surrounding text
    json_match = re.search(r'\{[\s\S]*\}', raw)
    if not json_match:
        raise AIParseError(f"No JSON object found in AI response. Raw: {raw[:300]}")

    try:
        data = json.loads(json_match.group())
    except json.JSONDecodeError as exc:
        raise AIParseError(f"Invalid JSON from AI: {exc}. Raw: {raw[:300]}") from exc

    raw_questions = data.get("questions", [])
    if not raw_questions:
        raise AIParseError("AI returned an empty questions list.")

    questions: list[Question] = []
    for i, rq in enumerate(raw_questions):
        try:
            q = _parse_one(rq, material_id, difficulty)
            questions.append(q)
        except Exception as exc:
            log.warning("Skipping malformed question %d: %s", i, exc)

    if not questions:
        raise AIParseError("All generated questions were malformed and could not be parsed.")

    log.info("Parsed %d valid questions from AI response", len(questions))
    return questions


def _parse_one(rq: dict, material_id: int, default_difficulty: str) -> Question:
    qtype_str = rq.get("type", "mcq").lower().replace("-", "_")
    try:
        qtype = QuestionType(qtype_str)
    except ValueError:
        qtype = QuestionType.MCQ

    diff_str = rq.get("difficulty", default_difficulty).lower()
    if diff_str == "mixed":
        diff_str = "medium"
    try:
        diff = Difficulty(diff_str)
    except ValueError:
        diff = Difficulty.MEDIUM

    options: list[QuestionOption] = []
    if qtype == QuestionType.MCQ:
        for opt in rq.get("options", []):
            options.append(
                QuestionOption(
                    letter=opt.get("letter", "?"),
                    text=opt.get("text", ""),
                    is_correct=bool(opt.get("is_correct", False)),
                )
            )

    if qtype == QuestionType.TRUE_FALSE and not options:
        options = [
            QuestionOption(letter="A", text="True", is_correct=rq.get("correct_answer", "True") == "True"),
            QuestionOption(letter="B", text="False", is_correct=rq.get("correct_answer", "True") == "False"),
        ]

    question_text = rq.get("question", "").strip()
    if not question_text:
        raise ValueError("Empty question text")

    return Question(
        id=0,
        material_id=material_id,
        question_type=qtype,
        difficulty=diff,
        question_text=question_text,
        correct_answer=rq.get("correct_answer", "").strip(),
        explanation=rq.get("explanation", "").strip(),
        topic=rq.get("topic", "").strip(),
        options=options,
    )
