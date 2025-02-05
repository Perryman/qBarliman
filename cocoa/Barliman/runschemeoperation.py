import time
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class RunSchemeOperation(QThread):
    # Signal to report when the task is finished: (taskType, output)
    finishedSignal = pyqtSignal(str, str)

    def __init__(self, editorWindowController, schemeScriptPathString, taskType):
        super().__init__()
        self.editorWindowController = editorWindowController
        self.schemeScriptPathString = schemeScriptPathString
        self.taskType = taskType
        self._isCanceled = False

    def run(self):
        if self._isCanceled:
            return
        print(f"Running Scheme operation: {self.taskType} with script: {self.schemeScriptPathString}")
        try:
            # Example: run the scheme script using subprocess.
            # Replace ['scheme', self.schemeScriptPathString] with your actual command.
            result = subprocess.run(
                ['scheme', self.schemeScriptPathString],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout
        except Exception as e:
            output = f"Error: {e}"
        # Simulate delay if needed
        time.sleep(1)
        self.finishedSignal.emit(self.taskType, output)

    def cancel(self):
        self._isCanceled = True
        # Optionally, kill any running subprocess here.
        print(f"Operation {self.taskType} canceled.")
