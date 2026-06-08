"""Application entry point."""

from __future__ import annotations

import argparse
import sys

from PySide6 import QtWidgets

from .api import TogglClient
from .config import load_token
from .window import FullscreenTimer


def main() -> None:
    parser = argparse.ArgumentParser(description="Toggl Timer")
    parser.add_argument(
        "--no-fullscreen",
        action="store_true",
        help="Start in windowed mode instead of full screen",
    )
    args, qt_args = parser.parse_known_args()

    token = load_token()
    app = QtWidgets.QApplication([sys.argv[0]] + qt_args)
    fullscreen = not args.no_fullscreen
    window = FullscreenTimer(TogglClient(token), fullscreen=fullscreen)
    if fullscreen:
        window.showFullScreen()
    else:
        window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
