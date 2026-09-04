"""Library page — list and manage study materials."""

from __future__ import annotations

import os
from pathlib import Path

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

from thelocaltutor.domain.models import Material, MaterialStatus
from thelocaltutor.services.material_service import delete_material, list_materials


class MaterialCard(QWidget):
    open_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, material: Material, parent=None):
        super().__init__(parent)
        self.setObjectName("material-item")
        self._material = material
        self._build_ui()
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)

        # File type icon
        icon_map = {"pdf": "PDF", "pptx": "PPT"}
        icon = QLabel(icon_map.get(self._material.file_type.value, "DOC"))
        icon.setFixedSize(44, 44)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(
            "background: #dbeafe; color: #1d4ed8; border-radius: 10px; "
            "font-weight: 700; font-size: 11px; border: none;"
        )
        layout.addWidget(icon)

        # Info
        info_col = QVBoxLayout()
        info_col.setSpacing(2)

        name = QLabel(self._material.name)
        name.setObjectName("material-name")

        pages_str = f"{self._material.page_count} pages" if self._material.page_count else "—"
        q_count = self._material.question_count
        meta = QLabel(
            f"{self._material.file_type.value.upper()}  •  {pages_str}  •  "
            f"{q_count} question{'s' if q_count != 1 else ''}"
        )
        meta.setObjectName("material-meta")

        if self._material.course:
            course_lbl = QLabel(self._material.course)
            course_lbl.setStyleSheet("font-size: 11px; color: #6366f1; font-weight: 600;")
            info_col.addWidget(course_lbl)

        info_col.addWidget(name)
        info_col.addWidget(meta)
        layout.addLayout(info_col)
        layout.addStretch()

        # Status badge
        status = self._material.status
        badge_text = status.value.capitalize()
        badge = QLabel(badge_text)
        badge.setObjectName(f"status-{status.value}")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedWidth(80)
        layout.addWidget(badge)

        # Action buttons (only shown for ready materials)
        if status == MaterialStatus.READY:
            open_btn = QPushButton("Open")
            open_btn.setObjectName("btn-primary")
            open_btn.setFixedWidth(72)
            open_btn.clicked.connect(lambda: self.open_requested.emit(self._material.id))
            layout.addWidget(open_btn)

        del_btn = QPushButton("Delete")
        del_btn.setObjectName("btn-danger")
        del_btn.setFixedWidth(72)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self._material.id))
        layout.addWidget(del_btn)

    def mousePressEvent(self, event) -> None:
        if self._material.status == MaterialStatus.READY:
            self.open_requested.emit(self._material.id)
        super().mousePressEvent(event)


class LibraryWidget(QWidget):
    import_requested = Signal()
    material_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("content-area")
        self._list_layout: QVBoxLayout | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 32, 32, 16)
        outer.setSpacing(16)

        # Header row
        header = QHBoxLayout()
        title = QLabel("My Library")
        title.setObjectName("page-title")
        header.addWidget(title)
        header.addStretch()
        import_btn = QPushButton("+ Import Material")
        import_btn.setObjectName("btn-primary")
        import_btn.clicked.connect(self.import_requested)
        header.addWidget(import_btn)
        outer.addLayout(header)

        sub = QLabel("All your imported study materials.")
        sub.setObjectName("page-subtitle")
        outer.addWidget(sub)

        # Scrollable list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self._list_container = QWidget()
        self._list_container.setObjectName("content-area")
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(10)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_container)
        outer.addWidget(scroll)

    def refresh(self) -> None:
        layout = self._list_layout
        if layout is None:
            return

        # Remove all existing cards (but keep the stretch at the end)
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        materials = list_materials()
        if not materials:
            empty = QLabel("No materials yet. Import a PDF or PowerPoint to get started.")
            empty.setStyleSheet("color: #94a3b8; font-size: 14px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.insertWidget(0, empty)
            return

        for mat in materials:
            card = MaterialCard(mat)
            card.open_requested.connect(self.material_selected)
            card.delete_requested.connect(self._on_delete)
            layout.insertWidget(layout.count() - 1, card)

    def _on_delete(self, material_id: int) -> None:
        reply = QMessageBox.question(
            self,
            "Delete Material",
            "Delete this material and all its generated questions? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_material(material_id)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
            self.refresh()
