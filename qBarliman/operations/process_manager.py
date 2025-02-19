import collections
from typing import Deque

from PySide6.QtCore import QObject, QProcess, Signal, Slot


class ProcessManager(QObject):
    """Manages a queue of external process executions."""

    processStarted = Signal(int, str)  # PID, task_type
    processOutput = Signal(str, str, str)  # stdout, stderr, task_type
    processFinished = Signal(int, str)  # exit code, task_type
    processError = Signal(str, str)  # error message, task_type

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process = QProcess(self)
        self._queue: Deque[tuple[str, list[str], str]] = (
            collections.deque()
        )  # command, args, task_type
        self._current_task_type = ""

        self._process.readyReadStandardOutput.connect(self._handle_stdout)
        self._process.readyReadStandardError.connect(self._handle_stderr)
        self._process.finished.connect(self._on_process_finished)
        self._process.errorOccurred.connect(self._handle_error)

    @Slot(str, list, str)
    def enqueue_process(self, command: str, arguments: list[str], task_type: str):
        """Add a process to the execution queue."""
        self._queue.append((command, arguments, task_type))
        if self._process.state() != QProcess.Running:
            self._start_next_process()

    def _start_next_process(self):
        """Start the next process in the queue."""
        if self._queue:
            command, arguments, task_type = self._queue.popleft()
            self._current_task_type = task_type
            self._process.start(command, arguments)
            self.processStarted.emit(self._process.processId(), task_type)

    def _handle_stdout(self):
        if data := self._process.readAllStandardOutput().data().decode():
            self.processOutput.emit(data, "", self._current_task_type)

    def _handle_stderr(self):
        if data := self._process.readAllStandardError().data().decode():
            self.processOutput.emit("", data, self._current_task_type)

    @Slot()
    def kill_current_process(self):
        if self._process.state() == QProcess.Running:
            self._process.kill()

    def _on_process_finished(self, exit_code: int, exit_status: QProcess.ExitStatus):
        self.processFinished.emit(exit_code, self._current_task_type)
        self._start_next_process()

    def _handle_error(self, error: QProcess.ProcessError):
        self.processError.emit(str(error), self._current_task_type)
