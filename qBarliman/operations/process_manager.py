from PySide6.QtCore import QObject, QProcess, Signal


class ProcessManager(QObject):
    processOutput = Signal(str, str)  # stdout, stderr
    processFinished = Signal(int)  # exit code
    processError = Signal(str)  # Error message

    def __init__(self):
        super().__init__()
        self.process = QProcess()

    def run_process(self, command, arguments):
        self.process.start(command, arguments)

        # Connect *directly* to anonymous functions (lambdas)
        self.process.readyReadStandardOutput.connect(
            lambda: self.processOutput.emit(
                self.process.readAllStandardOutput().data().decode(), ""
            )
        )
        self.process.readyReadStandardError.connect(
            lambda: self.processOutput.emit(
                "", self.process.readAllStandardError().data().decode()
            )
        )
        self.process.finished.connect(
            lambda exitCode, exitStatus: self.processFinished.emit(exitCode)
        )
        self.process.errorOccurred.connect(
            lambda error: self.processError.emit(str(f"{error=}"))
        )

    def kill_process(self):
        if self.process.state() != QProcess.NotRunning:
            self.process.kill()
