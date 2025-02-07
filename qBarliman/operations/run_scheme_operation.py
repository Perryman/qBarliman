import time
from PyQt6.QtCore import QThread, pyqtSignal, QProcess


class RunSchemeOperation(QThread):
    # Define signals for different types of updates
    finishedSignal = pyqtSignal(str, str)  # (taskType, output)
    statusUpdateSignal = pyqtSignal(str, str, str)  # (taskType, status, color)
    spinnerUpdateSignal = pyqtSignal(str, bool)  # (taskType, isSpinning)

    def __init__(self, editor_window_controller, schemeScriptPathString, taskType):
        super().__init__()
        self.schemeScriptPathString = schemeScriptPathString
        self.taskType = taskType
        self._isCanceled = False
        self.process = None  # Initialize as None
        self.start_time = 0

        # Constants
        self.DEFAULT_COLOR = "black"
        self.SYNTAX_ERROR_COLOR = "orange"
        self.PARSE_ERROR_COLOR = "magenta"
        self.FAILED_ERROR_COLOR = "red"
        self.THINKING_COLOR = "purple"

        self.ILLEGAL_SEXPR = "Illegal sexpression"
        self.PARSE_ERROR = "Syntax error"
        self.EVAL_FAILED = "Evaluation failed"
        self.THINKING = "???"

    def run(self):
        if self._isCanceled:
            return

        self.start_time = time.monotonic()
        self.spinnerUpdateSignal.emit(self.taskType, True)
        self.statusUpdateSignal.emit(self.taskType, self.THINKING, self.THINKING_COLOR)

        try:
            self.process = QProcess()  # Create QProcess in the correct thread
            self.process.finished.connect(self.handleProcessFinished)
            self.process.readyReadStandardOutput.connect(self.readStandardOutput)
            self.process.readyReadStandardError.connect(self.readStandardError)
            self.process.errorOccurred.connect(self.handleProcessError)

            self.process.start("scheme", [self.schemeScriptPathString])

        except Exception as e:
            self.finishedSignal.emit(self.taskType, f"Error: {e}")
            self.spinnerUpdateSignal.emit(self.taskType, False)

    def cancel(self):
        self._isCanceled = True
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()

    def handleProcessFinished(self):
        output = self.process.readAllStandardOutput().data().decode()
        err = self.process.readAllStandardError().data().decode()

        if err:
            output += f"\nErrors: {err}"

        self.finishedSignal.emit(self.taskType, output)
        self.spinnerUpdateSignal.emit(self.taskType, False)

    def readStandardOutput(self):
        output = self.process.readAllStandardOutput().data().decode()
        self.finishedSignal.emit(self.taskType, output)

    def readStandardError(self):
        err = self.process.readAllStandardError().data().decode()
        self.finishedSignal.emit(self.taskType, f"Errors: {err}")

    def handleProcessError(self, error):
        self.finishedSignal.emit(self.taskType, f"Process error: {error}")
        self.spinnerUpdateSignal.emit(self.taskType, False)
