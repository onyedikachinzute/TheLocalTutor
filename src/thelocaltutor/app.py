"""Application entry point."""

from __future__ import annotations

import sys

from PySide6.QtGui import QFontDatabase, QFont
from PySide6.QtWidgets import QApplication

from thelocaltutor.core.logging_config import setup_logging
from thelocaltutor.infrastructure.database import schema
from thelocaltutor.presentation.main_window import MainWindow


def main() -> int:
    setup_logging()
    schema.initialise()

    app = QApplication(sys.argv)
    app.setApplicationName("TheLocalTutor")
    app.setApplicationDisplayName("TheLocalTutor")

    # Load stylesheet
    from pathlib import Path
    style_path = Path(__file__).parent / "presentation" / "styles" / "app_style.qss"
    if style_path.exists():
        with style_path.open() as f:
            app.setStyleSheet(f.read())

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
