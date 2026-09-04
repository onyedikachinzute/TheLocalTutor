"""Dashboard / home page."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from thelocaltutor.services.study_service import get_app_stats


class StatCard(QWidget):
    def __init__(self, value: str, label: str, parent=None):
        super().__init__(parent)
        self.setObjectName("stat-card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(4)

        val_lbl = QLabel(value)
        val_lbl.setObjectName("stat-value")
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(label)
        lbl.setObjectName("stat-label")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(val_lbl)
        layout.addWidget(lbl)

        self._value_lbl = val_lbl

    def set_value(self, value: str) -> None:
        self._value_lbl.setText(value)


class QuickActionButton(QPushButton):
    def __init__(self, title: str, desc: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(90)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(2)

        t = QLabel(title)
        t.setStyleSheet("font-weight: 700; font-size: 14px; color: #0f172a;")
        d = QLabel(desc)
        d.setStyleSheet("font-size: 12px; color: #64748b;")

        layout.addWidget(t)
        layout.addWidget(d)

        self.setStyleSheet("""
            QPushButton#card { background: #fff; border: 1.5px solid #e2e8f0; border-radius: 14px; }
            QPushButton#card:hover { border-color: #93c5fd; background: #eff6ff; }
        """)


class DashboardWidget(QWidget):
    import_requested = Signal()
    practice_requested = Signal()
    library_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("content-area")
        self._cards: dict[str, StatCard] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        container = QWidget()
        container.setObjectName("content-area")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # Header
        title = QLabel("Dashboard")
        title.setObjectName("page-title")
        sub = QLabel("Welcome back — here's your study overview.")
        sub.setObjectName("page-subtitle")
        layout.addWidget(title)
        layout.addWidget(sub)

        # Stat cards
        stats_grid = QGridLayout()
        stats_grid.setSpacing(14)
        defs = [
            ("materials", "0", "Study Materials"),
            ("questions", "0", "Questions Generated"),
            ("sessions", "0", "Sessions Completed"),
            ("accuracy", "—", "Overall Accuracy"),
        ]
        for i, (key, val, lbl) in enumerate(defs):
            card = StatCard(val, lbl)
            self._cards[key] = card
            stats_grid.addWidget(card, 0, i)
        layout.addLayout(stats_grid)

        # Quick actions
        actions_title = QLabel("Quick Actions")
        actions_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0f172a; margin-top: 8px;")
        layout.addWidget(actions_title)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(14)

        import_btn = QuickActionButton("Import Material", "Add a PDF or PowerPoint file")
        import_btn.clicked.connect(self.import_requested)
        actions_row.addWidget(import_btn)

        practice_btn = QuickActionButton("Start Practice", "Test yourself on generated questions")
        practice_btn.clicked.connect(self.practice_requested)
        actions_row.addWidget(practice_btn)

        library_btn = QuickActionButton("Browse Library", "View and manage your study materials")
        library_btn.clicked.connect(self.library_requested)
        actions_row.addWidget(library_btn)

        layout.addLayout(actions_row)
        layout.addStretch()

        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self) -> None:
        try:
            stats = get_app_stats()
            self._cards["materials"].set_value(str(stats.total_materials))
            self._cards["questions"].set_value(str(stats.total_questions))
            self._cards["sessions"].set_value(str(stats.total_sessions))
            acc = f"{stats.overall_accuracy}%" if stats.total_attempted > 0 else "—"
            self._cards["accuracy"].set_value(acc)
        except Exception:
            pass
