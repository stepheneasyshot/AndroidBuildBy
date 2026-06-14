from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from .ui.main_window import MainWindow
from .ui.styles import APP_NAME, MAIN_STYLESHEET

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)


def main():
    logging.getLogger("androguard").setLevel(logging.WARNING)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("AndroidBuildBy")
    app.setStyleSheet(MAIN_STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
