"""Colour scheme derived from a project's colour.

Mirrors the web version: the window takes on the project's colour and text
switches between dark and light for contrast.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6 import QtGui

from .utils import is_dark

_DEFAULT_BACKGROUND = "#1a1a1a"


@dataclass(frozen=True)
class Theme:
    """A resolved colour scheme: window background plus text colours."""

    background: str
    text: str
    subtext: str

    @classmethod
    def for_color(cls, color: str | None) -> "Theme":
        dark = is_dark(color)
        return cls(
            background=color or _DEFAULT_BACKGROUND,
            text="#ffffff" if dark else "#111111",
            subtext="rgba(255,255,255,0.75)" if dark else "rgba(0,0,0,0.6)",
        )

    # -- Convenience accessors used by the widgets -------------------------- #
    def text_qcolor(self) -> QtGui.QColor:
        return QtGui.QColor(self.text)

    def dim_qcolor(self, alpha: int = 110) -> QtGui.QColor:
        color = QtGui.QColor(self.text)
        color.setAlpha(alpha)
        return color

    def apply_window_background(self, widget) -> None:
        pal = widget.palette()
        pal.setColor(QtGui.QPalette.Window, QtGui.QColor(self.background))
        widget.setPalette(pal)
        widget.setAutoFillBackground(True)

    # -- Stylesheets -------------------------------------------------------- #
    def title_qss(self) -> str:
        return f"color: {self.subtext};"

    def timer_qss(self) -> str:
        return f"color: {self.text};"

    def hint_qss(self) -> str:
        return f"color: {self.subtext}; font-size: 16px;"

    def stop_button_qss(self) -> str:
        return f"""
            QPushButton {{
                color: {self.text};
                background: transparent;
                border: 2px solid {self.text};
                border-radius: 10px;
                padding: 12px 28px;
                font-size: 20px;
            }}
            QPushButton:hover {{ background: rgba(127,127,127,0.2); }}
        """

    def exit_fs_button_qss(self) -> str:
        return f"""
            QPushButton {{
                color: {self.subtext};
                background: transparent;
                border: 1px solid {self.subtext};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: rgba(127,127,127,0.2); }}
        """

    def list_qss(self) -> str:
        return """
            QListWidget { background: transparent; border: none; outline: none; }
            QListWidget::item {
                border: 2px solid transparent;
                border-radius: 6px;
                padding: 8px 24px;
            }
            QListWidget::item:selected { background: transparent; }
        """
