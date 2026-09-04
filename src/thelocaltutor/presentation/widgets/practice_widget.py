"""Practice session widget — present questions, collect answers."""

from __future__ import annotations

import time
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from thelocaltutor.domain.models import Question, QuestionType, SessionMode
from thelocaltutor.services.study_service import finish_session, start_session, submit_answer


class OptionButton(QPushButton):
    def __init__(self, letter: str, text: str, parent=None):
        super().__init__(f"  {letter}.  {text}", parent)
        self.setObjectName("option-btn")
        self.letter = letter
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(48)

    def set_state(self, state: str) -> None:
        for prop in ("selected", "correct", "incorrect"):
            self.setProperty(prop, prop == state if state else False)
        self.style().unpolish(self)
        self.style().polish(self)


class PracticeWidget(QWidget):
    session_finished = Signal(int)
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("content-area")
        self._session_id: int | None = None
        self._questions: list[Question] = []
        self._current_index: int = 0
        self._option_buttons: list[OptionButton] = []
        self._selected_letter: str | None = None
        self._answer_revealed: bool = False
        self._start_time: float = 0.0
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 24, 32, 24)
        outer.setSpacing(16)

        # Top bar
        top = QHBoxLayout()
        back = QPushButton("← Exit Session")
        back.setObjectName("btn-secondary")
        back.clicked.connect(self._on_exit)
        top.addWidget(back)
        top.addStretch()

        self._progress_lbl = QLabel()
        self._progress_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-weight: 500;")
        top.addWidget(self._progress_lbl)

        outer.addLayout(top)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedHeight(8)
        self._progress_bar.setTextVisible(False)
        outer.addWidget(self._progress_bar)

        # Question card
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        card = QWidget()
        card.setObjectName("question-card")
        self._card_layout = QVBoxLayout(card)
        self._card_layout.setContentsMargins(32, 32, 32, 32)
        self._card_layout.setSpacing(16)

        # Difficulty / type row
        meta_row = QHBoxLayout()
        self._diff_lbl = QLabel()
        meta_row.addWidget(self._diff_lbl)
        self._type_lbl = QLabel()
        self._type_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; font-weight: 500;")
        meta_row.addWidget(self._type_lbl)
        meta_row.addStretch()
        self._topic_lbl = QLabel()
        self._topic_lbl.setStyleSheet("font-size: 11px; color: #6366f1; font-weight: 600;")
        meta_row.addWidget(self._topic_lbl)
        self._card_layout.addLayout(meta_row)

        # Question text
        self._question_lbl = QLabel()
        self._question_lbl.setObjectName("question-text")
        self._question_lbl.setWordWrap(True)
        self._card_layout.addWidget(self._question_lbl)

        # Options container
        self._options_container = QVBoxLayout()
        self._options_container.setSpacing(8)
        self._card_layout.addLayout(self._options_container)

        # Short-answer input
        self._sa_input = QTextEdit()
        self._sa_input.setPlaceholderText("Type your answer here...")
        self._sa_input.setFixedHeight(100)
        self._sa_input.setVisible(False)
        self._card_layout.addWidget(self._sa_input)

        # Explanation (revealed after answer)
        self._explanation_widget = QWidget()
        self._explanation_widget.setVisible(False)
        exp_layout = QVBoxLayout(self._explanation_widget)
        exp_layout.setContentsMargins(0, 0, 0, 0)
        exp_layout.setSpacing(6)
        exp_lbl = QLabel("Explanation")
        exp_lbl.setStyleSheet("font-weight: 700; color: #1e293b; font-size: 13px;")
        self._exp_text = QLabel()
        self._exp_text.setWordWrap(True)
        self._exp_text.setStyleSheet("color: #374151; font-size: 13px; line-height: 1.5;")
        self._correct_ans_lbl = QLabel()
        self._correct_ans_lbl.setWordWrap(True)
        self._correct_ans_lbl.setStyleSheet("color: #16a34a; font-size: 13px; font-weight: 600;")
        exp_layout.addWidget(self._correct_ans_lbl)
        exp_layout.addWidget(exp_lbl)
        exp_layout.addWidget(self._exp_text)
        self._card_layout.addWidget(self._explanation_widget)

        scroll.setWidget(card)
        outer.addWidget(scroll)

        # Bottom actions
        bottom = QHBoxLayout()
        bottom.setSpacing(12)
        self._submit_btn = QPushButton("Submit Answer")
        self._submit_btn.setObjectName("btn-primary")
        self._submit_btn.clicked.connect(self._on_submit)
        bottom.addStretch()
        bottom.addWidget(self._submit_btn)
        self._next_btn = QPushButton("Next Question  →")
        self._next_btn.setObjectName("btn-primary")
        self._next_btn.setVisible(False)
        self._next_btn.clicked.connect(self._on_next)
        bottom.addWidget(self._next_btn)
        outer.addLayout(bottom)

    # ── Public API ────────────────────────────────────────────────────────────

    def start_practice(self, material_id: int, max_questions: int | None = None) -> None:
        try:
            session_id, questions = start_session(material_id, SessionMode.PRACTICE, max_questions)
        except ValueError as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Cannot Start", str(e))
            self.back_requested.emit()
            return

        self._session_id = session_id
        self._questions = questions
        self._current_index = 0
        self._show_question()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _show_question(self) -> None:
        q = self._questions[self._current_index]
        total = len(self._questions)
        idx = self._current_index

        self._progress_lbl.setText(f"Question {idx + 1} of {total}")
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(idx)

        diff = q.difficulty.value
        diff_colors = {"easy": "#16a34a", "medium": "#d97706", "hard": "#dc2626"}
        self._diff_lbl.setText(diff.capitalize())
        self._diff_lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 700; color: {diff_colors.get(diff, '#64748b')};"
        )
        type_names = {"mcq": "Multiple Choice", "true_false": "True / False", "short_answer": "Short Answer"}
        self._type_lbl.setText(type_names.get(q.question_type.value, q.question_type.value))
        self._topic_lbl.setText(q.topic if q.topic else "")

        self._question_lbl.setText(q.question_text)
        self._answer_revealed = False
        self._selected_letter = None
        self._explanation_widget.setVisible(False)
        self._submit_btn.setVisible(True)
        self._next_btn.setVisible(False)

        # Clear old options
        while self._options_container.count():
            item = self._options_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._option_buttons.clear()

        is_last = self._current_index >= len(self._questions) - 1
        self._next_btn.setText("Finish Session" if is_last else "Next Question  →")

        if q.question_type == QuestionType.SHORT_ANSWER:
            self._sa_input.setVisible(True)
            self._sa_input.clear()
            self._sa_input.setEnabled(True)
        else:
            self._sa_input.setVisible(False)
            options = q.options if q.options else []
            if q.question_type == QuestionType.TRUE_FALSE and not options:
                from thelocaltutor.domain.models import QuestionOption
                options = [
                    QuestionOption("A", "True", q.correct_answer == "True"),
                    QuestionOption("B", "False", q.correct_answer == "False"),
                ]
            for opt in options:
                btn = OptionButton(opt.letter, opt.text)
                btn.clicked.connect(lambda checked, b=btn: self._on_option_selected(b))
                self._options_container.addWidget(btn)
                self._option_buttons.append(btn)

        self._start_time = time.monotonic()

    def _on_option_selected(self, selected: OptionButton) -> None:
        if self._answer_revealed:
            return
        for btn in self._option_buttons:
            btn.setChecked(False)
            btn.set_state("")
        selected.setChecked(True)
        selected.set_state("selected")
        self._selected_letter = selected.letter

    def _on_submit(self) -> None:
        if self._answer_revealed:
            return
        q = self._questions[self._current_index]
        elapsed = int(time.monotonic() - self._start_time)

        if q.question_type == QuestionType.SHORT_ANSWER:
            user_answer = self._sa_input.toPlainText().strip()
            if not user_answer:
                return
        else:
            if self._selected_letter is None:
                return
            user_answer = self._selected_letter

        is_correct = submit_answer(self._session_id, q, user_answer, elapsed)
        self._reveal_answer(q, user_answer, is_correct)

    def _reveal_answer(self, q: Question, user_answer: str, is_correct: bool) -> None:
        self._answer_revealed = True
        self._submit_btn.setVisible(False)
        self._next_btn.setVisible(True)
        self._sa_input.setEnabled(False)

        for btn in self._option_buttons:
            is_user = btn.letter == user_answer
            is_right = btn.letter == q.correct_answer
            if is_right:
                btn.set_state("correct")
            elif is_user and not is_right:
                btn.set_state("incorrect")
            else:
                btn.set_state("")

        correct_text = f"Correct answer: {q.correct_answer}"
        if q.question_type == QuestionType.SHORT_ANSWER:
            correct_text = f"Model answer: {q.correct_answer}"
        result_prefix = "Correct!" if is_correct else "Incorrect."
        self._correct_ans_lbl.setText(f"{result_prefix}  {correct_text}")
        self._correct_ans_lbl.setStyleSheet(
            f"color: {'#16a34a' if is_correct else '#dc2626'}; font-size: 13px; font-weight: 600;"
        )
        self._exp_text.setText(q.explanation or "No explanation provided.")
        self._explanation_widget.setVisible(True)

    def _on_next(self) -> None:
        self._current_index += 1
        if self._current_index >= len(self._questions):
            self._finish()
        else:
            self._show_question()

    def _finish(self) -> None:
        if self._session_id is not None:
            finish_session(self._session_id)
            self.session_finished.emit(self._session_id)

    def _on_exit(self) -> None:
        from PySide6.QtWidgets import QMessageBox
        if self._session_id is not None and self._current_index < len(self._questions):
            reply = QMessageBox.question(
                self, "Exit Session",
                "Exit the current session? Progress will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self.back_requested.emit()
