"""Domain models (pure dataclasses — no ORM coupling)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class FileType(str, Enum):
    PDF = "pdf"
    PPTX = "pptx"


class MaterialStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class QuestionType(str, Enum):
    MCQ = "mcq"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    MIXED = "mixed"


class SessionMode(str, Enum):
    PRACTICE = "practice"
    EXAM = "exam"


@dataclass
class Material:
    id: int
    name: str
    file_path: str
    file_type: FileType
    date_added: datetime
    page_count: int
    status: MaterialStatus
    course: str = ""
    error_message: str = ""
    chunk_count: int = 0
    question_count: int = 0


@dataclass
class DocumentChunk:
    id: int
    material_id: int
    page_number: int
    content: str
    chunk_index: int


@dataclass
class QuestionOption:
    letter: str   # A / B / C / D
    text: str
    is_correct: bool


@dataclass
class Question:
    id: int
    material_id: int
    question_type: QuestionType
    difficulty: Difficulty
    question_text: str
    correct_answer: str
    explanation: str
    options: list[QuestionOption] = field(default_factory=list)
    topic: str = ""
    source_page: int = 0
    date_created: datetime = field(default_factory=datetime.now)


@dataclass
class Attempt:
    id: int
    session_id: int
    question_id: int
    user_answer: str
    is_correct: bool
    time_taken_seconds: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class StudySession:
    id: int
    material_id: int
    mode: SessionMode
    started_at: datetime
    total_questions: int
    ended_at: Optional[datetime] = None
    score_percent: Optional[float] = None
    correct_count: int = 0
    question_ids: list[int] = field(default_factory=list)


@dataclass
class SessionResult:
    session: StudySession
    attempts: list[Attempt]
    questions: list[Question]

    @property
    def score_percent(self) -> float:
        if not self.attempts:
            return 0.0
        correct = sum(1 for a in self.attempts if a.is_correct)
        return round(correct / len(self.attempts) * 100, 1)

    @property
    def correct_count(self) -> int:
        return sum(1 for a in self.attempts if a.is_correct)

    def question_for_attempt(self, attempt: Attempt) -> Optional[Question]:
        return next((q for q in self.questions if q.id == attempt.question_id), None)


@dataclass
class AppStats:
    total_materials: int
    total_questions: int
    total_sessions: int
    total_correct: int
    total_attempted: int

    @property
    def overall_accuracy(self) -> float:
        if self.total_attempted == 0:
            return 0.0
        return round(self.total_correct / self.total_attempted * 100, 1)
