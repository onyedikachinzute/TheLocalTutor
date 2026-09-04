"""Material detail view — questions list and study actions."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from thelocaltutor.domain.models import Material, Question, QuestionType
from thelocaltutor.services.material_service import get_material
from thelocaltutor.services.question_service import delete_questions, list_questions


class QuestionRow(QWidget):
    def __init__(self, question: Question, number: int, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        num = QLabel(f"{number}.")
        num.setFixedWidth(24)
        num.setStyleSheet("color: #94a3b8; font-size: 13px;")
        layout.addWidget(num)

        text = QLabel(question.question_text)
        text.setWordWrap(True)
        text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        text.setStyleSheet("font-size: 13px; color: #1e293b;")
        layout.addWidget(text)

        type_badge = QLabel(_type_label(question.question_type))
        type_badge.setFixedWidth(90)
        type_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        type_badge.setStyleSheet(
            "font-size: 11px; font-weight: 600; background: #f1f5f9; "
            "color: #475569; border-radius: 5px; padding: 2px 6px;"
        )
        layout.addWidget(type_badge)

        diff_id = f"difficulty-{question.difficulty.value}"
        diff = QLabel(question.difficulty.value.capitalize())
        diff.setObjectName(diff_id)
        diff.setFixedWidth(56)
        diff.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(diff)


def _type_label(qt: QuestionType) -> str:
    return {"mcq": "MCQ", "true_false": "True / False", "short_answer": "Short Answer"}.get(qt.value, qt.value)


class MaterialWidget(QWidget):
    back_requested = Signal()
    practice_requested = Signal(int)
    generate_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("content-area")
        self._material: Material | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(32, 24, 32, 24)
        self._outer.setSpacing(0)

        # Back
        back_btn = QPushButton("← Back to Library")
        back_btn.setObjectName("btn-secondary")
        back_btn.setFixedWidth(160)
        back_btn.clicked.connect(self.back_requested)
        self._outer.addWidget(back_btn)
        self._outer.addSpacing(16)

        # Header card
        self._header_card = QWidget()
        self._header_card.setObjectName("card")
        hc_layout = QVBoxLayout(self._header_card)
        hc_layout.setContentsMargins(24, 20, 24, 20)
        hc_layout.setSpacing(8)

        title_row = QHBoxLayout()
        self._title_lbl = QLabel()
        self._title_lbl.setObjectName("page-title")
        title_row.addWidget(self._title_lbl)
        title_row.addStretch()

        self._generate_btn = QPushButton("Generate Questions")
        self._generate_btn.setObjectName("btn-primary")
        self._generate_btn.clicked.connect(self._on_generate)
        title_row.addWidget(self._generate_btn)

        self._practice_btn = QPushButton("Start Practice")
        self._practice_btn.setObjectName("btn-secondary")
        self._practice_btn.clicked.connect(self._on_practice)
        title_row.addWidget(self._practice_btn)

        hc_layout.addLayout(title_row)

        self._meta_lbl = QLabel()
        self._meta_lbl.setObjectName("page-subtitle")
        hc_layout.addWidget(self._meta_lbl)

        self._outer.addWidget(self._header_card)
        self._outer.addSpacing(16)

        # Questions section
        q_header = QHBoxLayout()
        self._q_title = QLabel("Questions")
        self._q_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0f172a;")
        q_header.addWidget(self._q_title)
        q_header.addStretch()
        self._clear_btn = QPushButton("Clear All")
        self._clear_btn.setObjectName("btn-danger")
        self._clear_btn.clicked.connect(self._on_clear)
        q_header.addWidget(self._clear_btn)
        self._outer.addLayout(q_header)
        self._outer.addSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self._q_container = QWidget()
        self._q_container.setObjectName("content-area")
        self._q_layout = QVBoxLayout(self._q_container)
        self._q_layout.setContentsMargins(0, 0, 0, 0)
        self._q_layout.setSpacing(8)
        self._q_layout.addStretch()

        scroll.setWidget(self._q_container)
        self._outer.addWidget(scroll)

    def load_material(self, material_id: int) -> None:
        self._material = get_material(material_id)
        if not self._material:
            return
        self._refresh_header()
        self._refresh_questions()

    def _refresh_header(self) -> None:
        if not self._material:
            return
        m = self._material
        self._title_lbl.setText(m.name)
        pages = f"{m.page_count} pages" if m.page_count else "—"
        self._meta_lbl.setText(
            f"{m.file_type.value.upper()}  •  {pages}  •  {m.question_count} question(s)"
            + (f"  •  {m.course}" if m.course else "")
        )
        has_questions = m.question_count > 0
        self._practice_btn.setEnabled(has_questions)

    def _refresh_questions(self) -> None:
        layout = self._q_layout
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        if not self._material:
            return

        questions = list_questions(self._material.id)
        if not questions:
            lbl = QLabel("No questions yet. Click 'Generate Questions' to create some with AI.")
            lbl.setStyleSheet("color: #94a3b8; font-size: 14px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.insertWidget(0, lbl)
            self._q_title.setText("Questions  (0)")
            self._clear_btn.setVisible(False)
        else:
            self._q_title.setText(f"Questions  ({len(questions)})")
            self._clear_btn.setVisible(True)
            for i, q in enumerate(questions, 1):
                row = QuestionRow(q, i)
                layout.insertWidget(layout.count() - 1, row)

    def _on_generate(self) -> None:
        if self._material:
            self.generate_requested.emit(self._material.id)

    def _on_practice(self) -> None:
        if self._material:
            self.practice_requested.emit(self._material.id)

    def _on_clear(self) -> None:
        if not self._material:
            return
        reply = QMessageBox.question(
            self, "Clear Questions",
            "Delete all questions for this material?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_questions(self._material.id)
            self.load_material(self._material.id)
