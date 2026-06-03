"""Application entry point."""

from __future__ import annotations

import sys

from PySide6 import QtWidgets

from .api import TogglClient
from .config import load_token
from .window import FullscreenTimer


def main() -> None:
    token = load_token()
    app = QtWidgets.QApplication(sys.argv)
    window = FullscreenTimer(TogglClient(token))
    window.showFullScreen()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
