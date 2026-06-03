"""Run blocking calls in Qt's thread pool and deliver results via signals."""

from __future__ import annotations

from typing import Callable

from PySide6 import QtCore


class WorkerSignals(QtCore.QObject):
    """Signals emitted by a :class:`Worker` (``QRunnable`` can't define them)."""

    result = QtCore.Signal(object)
    error = QtCore.Signal(str)


class Worker(QtCore.QRunnable):
    """Invoke ``fn(*args, **kwargs)`` on a pool thread, emitting the outcome."""

    def __init__(self, fn: Callable, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self.signals = WorkerSignals()

    @QtCore.Slot()
    def run(self) -> None:
        try:
            value = self._fn(*self._args, **self._kwargs)
        except Exception as exc:  # noqa: BLE001 - surfaced to the UI
            self.signals.error.emit(str(exc))
        else:
            self.signals.result.emit(value)


def run_async(
    pool: QtCore.QThreadPool,
    fn: Callable,
    *args,
    on_result: Callable | None = None,
    on_error: Callable | None = None,
) -> None:
    """Schedule ``fn`` on ``pool`` and route its result/error to callbacks."""
    worker = Worker(fn, *args)
    if on_result is not None:
        worker.signals.result.connect(on_result)
    if on_error is not None:
        worker.signals.error.connect(on_error)
    pool.start(worker)
