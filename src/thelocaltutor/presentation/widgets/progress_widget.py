"""Progress page — study history and performance overview."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from thelocaltutor.infrastructure.database.repositories import session_repo
from thelocaltutor.services.study_service import get_app_stats


class ProgressWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("content-area")
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

        title = QLabel("Progress")
        title.setObjectName("page-title")
        sub = QLabel("Your study history and performance over time.")
        sub.setObjectName("page-subtitle")
        layout.addWidget(title)
        layout.addWidget(sub)

        # Summary cards
        stats = get_app_stats()
        summary_row = QHBoxLayout()
        summary_row.setSpacing(14)

        for value, label in [
            (str(stats.total_sessions), "Sessions Completed"),
            (str(stats.total_attempted), "Questions Answered"),
            (str(stats.total_correct), "Correct Answers"),
            (f"{stats.overall_accuracy}%", "Overall Accuracy"),
        ]:
            card = QWidget()
            card.setObjectName("stat-card")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(20, 20, 20, 20)
            cl.setSpacing(4)
            v = QLabel(value)
            v.setObjectName("stat-value")
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lb = QLabel(label)
            lb.setObjectName("stat-label")
            lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(v)
            cl.addWidget(lb)
            summary_row.addWidget(card)

        layout.addLayout(summary_row)

        # History
        hist_title = QLabel("Session History")
        hist_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0f172a; margin-top: 8px;")
        layout.addWidget(hist_title)

        self._history_container = QWidget()
        self._history_container.setObjectName("content-area")
        self._history_layout = QVBoxLayout(self._history_container)
        self._history_layout.setContentsMargins(0, 0, 0, 0)
        self._history_layout.setSpacing(8)
        self._history_layout.addStretch()
        layout.addWidget(self._history_container)

        layout.addStretch()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self) -> None:
        layout = self._history_layout
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        from thelocaltutor.services.material_service import list_materials
        materials = {m.id: m for m in list_materials()}

        sessions = []
        for m in materials.values():
            sessions.extend(session_repo.list_sessions_for_material(m.id))
        sessions.sort(key=lambda s: s.started_at, reverse=True)

        if not sessions:
            empty = QLabel("No sessions yet. Start practising to see your history here.")
            empty.setStyleSheet("color: #94a3b8; font-size: 14px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.insertWidget(0, empty)
            return

        for s in sessions:
            mat = materials.get(s.material_id)
            mat_name = mat.name if mat else "Unknown"
            row = QWidget()
            row.setObjectName("card")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(18, 14, 18, 14)
            rl.setSpacing(12)

            score = f"{s.score_percent:.0f}%" if s.score_percent is not None else "—"
            score_lbl = QLabel(score)
            score_lbl.setFixedWidth(60)
            score_color = "#16a34a" if (s.score_percent or 0) >= 75 else "#d97706" if (s.score_percent or 0) >= 60 else "#dc2626"
            score_lbl.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {score_color};")

            info = QVBoxLayout()
            info.setSpacing(2)
            name = QLabel(mat_name)
            name.setStyleSheet("font-size: 14px; font-weight: 600; color: #0f172a;")
            meta = QLabel(
                f"{s.started_at.strftime('%b %d, %Y  %H:%M')}  •  "
                f"{s.correct_count}/{s.total_questions} correct  •  {s.mode.value}"
            )
            meta.setStyleSheet("font-size: 12px; color: #64748b;")
            info.addWidget(name)
            info.addWidget(meta)

            rl.addWidget(score_lbl)
            rl.addLayout(info)
            rl.addStretch()
            layout.insertWidget(layout.count() - 1, row)
