from PySide6.QtCore import QObject, QProcess, Signal


class ProcessManager(QObject):
    """Manages external process execution."""

    processStarted = Signal(int)  # PID
    processOutput = Signal(str, str)  # stdout, stderr
    processFinished = Signal(int)  # exit code
    processError = Signal(str)  # error message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process = QProcess(self)

        # Connect QProcess signals directly
        self._process.started.connect(
            lambda: self.processStarted.emit(self._process.processId())
        )
        self._process.readyReadStandardOutput.connect(self._handle_stdout)
        self._process.readyReadStandardError.connect(self._handle_stderr)
        self._process.finished.connect(lambda code, _: self.processFinished.emit(code))
        self._process.errorOccurred.connect(
            lambda error: self.processError.emit(str(error))
        )

    @property
    def process(self) -> QProcess:
        return self._process

    def run_process(self, command: str, arguments: list[str]) -> int:
        """Start process and return PID."""
        self._stdout_buffer = ""
        self._stderr_buffer = ""
        self._process.start(command, arguments)
        return self._process.processId()

    def _handle_stdout(self):
        if data := self._process.readAllStandardOutput().data().decode():
            self.processOutput.emit(data, "")

    def _handle_stderr(self):
        if data := self._process.readAllStandardError().data().decode():
            self.processOutput.emit("", data)
