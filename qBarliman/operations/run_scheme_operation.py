import subprocess
import time
from PyQt6.QtCore import QThread, pyqtSignal


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
        self.process = None
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
            self.process = subprocess.Popen(
                ["scheme", self.schemeScriptPathString],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            output, err = self.process.communicate()

            if err:
                output += f"\nErrors: {err}"

            # Let the main window handle the output processing
            self.finishedSignal.emit(self.taskType, output)

        except Exception as e:
            self.finishedSignal.emit(self.taskType, f"Error: {e}")
        finally:
            self.spinnerUpdateSignal.emit(self.taskType, False)

    def cancel(self):
        self._isCanceled = True
        if self.process:
            try:
                self.process.kill()
            except Exception as e:
                print(f"Error killing process: {e}")
