"""Background worker for AI question generation."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from thelocaltutor.services import question_service


class GenerateWorker(QThread):
    progress = Signal(str)
    finished_ok = Signal(int)  # count
    failed = Signal(str)

    def __init__(self, material_id: int, count: int, types: list[str], difficulty: str, parent=None):
        super().__init__(parent)
        self._material_id = material_id
        self._count = count
        self._types = types
        self._difficulty = difficulty

    def run(self) -> None:
        try:
            self.progress.emit("Generating questions with AI... this may take a minute.")
            questions = question_service.generate_for_material(
                self._material_id,
                self._count,
                self._types,
                self._difficulty,
            )
            self.finished_ok.emit(len(questions))
        except Exception as exc:
            self.failed.emit(str(exc))
