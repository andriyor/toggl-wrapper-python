"""The main window: a controller that wires data, timers and views together.

It owns the application state and the network orchestration, and drives a
``QStackedWidget`` of three dumb view pages (status / idle / running). The
pages never touch the API; the window never touches widget internals beyond the
small methods the pages expose.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from PySide6 import QtCore, QtGui, QtWidgets

logger = logging.getLogger(__name__)

from .api import TogglClient
from .theme import Theme
from .utils import format_seconds, parse_start
from .widgets import IdlePage, RunningPage, StatusPage
from .workers import run_async

POLL_INTERVAL_MS = 60_000
TICK_INTERVAL_MS = 1_000


class FullscreenTimer(QtWidgets.QWidget):
    def __init__(self, client: TogglClient, *, fullscreen: bool = True):
        super().__init__()
        self.client = client
        self.pool = QtCore.QThreadPool.globalInstance()
        self._fullscreen = fullscreen

        # -- State --------------------------------------------------------- #
        self.workspace_id: int | None = None
        self.projects_by_id: dict[int, dict] = {}
        self.pinned: list[dict] = []
        self.current: dict | None = None  # running entry, or None
        self.start_dt: datetime | None = None
        self.busy = False  # guards against double start/stop

        # -- Views --------------------------------------------------------- #
        self.status_page = StatusPage()
        self.idle_page = IdlePage()
        self.running_page = RunningPage()

        self.stack = QtWidgets.QStackedWidget()
        for page in (self.status_page, self.idle_page, self.running_page):
            self.stack.addWidget(page)

        self.exit_fs_button = QtWidgets.QPushButton("Exit Full Screen")
        self.exit_fs_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.exit_fs_button.setCursor(QtCore.Qt.PointingHandCursor)
        self.exit_fs_button.clicked.connect(self._exit_fullscreen)
        self.exit_fs_button.setVisible(fullscreen)

        top_bar = QtWidgets.QHBoxLayout()
        top_bar.setContentsMargins(12, 8, 12, 0)
        top_bar.addStretch(1)
        top_bar.addWidget(self.exit_fs_button)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(top_bar)
        layout.addWidget(self.stack)

        self.idle_page.selection_changed.connect(self._on_selection_changed)
        self.running_page.stop_requested.connect(self.stop_timer)

        # -- Timers -------------------------------------------------------- #
        self.clock = QtCore.QTimer(self)
        self.clock.setInterval(TICK_INTERVAL_MS)
        self.clock.timeout.connect(self._tick)

        self.poller = QtCore.QTimer(self)
        self.poller.setInterval(POLL_INTERVAL_MS)
        self.poller.timeout.connect(self.refresh_current)

        self.setWindowTitle("Toggl Timer")
        self._apply_theme(None)
        self.status_page.set_message("Loading…")
        self.stack.setCurrentWidget(self.status_page)
        self.bootstrap()

    # -- Theming ------------------------------------------------------------ #
    def _apply_theme(self, color: str | None) -> None:
        theme = Theme.for_color(color)
        theme.apply_window_background(self)
        self.exit_fs_button.setStyleSheet(theme.exit_fs_button_qss())
        for page in (self.status_page, self.idle_page, self.running_page):
            page.apply_theme(theme)

    def _on_selection_changed(self, project: dict | None) -> None:
        self._apply_theme(project.get("color") if project else None)

    # -- Helpers ------------------------------------------------------------ #
    def _run(self, fn, *args, on_result=None, on_error=None) -> None:
        run_async(self.pool, fn, *args, on_result=on_result,
                  on_error=on_error or self._on_error)

    # -- Bootstrap / polling ------------------------------------------------ #
    def bootstrap(self) -> None:
        self._run(self._bootstrap_blocking, on_result=self._on_bootstrap)

    def _bootstrap_blocking(self) -> dict:
        me = self.client.me()
        wid = me["default_workspace_id"]
        return {
            "wid": wid,
            "projects": self.client.projects(wid),
            "current": self.client.current_entry(),
        }

    def _on_bootstrap(self, data: dict) -> None:
        self.workspace_id = data["wid"]
        projects = data["projects"] or []
        self.projects_by_id = {p["id"]: p for p in projects}
        self.pinned = [p for p in projects if p.get("pinned")]
        self.current = data["current"] or None
        self._render()
        self.poller.start()

    def refresh_current(self) -> None:
        if self.busy:
            return
        self._run(self.client.current_entry, on_result=self._on_current,
                  on_error=self._on_poll_error)

    def _on_current(self, entry: dict | None) -> None:
        self.current = entry or None
        self._render()

    # -- Mode rendering ----------------------------------------------------- #
    def _render(self) -> None:
        if self.current:
            self._enter_running()
        else:
            self._enter_idle()

    def _enter_running(self) -> None:
        entry = self.current or {}
        project = self.projects_by_id.get(entry.get("project_id"))
        self.start_dt = parse_start(entry.get("start"))

        self.running_page.set_entry(
            project["name"] if project else "No project",
            entry.get("description"),
        )
        self._apply_theme(project.get("color") if project else None)
        self.stack.setCurrentWidget(self.running_page)

        self._tick()
        self.clock.start()

    def _enter_idle(self) -> None:
        self.clock.stop()
        self.start_dt = None

        if not self.pinned:
            self._apply_theme(None)
            self.status_page.set_message(
                "No pinned projects", "Pin a project in Toggl · Esc to exit"
            )
            self.stack.setCurrentWidget(self.status_page)
            return

        # set_projects emits selection_changed, which recolours the window.
        self.idle_page.set_projects(self.pinned)
        self.stack.setCurrentWidget(self.idle_page)

    # -- Actions ------------------------------------------------------------ #
    def start_timer(self) -> None:
        project = self.idle_page.selected_project()
        if self.busy or project is None or self.workspace_id is None:
            return
        self.busy = True
        self.idle_page.set_title("Starting…")
        self._run(self.client.start, self.workspace_id, project["id"],
                  on_result=self._on_started, on_error=self._on_action_error)

    def _on_started(self, entry: dict | None) -> None:
        self.busy = False
        self.current = entry or None
        self._render()

    def stop_timer(self) -> None:
        if self.busy or not self.current or self.workspace_id is None:
            return
        self.busy = True
        self.running_page.set_stopping(True)
        self._run(self.client.stop, self.workspace_id, self.current["id"],
                  on_result=self._on_stopped, on_error=self._on_action_error)

    def _on_stopped(self, _entry: dict | None) -> None:
        self.busy = False
        self.running_page.set_stopping(False)
        self.current = None
        self._render()

    def _on_action_error(self, message: str) -> None:
        self.busy = False
        self.running_page.set_stopping(False)
        self._on_error(message)

    def _on_poll_error(self, message: str) -> None:
        logger.warning("poll failed (will retry): %s", message)

    def _on_error(self, message: str) -> None:
        logger.error(message)
        self.clock.stop()
        self.status_page.set_message(f"Error: {message}", "Esc to exit")
        self.stack.setCurrentWidget(self.status_page)

    # -- Timer tick --------------------------------------------------------- #
    def _tick(self) -> None:
        if not self.start_dt:
            self.running_page.set_elapsed("00:00:00")
            return
        elapsed = (datetime.now(timezone.utc) - self.start_dt).total_seconds()
        self.running_page.set_elapsed(format_seconds(elapsed))

    # -- Full screen toggle ------------------------------------------------- #
    def _exit_fullscreen(self) -> None:
        self._fullscreen = False
        self.exit_fs_button.setVisible(False)
        self.showNormal()

    # -- Keyboard ----------------------------------------------------------- #
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        key = event.key()
        if key == QtCore.Qt.Key_F11:
            if self._fullscreen:
                self._exit_fullscreen()
            else:
                self._fullscreen = True
                self.exit_fs_button.setVisible(True)
                self.showFullScreen()
            return
        if key in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_Q):
            self.close()
            return
        if key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            if self.current:
                self.stop_timer()
            else:
                self.start_timer()
            return

        # Arrow navigation only matters while idle with a pinned list.
        if self.current or not self.pinned:
            super().keyPressEvent(event)
            return

        if key == QtCore.Qt.Key_Down:
            self.idle_page.move_selection(1)
        elif key == QtCore.Qt.Key_Up:
            self.idle_page.move_selection(-1)
        else:
            super().keyPressEvent(event)
