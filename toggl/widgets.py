"""The three view pages stacked inside the main window.

Each page is a self-contained ``QWidget`` that knows how to render one mode and
how to restyle itself for a :class:`~toggl.theme.Theme`. The window
(:mod:`toggl.window`) swaps between them and feeds them data.
"""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from .theme import Theme


def _centered_label(text: str = "", *, point_size: int | None = None) -> QtWidgets.QLabel:
    label = QtWidgets.QLabel(text)
    label.setAlignment(QtCore.Qt.AlignCenter)
    if point_size is not None:
        font = label.font()
        font.setPointSize(point_size)
        label.setFont(font)
    return label


class StatusPage(QtWidgets.QWidget):
    """A single centred message with an optional hint — loading and errors."""

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.title = _centered_label(point_size=28)
        self.hint = _centered_label()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(24)
        layout.addStretch(1)
        layout.addWidget(self.title)
        layout.addWidget(self.hint)
        layout.addStretch(1)

    def set_message(self, text: str, hint: str = "") -> None:
        self.title.setText(text)
        self.hint.setText(hint)
        self.hint.setVisible(bool(hint))

    def apply_theme(self, theme: Theme) -> None:
        self.title.setStyleSheet(theme.title_qss())
        self.hint.setStyleSheet(theme.hint_qss())


class IdlePage(QtWidgets.QWidget):
    """Pick a pinned project with the keyboard before starting a timer."""

    #: Emitted with the newly-selected project dict whenever selection changes.
    selection_changed = QtCore.Signal(object)

    _HINT = "↑ / ↓ to pick · Enter to start · Esc to exit"

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._theme = Theme.for_color(None)
        self._projects: list[dict] = []
        self._index = 0

        self.title = _centered_label(point_size=28)

        self.list = QtWidgets.QListWidget()
        self.list.setFocusPolicy(QtCore.Qt.NoFocus)  # keys handled by the window
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list.setTextElideMode(QtCore.Qt.ElideNone)
        self.list.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.list.setMaximumHeight(420)

        self.hint = _centered_label(self._HINT)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(24)
        layout.addStretch(1)
        layout.addWidget(self.title)
        layout.addWidget(self.hint)
        layout.addStretch(1)

    # -- Data / selection --------------------------------------------------- #
    def set_projects(self, projects: list[dict]) -> None:
        self._projects = projects
        self._index = min(self._index, max(0, len(projects) - 1))
        self.list.clear()
        for project in projects:
            item = QtWidgets.QListWidgetItem(project.get("name", "Untitled"))
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            font = item.font()
            font.setPointSize(22)
            item.setFont(font)
            self.list.addItem(item)
        self._refresh()

    def move_selection(self, delta: int) -> None:
        if not self._projects:
            return
        self._index = (self._index + delta) % len(self._projects)
        self._refresh()

    def selected_project(self) -> dict | None:
        if not self._projects:
            return None
        return self._projects[self._index]

    def set_title(self, text: str) -> None:
        self.title.setText(text)

    def _restyle_items(self) -> None:
        """Repaint title + items for the current selection. Emits nothing.

        Kept separate from :meth:`_refresh` so re-theming (which calls this)
        can't feed back into ``selection_changed`` and recurse.
        """
        project = self.selected_project()
        self.title.setText(project.get("name", "Pick a project") if project else "")

        # The active project is bold + full colour; the rest are dimmed,
        # mirroring the web version's opacity treatment. (Per-index borders
        # aren't expressible in QSS, so emphasis is via weight + colour.)
        active = self._theme.text_qcolor()
        dim = self._theme.dim_qcolor()
        for i in range(self.list.count()):
            item = self.list.item(i)
            is_active = i == self._index
            font = item.font()
            font.setBold(is_active)
            item.setFont(font)
            item.setForeground(active if is_active else dim)

        current = self.list.item(self._index)
        if current is not None:
            self.list.scrollToItem(current, QtWidgets.QAbstractItemView.EnsureVisible)

    def _refresh(self) -> None:
        """Restyle for the current selection and announce it to the window."""
        self._restyle_items()
        self.selection_changed.emit(self.selected_project())

    # -- Theming ------------------------------------------------------------ #
    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.title.setStyleSheet(theme.title_qss())
        self.hint.setStyleSheet(theme.hint_qss())
        self.list.setStyleSheet(theme.list_qss())
        self._restyle_items()


class RunningPage(QtWidgets.QWidget):
    """Show the running entry's project, description and elapsed time."""

    #: Emitted when the user asks to stop the running timer.
    stop_requested = QtCore.Signal()

    _STOP_TEXT = "⏸  Stop"
    _HINT = "Enter to stop · Esc to exit"

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.title = _centered_label(point_size=28)
        self.desc = _centered_label(point_size=18)

        self.timer = _centered_label("00:00:00")
        mono = QtGui.QFont("monospace")
        mono.setStyleHint(QtGui.QFont.Monospace)
        mono.setPixelSize(160)
        self.timer.setFont(mono)

        self.stop_button = QtWidgets.QPushButton(self._STOP_TEXT)
        self.stop_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.stop_button.setCursor(QtCore.Qt.PointingHandCursor)
        self.stop_button.clicked.connect(self.stop_requested)

        self.hint = _centered_label(self._HINT)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(24)
        layout.addStretch(1)
        layout.addWidget(self.title)
        layout.addWidget(self.desc)
        layout.addWidget(self.timer)
        layout.addWidget(self.stop_button, alignment=QtCore.Qt.AlignHCenter)
        layout.addWidget(self.hint)
        layout.addStretch(1)

    def set_entry(self, title: str, description: str | None) -> None:
        self.title.setText(title)
        self.desc.setText(description or "")
        self.desc.setVisible(bool(description))

    def set_elapsed(self, text: str) -> None:
        self.timer.setText(text)

    def set_stopping(self, stopping: bool) -> None:
        self.stop_button.setText("Stopping…" if stopping else self._STOP_TEXT)
        self.stop_button.setDisabled(stopping)

    def apply_theme(self, theme: Theme) -> None:
        self.title.setStyleSheet(theme.title_qss())
        self.desc.setStyleSheet(theme.title_qss())
        self.timer.setStyleSheet(theme.timer_qss())
        self.stop_button.setStyleSheet(theme.stop_button_qss())
        self.hint.setStyleSheet(theme.hint_qss())
