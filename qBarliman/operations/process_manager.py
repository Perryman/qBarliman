from PySide6.QtCore import QObject, QProcess, Signal


class ProcessManager(QObject):
    processOutput = Signal(str, str)  # stdout, stderr
    processFinished = Signal(int)  # exit code
    processError = Signal(str)  # Error message

    def __init__(self):
        super().__init__()
        self.process = None  # Initialize to None

    def run_process(self, command, arguments):
        # Create a NEW QProcess instance each time.
        self.process = QProcess()
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
        return self.process.processId()
