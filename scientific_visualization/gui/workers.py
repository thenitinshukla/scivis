"""Generic background-execution helper for the Qt GUI layer.

Nothing in this module contains scientific logic: it only moves an
already-existing callable off the GUI thread so the application stays
responsive while it runs. This is intentionally tiny and dependency-free
(pure PyQt5) so it can be reused by any tab (ML training, movie export,
future long-running analysis) without introducing new coupling between
the GUI and the science/ML layers -- the worker is handed a plain
Python callable and only ever talks back to Qt through signals.

Threading note (important, and the reason for `_ResultBridge` below):
Qt's "auto" connection type decides whether a signal is delivered
directly (synchronously, in the emitting thread) or queued (asynchronously,
posted to the receiving object's own thread) by comparing the *receiver
object's* thread affinity against the emitting thread at emit time. That
only works when the receiver is an actual QObject living on a known
thread. Connecting a worker thread's signal straight to a plain Python
function/lambda (as an earlier version of this module did) gives Qt no
receiver object to check, so PyQt falls back to a direct connection --
meaning the "on the GUI thread" callback silently executes on the
*worker* thread instead. That, in turn, made cleanup's `thread.wait()`
call wait on its own thread (a no-op Qt just warns about and returns from
immediately), so the QThread could still be finishing up in the
background after Python believed it was done and dropped its last
reference -- a real "QThread destroyed while still running" crash, not
just a cosmetic issue.

The fix is `_ResultBridge`: a tiny QObject created on (and left on) the
GUI thread. Connecting the worker's signals to *its* bound methods gives
Qt a receiver whose thread affinity is unambiguous, so the connection is
correctly auto-queued back to the GUI thread, and cleanup only ever runs
there.
"""
from __future__ import annotations

from typing import Any, Callable

from PyQt5.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QProgressDialog, QWidget


class _CallableWorker(QObject):
    finished = pyqtSignal(object)
    failed = pyqtSignal(Exception)

    def __init__(self, fn: Callable[[], Any]):
        super().__init__()
        self._fn = fn

    def run(self):
        try:
            result = self._fn()
        except Exception as exc:  # noqa: BLE001 - surfaced to the caller, not swallowed
            self.failed.emit(exc)
        else:
            self.finished.emit(result)


class _ResultBridge(QObject):
    """Lives on the GUI thread for its entire life (never moved). Receiving
    the worker's finished/failed signals here -- instead of on a plain
    Python callable -- is what makes Qt correctly auto-queue the delivery
    back to the GUI thread. See the module docstring for why that matters.
    """

    def __init__(self, thread: QThread, worker: _CallableWorker, progress: QProgressDialog,
                 on_success: Callable[[Any], None], on_error: Callable[[Exception], None]):
        super().__init__()
        self._thread = thread
        self._worker = worker
        self._progress = progress
        self._on_success = on_success
        self._on_error = on_error
        self._cancelled = False

    def _cleanup(self):
        # Runs on the GUI thread (see class docstring), so this genuinely
        # waits for the *worker* thread to finish -- not a no-op self-wait.
        self._thread.quit()
        self._thread.wait()
        self._thread.deleteLater()
        self._worker.deleteLater()

    def on_finished(self, result: Any):
        # QProgressDialog.close() emits its own `canceled` signal internally,
        # even when closed programmatically (not by the user). Block signals
        # first so that self-inflicted close doesn't get misread as the user
        # pressing Cancel and suppress the real result below.
        self._progress.blockSignals(True)
        self._progress.close()
        self._cleanup()
        if not self._cancelled:
            self._on_success(result)

    def on_failed(self, exc: Exception):
        self._progress.blockSignals(True)
        self._progress.close()
        self._cleanup()
        if not self._cancelled:
            self._on_error(exc)

    def on_cancel(self):
        self._cancelled = True
        self._progress.close()


def run_in_background(
    parent: QWidget,
    fn: Callable[[], Any],
    *,
    on_success: Callable[[Any], None],
    on_error: Callable[[Exception], None],
    label: str = "Working…",
):
    """Run ``fn`` on a worker thread while showing a busy dialog.

    ``fn`` must not touch any Qt widgets -- it should only call into the
    deterministic, Qt-independent science/ML/export APIs. ``on_success``
    and ``on_error`` run back on the GUI thread and are the only places
    that should update widgets, so existing tab code can keep its current
    widget-updating logic unchanged and simply call this wrapper instead
    of calling ``fn`` directly.

    The dialog's Cancel button does not interrupt ``fn`` (safely
    cancelling arbitrary NumPy/scikit-learn/OpenCV work mid-call is not
    generally possible) -- it only stops the GUI from waiting on/for the
    result, so the user is not stuck staring at a frozen window.
    """
    thread = QThread(parent)
    worker = _CallableWorker(fn)
    worker.moveToThread(thread)

    progress = QProgressDialog(label, "Cancel", 0, 0, parent)
    progress.setWindowModality(Qt.WindowModal)
    progress.setMinimumDuration(0)
    progress.setAutoClose(True)
    progress.setAutoReset(True)

    bridge = _ResultBridge(thread, worker, progress, on_success, on_error)
    bridge.setParent(parent)
    # Belt-and-suspenders: also anchor a strong reference via the thread
    # object itself, so the bridge can't be garbage-collected early even
    # in a context where `parent` doesn't keep Qt-parented children alive
    # as expected (e.g. some test harnesses).
    thread._bridge = bridge  # type: ignore[attr-defined]

    thread.started.connect(worker.run)
    worker.finished.connect(bridge.on_finished)
    worker.failed.connect(bridge.on_failed)
    progress.canceled.connect(bridge.on_cancel)

    thread.start()
    progress.show()
