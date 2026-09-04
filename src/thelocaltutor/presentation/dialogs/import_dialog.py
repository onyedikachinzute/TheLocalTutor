"""Import material dialog — file picker with course field."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ImportDialog(QDialog):
    import_confirmed = Signal(str, str)  # file_path, course

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Study Material")
        self.setFixedSize(520, 220)
        self.setObjectName("dialog")
        self._file_path = ""
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("Import Study Material")
        title.setObjectName("dialog-title")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        file_row = QHBoxLayout()
        self._path_label = QLineEdit()
        self._path_label.setReadOnly(True)
        self._path_label.setPlaceholderText("Select a PDF or PowerPoint file...")
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("btn-secondary")
        browse_btn.clicked.connect(self._browse)
        file_row.addWidget(self._path_label)
        file_row.addWidget(browse_btn)
        form.addRow("File", file_row)

        self._course_input = QLineEdit()
        self._course_input.setPlaceholderText("e.g. Biology 101 (optional)")
        form.addRow("Course", self._course_input)

        layout.addLayout(form)
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setObjectName("btn-secondary")
        cancel.clicked.connect(self.reject)
        self._import_btn = QPushButton("Import")
        self._import_btn.setObjectName("btn-primary")
        self._import_btn.setEnabled(False)
        self._import_btn.clicked.connect(self._confirm)
        btn_row.addWidget(cancel)
        btn_row.addWidget(self._import_btn)
        layout.addLayout(btn_row)

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Study Material",
            "",
            "Documents (*.pdf *.pptx);;PDF Files (*.pdf);;PowerPoint Files (*.pptx)",
        )
        if path:
            self._file_path = path
            self._path_label.setText(path)
            self._import_btn.setEnabled(True)

    def _confirm(self) -> None:
        if not self._file_path:
            QMessageBox.warning(self, "No File", "Please select a file to import.")
            return
        self.import_confirmed.emit(self._file_path, self._course_input.text().strip())
        self.accept()
