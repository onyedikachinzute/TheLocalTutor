"""Generate questions dialog — configure count, types, difficulty."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from thelocaltutor.core import config


class GenerateDialog(QDialog):
    generate_confirmed = Signal(int, list, str)  # count, types, difficulty

    def __init__(self, material_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Questions")
        self.setFixedSize(480, 340)
        self._build_ui(material_name)

    def _build_ui(self, material_name: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("Generate Questions")
        title.setObjectName("dialog-title")
        layout.addWidget(title)

        sub = QLabel(f"From: {material_name}")
        sub.setStyleSheet("font-size: 12px; color: #64748b;")
        layout.addWidget(sub)

        form = QFormLayout()
        form.setSpacing(12)

        self._count_spin = QSpinBox()
        self._count_spin.setRange(1, 50)
        self._count_spin.setValue(config.get("default_question_count"))
        form.addRow("Number of questions", self._count_spin)

        self._diff_combo = QComboBox()
        self._diff_combo.addItems(["easy", "medium", "hard", "mixed"])
        self._diff_combo.setCurrentText(config.get("default_difficulty"))
        form.addRow("Difficulty", self._diff_combo)

        types_row = QHBoxLayout()
        defaults = config.get("default_question_types")
        self._mcq_cb = QCheckBox("MCQ")
        self._tf_cb = QCheckBox("True / False")
        self._sa_cb = QCheckBox("Short Answer")
        self._mcq_cb.setChecked("mcq" in defaults)
        self._tf_cb.setChecked("true_false" in defaults)
        self._sa_cb.setChecked("short_answer" in defaults)
        types_row.addWidget(self._mcq_cb)
        types_row.addWidget(self._tf_cb)
        types_row.addWidget(self._sa_cb)
        types_row.addStretch()
        form.addRow("Question types", types_row)

        layout.addLayout(form)
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setObjectName("btn-secondary")
        cancel.clicked.connect(self.reject)
        gen_btn = QPushButton("Generate")
        gen_btn.setObjectName("btn-primary")
        gen_btn.clicked.connect(self._confirm)
        btn_row.addWidget(cancel)
        btn_row.addWidget(gen_btn)
        layout.addLayout(btn_row)

    def _confirm(self) -> None:
        types = []
        if self._mcq_cb.isChecked():
            types.append("mcq")
        if self._tf_cb.isChecked():
            types.append("true_false")
        if self._sa_cb.isChecked():
            types.append("short_answer")
        if not types:
            QMessageBox.warning(self, "No Types", "Select at least one question type.")
            return
        self.generate_confirmed.emit(
            self._count_spin.value(),
            types,
            self._diff_combo.currentText(),
        )
        self.accept()
