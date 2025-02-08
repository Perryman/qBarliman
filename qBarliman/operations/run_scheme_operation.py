import time
import os
from PySide6.QtCore import QThread, Signal, QProcess, Slot
from qBarliman.constants import *


class RunSchemeOperation(QThread):
    finishedSignal = Signal(str, str)  # (taskType, output)
    statusUpdateSignal = Signal(str, str, str)  # (taskType, status, color)
    timerUpdateSignal = Signal(str, float)  # (taskType, elapsedTime)

    def __init__(self, editor_window_controller, schemeScriptPathString, taskType):
        super().__init__()
        self.schemeScriptPathString = schemeScriptPathString
        self.taskType = taskType
        self._isCanceled = False
        self.process = None
        self.start_time = time.monotonic()

        # Basic status constants
        self.THINKING = "???"
        self.THINKING_COLOR = "purple"

    def run(self):
        if self._isCanceled:
            print("RunSchemeOperation: Operation was canceled before start")
            return

        try:
            print(f"RunSchemeOperation: Creating process for {self.taskType}")
            self.process = QProcess()
            self.process.finished.connect(self.handleProcessFinished)
            self.process.readyReadStandardOutput.connect(self.readStandardOutput)
            self.process.readyReadStandardError.connect(self.readStandardError)
            self.process.errorOccurred.connect(self.handleProcessError)

            print(
                f"RunSchemeOperation: Starting process with script {self.schemeScriptPathString}"
            )
            self.process.start(SCHEME_EXECUTABLE, [self.schemeScriptPathString])
            print("RunSchemeOperation: Process started.")

            # Wait briefly for process to start
            if not self.process.waitForStarted(1000):
                print("RunSchemeOperation: Process failed to start within timeout!")
            else:
                print(
                    f"RunSchemeOperation: Process state after start: {self.process.state()}"
                )

        except Exception as e:
            print(f"RunSchemeOperation: Exception during process start: {e}")
            self.finishedSignal.emit(self.taskType, f"Error: {e}")

    def cancel(self):
        debug(
            f"RunSchemeOperation.cancel: entry - Canceling operation for taskType={self.taskType}"
        )
        if self.process:
            debug(
                f"RunSchemeOperation.cancel: - Process state before terminate: {self.process.state()}"
            )
            debug(
                f"RunSchemeOperation.cancel: - Process ID: {self.process.processId()}"
            )

        self._isCanceled = True
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            debug("RunSchemeOperation.cancel: Attempting graceful termination")
            self.process.terminate()  # Try terminate first
            if not self.process.waitForFinished(1000):  # Wait up to 1 second
                debug(
                    "RunSchemeOperation.cancel: Process didn't terminate, forcing kill"
                )
                self.process.kill()  # Force kill if terminate doesn't work

        if self.process:
            debug(
                f"RunSchemeOperation.cancel: - Process state after terminate: {self.process.state()}"
            )

    @Slot()
    def handleProcessFinished(self):
        debug("RunSchemeOperation.handleProcessFinished: ENTRY - handler called!")
        debug(
            f"RunSchemeOperation.handleProcessFinished: Process finished at {time.time():.3f}"
        )
        output = self.process.readAllStandardOutput().data().decode()
        err = self.process.readAllStandardError().data().decode()
        debug(
            f"RunSchemeOperation.handleProcessFinished: Exit code: {self.process.exitCode()}"
        )
        debug(
            f"RunSchemeOperation.handleProcessFinished: Exit status: {self.process.exitStatus()}"
        )

        debug(
            f"RunSchemeOperation.handleProcessFinished: Output size: {len(output)} bytes"
        )
        if output:
            debug(
                f"RunSchemeOperation.handleProcessFinished: First 100 chars: {output[:100]}"
            )
        if err:
            debug(f"RunSchemeOperation.handleProcessFinished: Error: {err}")

        self.finishedSignal.emit(
            self.taskType, output if not err else f"{output}\nErrors: {err}"
        )
        elapsed = time.monotonic() - self.start_time
        print(f"RunSchemeOperation.handleProcessFinished: Completed in {elapsed:.2f}s")

    def readStandardOutput(self):
        debug("RunSchemeOperation.readStandardOutput: ENTRY - handler called!")
        output = self.process.readAllStandardOutput().data().decode()
        debug(f"RunSchemeOperation.readStandardOutput: Got {len(output)} bytes")
        self.finishedSignal.emit(self.taskType, output)

    def readStandardError(self):
        debug("RunSchemeOperation.readStandardError: ENTRY - handler called!")
        err = self.process.readAllStandardError().data().decode()
        debug(f"RunSchemeOperation.readStandardError: Got {len(err)} bytes")
        self.finishedSignal.emit(self.taskType, f"Errors: {err}")

    def handleProcessError(self, error):
        debug(
            f"RunSchemeOperation.handleProcessError: ENTRY - handler called! error={error}"
        )
        debug(f"RunSchemeOperation.handleProcessError: State={self.process.state()}")
        debug(f"RunSchemeOperation.handleProcessError: Error={self.process.error()}")
        debug(
            f"RunSchemeOperation.handleProcessError: ExitCode={self.process.exitCode()}"
        )
        self.finishedSignal.emit(
            self.taskType, f"Process error: {self.process.error()}"
        )
