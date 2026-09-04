"""Session results page."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from thelocaltutor.domain.models import Question, QuestionType, SessionResult
from thelocaltutor.services.study_service import get_result


class ResultRow(QWidget):
    def __init__(self, number: int, question: Question, user_answer: str, is_correct: bool, parent=None):
        super().__init__(parent)
        obj = "result-correct" if is_correct else "result-incorrect"
        self.setObjectName(obj)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        top = QHBoxLayout()
        icon = QLabel("✓" if is_correct else "✗")
        icon.setFixedWidth(20)
        icon.setStyleSheet(f"color: {'#16a34a' if is_correct else '#dc2626'}; font-weight: 700; font-size: 16px;")
        top.addWidget(icon)
        q_lbl = QLabel(f"{number}. {question.question_text}")
        q_lbl.setWordWrap(True)
        q_lbl.setStyleSheet("font-size: 13px; color: #1e293b; font-weight: 500;")
        top.addWidget(q_lbl)
        layout.addLayout(top)

        ans_row = QHBoxLayout()
        ans_row.setContentsMargins(28, 0, 0, 0)

        if question.question_type != QuestionType.SHORT_ANSWER:
            your = QLabel(f"Your answer:  {user_answer or '(no answer)'}")
            your.setStyleSheet(f"font-size: 12px; color: {'#16a34a' if is_correct else '#dc2626'};")
            ans_row.addWidget(your)

            if not is_correct:
                correct = QLabel(f"Correct:  {question.correct_answer}")
                correct.setStyleSheet("font-size: 12px; color: #16a34a; font-weight: 600;")
                ans_row.addWidget(correct)
        else:
            your = QLabel(f"Your answer:  {user_answer or '(no answer)'}")
            your.setStyleSheet("font-size: 12px; color: #374151;")
            ans_row.addWidget(your)
            model = QLabel(f"Model answer:  {question.correct_answer}")
            model.setStyleSheet("font-size: 12px; color: #16a34a; font-weight: 600;")
            ans_row.addWidget(model)

        ans_row.addStretch()
        layout.addLayout(ans_row)

        if question.explanation:
            exp = QLabel(f"  {question.explanation}")
            exp.setWordWrap(True)
            exp.setContentsMargins(28, 0, 0, 0)
            exp.setStyleSheet("font-size: 12px; color: #64748b; font-style: italic;")
            layout.addWidget(exp)


class ResultsWidget(QWidget):
    practice_again = Signal(int)
    go_to_library = Signal()
    go_to_dashboard = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("content-area")
        self._material_id: int | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 32, 32, 24)
        outer.setSpacing(20)

        # Score summary card
        self._summary_card = QWidget()
        self._summary_card.setObjectName("card")
        sc_layout = QVBoxLayout(self._summary_card)
        sc_layout.setContentsMargins(32, 28, 32, 28)
        sc_layout.setSpacing(8)
        sc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._score_lbl = QLabel("—")
        self._score_lbl.setObjectName("score-circle")
        self._score_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._score_desc = QLabel()
        self._score_desc.setObjectName("score-label")
        self._score_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._grade_lbl = QLabel()
        self._grade_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._grade_lbl.setStyleSheet("font-size: 18px; font-weight: 700;")

        sc_layout.addWidget(self._score_lbl)
        sc_layout.addWidget(self._grade_lbl)
        sc_layout.addWidget(self._score_desc)

        # Actions
        actions = QHBoxLayout()
        actions.setSpacing(12)
        dashboard_btn = QPushButton("Go to Dashboard")
        dashboard_btn.setObjectName("btn-secondary")
        dashboard_btn.clicked.connect(self.go_to_dashboard)
        library_btn = QPushButton("Back to Library")
        library_btn.setObjectName("btn-secondary")
        library_btn.clicked.connect(self.go_to_library)
        self._again_btn = QPushButton("Practice Again")
        self._again_btn.setObjectName("btn-primary")
        self._again_btn.clicked.connect(self._on_practice_again)

        actions.addWidget(dashboard_btn)
        actions.addWidget(library_btn)
        actions.addStretch()
        actions.addWidget(self._again_btn)
        sc_layout.addSpacing(8)
        sc_layout.addLayout(actions)
        outer.addWidget(self._summary_card)

        # Review list
        review_title = QLabel("Question Review")
        review_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0f172a;")
        outer.addWidget(review_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self._review_container = QWidget()
        self._review_container.setObjectName("content-area")
        self._review_layout = QVBoxLayout(self._review_container)
        self._review_layout.setContentsMargins(0, 0, 0, 0)
        self._review_layout.setSpacing(8)
        self._review_layout.addStretch()

        scroll.setWidget(self._review_container)
        outer.addWidget(scroll)

    def load_result(self, session_id: int) -> None:
        try:
            result = get_result(session_id)
        except Exception:
            return

        self._material_id = result.session.material_id
        score = result.score_percent
        correct = result.correct_count
        total = len(result.attempts)

        self._score_lbl.setText(f"{score:.0f}%")
        self._score_desc.setText(f"{correct} of {total} correct")

        grade, color = _grade(score)
        self._grade_lbl.setText(grade)
        self._grade_lbl.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {color};")

        # Review rows
        layout = self._review_layout
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        attempt_map = {a.question_id: a for a in result.attempts}
        for i, q in enumerate(result.questions, 1):
            attempt = attempt_map.get(q.id)
            if not attempt:
                continue
            row = ResultRow(i, q, attempt.user_answer, attempt.is_correct)
            layout.insertWidget(layout.count() - 1, row)

    def _on_practice_again(self) -> None:
        if self._material_id:
            self.practice_again.emit(self._material_id)


def _grade(score: float) -> tuple[str, str]:
    if score >= 90:
        return "Excellent!", "#16a34a"
    if score >= 75:
        return "Good Job!", "#2563eb"
    if score >= 60:
        return "Keep Practising", "#d97706"
    return "Needs Work", "#dc2626"
