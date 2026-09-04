"""Main application window — navigation and page routing."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QProgressDialog,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from thelocaltutor.core.logging_config import setup_logging
from thelocaltutor.infrastructure.database import schema
from thelocaltutor.presentation.dialogs.generate_dialog import GenerateDialog
from thelocaltutor.presentation.dialogs.import_dialog import ImportDialog
from thelocaltutor.presentation.widgets.dashboard_widget import DashboardWidget
from thelocaltutor.presentation.widgets.library_widget import LibraryWidget
from thelocaltutor.presentation.widgets.material_widget import MaterialWidget
from thelocaltutor.presentation.widgets.practice_widget import PracticeWidget
from thelocaltutor.presentation.widgets.progress_widget import ProgressWidget
from thelocaltutor.presentation.widgets.results_widget import ResultsWidget
from thelocaltutor.presentation.widgets.settings_widget import SettingsWidget
from thelocaltutor.presentation.widgets.sidebar import Sidebar
from thelocaltutor.presentation.workers.generate_worker import GenerateWorker
from thelocaltutor.presentation.workers.import_worker import ImportWorker


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TheLocalTutor — AI Study Assistant")
        self.resize(1100, 720)
        self._import_worker: ImportWorker | None = None
        self._gen_worker: GenerateWorker | None = None
        self._progress: QProgressDialog | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.page_requested.connect(self._navigate)
        layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._stack.setObjectName("content-area")
        layout.addWidget(self._stack)

        self._dashboard = DashboardWidget()
        self._library = LibraryWidget()
        self._material = MaterialWidget()
        self._practice = PracticeWidget()
        self._results = ResultsWidget()
        self._progress_page = ProgressWidget()
        self._settings = SettingsWidget()

        self._stack.addWidget(self._dashboard)   # 0
        self._stack.addWidget(self._library)     # 1
        self._stack.addWidget(self._material)    # 2
        self._stack.addWidget(self._practice)    # 3
        self._stack.addWidget(self._results)     # 4
        self._stack.addWidget(self._progress_page)  # 5
        self._stack.addWidget(self._settings)   # 6

        # Wire signals
        self._dashboard.import_requested.connect(self._open_import)
        self._dashboard.practice_requested.connect(lambda: self._navigate("library"))
        self._dashboard.library_requested.connect(lambda: self._navigate("library"))

        self._library.import_requested.connect(self._open_import)
        self._library.material_selected.connect(self._open_material)

        self._material.back_requested.connect(lambda: self._navigate("library"))
        self._material.generate_requested.connect(self._open_generate)
        self._material.practice_requested.connect(self._start_practice)

        self._practice.session_finished.connect(self._show_results)
        self._practice.back_requested.connect(lambda: self._navigate("library"))

        self._results.go_to_dashboard.connect(lambda: self._navigate("dashboard"))
        self._results.go_to_library.connect(lambda: self._navigate("library"))
        self._results.practice_again.connect(self._start_practice)

        self._navigate("dashboard")

    # ── Navigation ────────────────────────────────────────────────────────────

    def _navigate(self, page: str) -> None:
        self._sidebar.navigate_to(page)
        pages = {
            "dashboard": 0,
            "library": 1,
            "material": 2,
            "practice": 3,
            "results": 4,
            "progress": 5,
            "settings": 6,
        }
        idx = pages.get(page, 0)
        self._stack.setCurrentIndex(idx)

        if page == "dashboard":
            self._dashboard.refresh()
        elif page == "library":
            self._library.refresh()
        elif page == "progress":
            self._progress_page.refresh()

    # ── Import ────────────────────────────────────────────────────────────────

    def _open_import(self) -> None:
        dlg = ImportDialog(self)
        dlg.import_confirmed.connect(self._start_import)
        dlg.exec()

    def _start_import(self, file_path: str, course: str) -> None:
        self._progress = QProgressDialog("Importing material...", "Cancel", 0, 0, self)
        self._progress.setWindowTitle("Please Wait")
        self._progress.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress.setCancelButton(None)
        self._progress.setMinimumDuration(0)
        self._progress.show()

        self._import_worker = ImportWorker(file_path, course)
        self._import_worker.progress.connect(self._progress.setLabelText)
        self._import_worker.finished_ok.connect(self._import_done)
        self._import_worker.failed.connect(self._import_failed)
        self._import_worker.start()

    def _import_done(self, material_id: int) -> None:
        if self._progress:
            self._progress.close()
            self._progress = None
        self._library.refresh()
        self._dashboard.refresh()
        self._open_material(material_id)

    def _import_failed(self, error: str) -> None:
        if self._progress:
            self._progress.close()
            self._progress = None
        QMessageBox.critical(self, "Import Failed", error)

    # ── Material detail ───────────────────────────────────────────────────────

    def _open_material(self, material_id: int) -> None:
        self._material.load_material(material_id)
        self._navigate("material")

    # ── Generate ──────────────────────────────────────────────────────────────

    def _open_generate(self, material_id: int) -> None:
        from thelocaltutor.services.material_service import get_material
        mat = get_material(material_id)
        if not mat:
            return
        dlg = GenerateDialog(mat.name, self)
        dlg.generate_confirmed.connect(lambda count, types, diff: self._start_generate(material_id, count, types, diff))
        dlg.exec()

    def _start_generate(self, material_id: int, count: int, types: list[str], difficulty: str) -> None:
        self._progress = QProgressDialog("Generating questions...", "Cancel", 0, 0, self)
        self._progress.setWindowTitle("Working")
        self._progress.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress.setCancelButton(None)
        self._progress.setMinimumDuration(0)
        self._progress.show()

        self._gen_worker = GenerateWorker(material_id, count, types, difficulty)
        self._gen_worker.progress.connect(self._progress.setLabelText)
        self._gen_worker.finished_ok.connect(lambda c: self._generate_done(material_id, c))
        self._gen_worker.failed.connect(self._generate_failed)
        self._gen_worker.start()

    def _generate_done(self, material_id: int, count: int) -> None:
        if self._progress:
            self._progress.close()
            self._progress = None
        QMessageBox.information(self, "Done", f"Generated {count} questions.")
        self._material.load_material(material_id)
        self._dashboard.refresh()

    def _generate_failed(self, error: str) -> None:
        if self._progress:
            self._progress.close()
            self._progress = None
        QMessageBox.critical(self, "Generation Failed", error)

    # ── Practice ──────────────────────────────────────────────────────────────

    def _start_practice(self, material_id: int) -> None:
        self._practice.start_practice(material_id)
        self._navigate("practice")

    def _show_results(self, session_id: int) -> None:
        self._results.load_result(session_id)
        self._navigate("results")
        self._dashboard.refresh()
