"""Background worker for importing and processing materials."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from thelocaltutor.services import material_service


class ImportWorker(QThread):
    progress = Signal(str)
    finished_ok = Signal(int)  # material_id
    failed = Signal(str)

    def __init__(self, file_path: str, course: str, parent=None):
        super().__init__(parent)
        self._file_path = file_path
        self._course = course

    def run(self) -> None:
        try:
            self.progress.emit("Importing file...")
            material_id = material_service.import_file(self._file_path, self._course)

            self.progress.emit("Parsing document...")
            material_service.process_material(material_id)

            self.finished_ok.emit(material_id)
        except Exception as exc:
            self.failed.emit(str(exc))
