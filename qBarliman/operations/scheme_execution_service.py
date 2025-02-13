import os
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from PySide6.QtCore import QObject, Signal

from qBarliman.constants import SCHEME_EXECUTABLE, debug, warn
from qBarliman.operations.process_manager import ProcessManager


class TaskStatus(Enum):
    SUCCESS = auto()
    PARSE_ERROR = auto()
    SYNTAX_ERROR = auto()
    EVALUATION_FAILED = auto()
    THINKING = auto()
    FAILED = auto()
    TERMINATED = auto()


@dataclass
class TaskResult:
    task_type: str
    status: TaskStatus
    message: str
    output: str = ""
    elapsed_time: Optional[float] = None


class SchemeExecutionService(QObject):
    """Service for executing Scheme code."""

    taskResultReady = Signal(TaskResult)  # Single, unified signal
    processStarted = Signal(str)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self.process_manager = ProcessManager()
        self._task_type = ""
        self.start_time = 0

        self.process_manager.processOutput.connect(self._handle_output)
        self.process_manager.processFinished.connect(self._handle_finished)
        self.process_manager.processError.connect(self._handle_error)


    def execute_scheme(self, script_path: str, task_type: str):
        """Execute a Scheme script."""
        debug(f"Execute scheme: {script_path=}")
        if not os.path.exists(script_path):
            result = TaskResult(
                task_type, TaskStatus.FAILED, "Script file not found."
            )
            self.taskResultReady.emit(result)
            return None

        if not SCHEME_EXECUTABLE:
            result = TaskResult(task_type, TaskStatus.FAILED, "SCHEME_EXECUTABLE not set.")
            self.taskResultReady.emit(result)
            return None

        self._task_type = task_type
        self.start_time = time.monotonic()
        self.processStarted.emit(task_type)
        command = SCHEME_EXECUTABLE
        arguments = ["--script", script_path]
        self.process_manager.run_process(command, arguments)
        return self.process_manager.process.processId()

    def kill_process(self, pid=None):
        debug(f"Kill process, pid={pid}")
        if pid is not None:
            try:
                os.kill(pid, 15) #SIGTERM
            except ProcessLookupError:
                warn(f"Process with PID {pid} not found.")
            except OSError as e: #more general, catch permission errors etc
                warn(f"Error killing process {pid}: {e}")
        else:
            self.process_manager.kill_process()

    def _handle_output(self, stdout: str, stderr: str):
        pass  # All processing in _handle_finished

    def _handle_error(self, error: str):
        result = TaskResult(self._task_type, TaskStatus.FAILED, error)
        self.taskResultReady.emit(result)


    def _handle_finished(self, exit_code: int):
        elapsed_time = time.monotonic() - self.start_time
        stdout = self.process_manager.process.readAllStandardOutput().data().decode()
        stderr = self.process_manager.process.readAllStandardError().data().decode()

        result = self._process_output(stdout, self._task_type, exit_code)
        result.elapsed_time = elapsed_time
        result.output = stderr if stderr else result.output
        self.taskResultReady.emit(result)

    def _process_output(self, output: str, task_type: str, exit_code: int = 0) -> TaskResult:
        """Processes output, determines status, *and* sets the color."""
        output = output.strip()

        if exit_code != 0:
            status = TaskStatus.SYNTAX_ERROR
            message = "Syntax Error"
        elif output == "parse-error-in-defn":
            status = TaskStatus.PARSE_ERROR
            message = "Parse error"
        elif output == "illegal-sexp-in-defn":
            status = TaskStatus.SYNTAX_ERROR
            message = "Illegal s-expression"
        elif output == "()":
            status = TaskStatus.EVALUATION_FAILED
            message = "Evaluation Failed"
        elif (
            output == "illegal-sexp-in-test/answer"
            or output == "parse-error-in-test/answer"
        ):
            status = TaskStatus.SYNTAX_ERROR
            message = "Syntax Error in test"

        elif output == "fail":
            status = TaskStatus.FAILED
            message = "Failed"
        else:
            status = TaskStatus.SUCCESS
            message = "Success"

        return TaskResult(task_type, status, message, output) # No more color here