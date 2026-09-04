"""Settings page — configure Ollama connection and defaults."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from thelocaltutor.core import config
from thelocaltutor.services.question_service import available_models


class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("content-area")
        self._build_ui()
        self._load_current()

    def _build_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        container = QWidget()
        container.setObjectName("content-area")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        title = QLabel("Settings")
        title.setObjectName("page-title")
        sub = QLabel("Configure your AI engine and study preferences.")
        sub.setObjectName("page-subtitle")
        layout.addWidget(title)
        layout.addWidget(sub)

        # ── AI Engine card ────────────────────────────────────────────────
        ai_card, ai_layout = self._card("AI Engine")
        ai_form = QFormLayout()
        ai_form.setSpacing(12)
        ai_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self._url_input = QComboBox()
        self._url_input.setEditable(True)
        self._url_input.addItem(config.get("ollama_base_url"))
        ai_form.addRow("Ollama URL", self._url_input)

        refresh_btn = QPushButton("Refresh Models")
        refresh_btn.setObjectName("btn-secondary")
        refresh_btn.clicked.connect(self._refresh_models)
        self._model_combo = QComboBox()
        self._model_combo.setEditable(True)
        self._model_combo.addItem(config.get("ollama_model"))
        model_row = QHBoxLayout()
        model_row.addWidget(self._model_combo)
        model_row.addWidget(refresh_btn)
        ai_form.addRow("Model", model_row)

        ai_layout.addLayout(ai_form)
        layout.addWidget(ai_card)

        # ── Question defaults card ────────────────────────────────────────
        q_card, q_layout = self._card("Question Defaults")
        q_form = QFormLayout()
        q_form.setSpacing(12)

        self._count_spin = QSpinBox()
        self._count_spin.setRange(1, 50)
        self._count_spin.setValue(config.get("default_question_count"))
        q_form.addRow("Questions per generation", self._count_spin)

        self._diff_combo = QComboBox()
        self._diff_combo.addItems(["easy", "medium", "hard", "mixed"])
        self._diff_combo.setCurrentText(config.get("default_difficulty"))
        q_form.addRow("Default difficulty", self._diff_combo)

        types_row = QHBoxLayout()
        self._mcq_cb = QCheckBox("MCQ")
        self._tf_cb = QCheckBox("True / False")
        self._sa_cb = QCheckBox("Short Answer")
        defaults = config.get("default_question_types")
        self._mcq_cb.setChecked("mcq" in defaults)
        self._tf_cb.setChecked("true_false" in defaults)
        self._sa_cb.setChecked("short_answer" in defaults)
        types_row.addWidget(self._mcq_cb)
        types_row.addWidget(self._tf_cb)
        types_row.addWidget(self._sa_cb)
        types_row.addStretch()
        q_form.addRow("Question types", types_row)

        q_layout.addLayout(q_form)
        layout.addWidget(q_card)

        # ── Processing card ───────────────────────────────────────────────
        proc_card, proc_layout = self._card("Document Processing")
        proc_form = QFormLayout()
        proc_form.setSpacing(12)

        self._chunk_spin = QSpinBox()
        self._chunk_spin.setRange(500, 10000)
        self._chunk_spin.setSingleStep(100)
        self._chunk_spin.setValue(config.get("chunk_size"))
        proc_form.addRow("Chunk size (chars)", self._chunk_spin)

        self._overlap_spin = QSpinBox()
        self._overlap_spin.setRange(0, 2000)
        self._overlap_spin.setSingleStep(50)
        self._overlap_spin.setValue(config.get("chunk_overlap"))
        proc_form.addRow("Chunk overlap (chars)", self._overlap_spin)

        self._max_chunks_spin = QSpinBox()
        self._max_chunks_spin.setRange(1, 20)
        self._max_chunks_spin.setValue(config.get("max_chunks_per_generation"))
        proc_form.addRow("Max chunks per generation", self._max_chunks_spin)

        proc_layout.addLayout(proc_form)
        layout.addWidget(proc_card)

        layout.addStretch()

        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("btn-primary")
        save_btn.setFixedWidth(160)
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _card(self, title: str) -> tuple[QWidget, QVBoxLayout]:
        card = QWidget()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(12)
        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #0f172a;")
        card_layout.addWidget(lbl)
        return card, card_layout

    def _load_current(self) -> None:
        self._refresh_models()

    def _refresh_models(self) -> None:
        models = available_models()
        current = self._model_combo.currentText()
        self._model_combo.clear()
        if models:
            self._model_combo.addItems(models)
        if current:
            self._model_combo.setEditText(current)

    def _save(self) -> None:
        types = []
        if self._mcq_cb.isChecked():
            types.append("mcq")
        if self._tf_cb.isChecked():
            types.append("true_false")
        if self._sa_cb.isChecked():
            types.append("short_answer")
        if not types:
            types = ["mcq"]

        config.set("ollama_base_url", self._url_input.currentText().strip())
        config.set("ollama_model", self._model_combo.currentText().strip())
        config.set("default_question_count", self._count_spin.value())
        config.set("default_difficulty", self._diff_combo.currentText())
        config.set("default_question_types", types)
        config.set("chunk_size", self._chunk_spin.value())
        config.set("chunk_overlap", self._overlap_spin.value())
        config.set("max_chunks_per_generation", self._max_chunks_spin.value())

        QMessageBox.information(self, "Saved", "Your settings have been saved.")
