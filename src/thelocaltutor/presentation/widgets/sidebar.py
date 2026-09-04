"""Navigation sidebar widget."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget


class SidebarButton(QPushButton):
    def __init__(self, icon_char: str, label: str, parent=None):
        super().__init__(f"  {icon_char}  {label}", parent)
        self.setObjectName("nav-btn")
        self.setCheckable(False)
        self.setProperty("active", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_active(self, active: bool) -> None:
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)


class Sidebar(QWidget):
    page_requested = Signal(str)

    _PAGES = [
        ("dashboard", "⊞", "Dashboard"),
        ("library", "⊟", "My Library"),
        ("practice", "✎", "Practice"),
        ("progress", "↗", "Progress"),
        ("settings", "⚙", "Settings"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)

        self._buttons: dict[str, SidebarButton] = {}
        self._ai_label: QLabel | None = None
        self._current_page = ""

        self._build_ui()
        self._check_ai_timer = QTimer(self)
        self._check_ai_timer.timeout.connect(self._refresh_ai_status)
        self._check_ai_timer.start(10_000)
        self._refresh_ai_status()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 16)
        layout.setSpacing(2)

        # Branding
        title = QLabel("LocalTutor")
        title.setObjectName("sidebar-title")
        subtitle = QLabel("AI Study Assistant")
        subtitle.setObjectName("sidebar-subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #1e293b; margin: 10px 0;")
        layout.addWidget(sep)
        layout.addSpacing(4)

        # Nav buttons
        section = QLabel("NAVIGATION")
        section.setObjectName("section-label")
        section.setStyleSheet("color: #475569; font-size: 10px; font-weight: 700; padding: 4px 6px;")
        layout.addWidget(section)
        layout.addSpacing(2)

        for page_id, icon, label in self._PAGES:
            btn = SidebarButton(icon, label)
            btn.clicked.connect(lambda checked=False, pid=page_id: self._on_click(pid))
            self._buttons[page_id] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # AI status
        ai_section = QLabel("AI ENGINE")
        ai_section.setStyleSheet("color: #475569; font-size: 10px; font-weight: 700; padding: 4px 6px;")
        layout.addWidget(ai_section)

        self._ai_label = QLabel("Checking...")
        self._ai_label.setObjectName("ai-status-label")
        self._ai_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ai_label.setStyleSheet("color: #94a3b8; font-size: 11px; padding: 4px 8px;")
        layout.addWidget(self._ai_label)

    def _on_click(self, page_id: str) -> None:
        self.navigate_to(page_id)
        self.page_requested.emit(page_id)

    def navigate_to(self, page_id: str) -> None:
        self._current_page = page_id
        for pid, btn in self._buttons.items():
            btn.set_active(pid == page_id)

    def _refresh_ai_status(self) -> None:
        from thelocaltutor.services.question_service import ai_available
        online = ai_available()
        if self._ai_label:
            if online:
                self._ai_label.setText("Ollama  Online")
                self._ai_label.setStyleSheet(
                    "color: #4ade80; background: rgba(74,222,128,0.12); "
                    "font-size: 11px; border-radius: 6px; padding: 4px 8px; font-weight: 600;"
                )
            else:
                self._ai_label.setText("Ollama  Offline")
                self._ai_label.setStyleSheet(
                    "color: #f87171; background: rgba(248,113,113,0.12); "
                    "font-size: 11px; border-radius: 6px; padding: 4px 8px; font-weight: 600;"
                )
