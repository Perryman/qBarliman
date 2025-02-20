import os
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from PySide6.QtCore import QObject, Signal

from config.constants import SCHEME_EXECUTABLE
from operations.process_manager import ProcessManager
from utils import log as l


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

    taskResultReady = Signal(TaskResult)
    processStarted = Signal(str)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self.process_manager = ProcessManager()
        self._task_type = ""
        self.start_time = 0
        self._current_process_id = None
        self._stdout_buffer = ""
        self._stderr_buffer = ""

        self.process_manager.processOutput.connect(self._handle_output)
        self.process_manager.processFinished.connect(self._handle_finished)
        self.process_manager.processError.connect(self._handle_error)

    def execute_scheme(self, script_path: str, task_type: str):
        """Execute a Scheme script."""
        l.good(f"Execute: scheme --script {script_path}")
        if not os.path.exists(script_path):
            return self._handle_execution_error(task_type, "Script file not found.")
        if not SCHEME_EXECUTABLE:
            return self._handle_execution_error(task_type, "SCHEME_EXECUTABLE not set.")
        self._task_type = task_type
        self.start_time = time.monotonic()
        self.processStarted.emit(task_type)

        self.process_manager.enqueue_process(
            SCHEME_EXECUTABLE, ["--script", script_path], task_type
        )

    # TODO Rename this here and in `execute_scheme`
    def _handle_execution_error(self, task_type, arg1):
        result = TaskResult(task_type, TaskStatus.FAILED, arg1)
        self.taskResultReady.emit(result)
        return None

    def kill_process(self, pid=None):
        l.debug(f"Kill process, pid={pid}")
        if pid is not None:
            try:
                os.kill(pid, 15)  # SIGTERM
                self._current_process_id = None  # Clear the ID
            except ProcessLookupError:
                l.warn(f"Process with PID {pid} not found.")
            except OSError as e:  # more general, catch permission errors etc
                l.warn(f"Error killing process {pid}: {e}")
        # No else case

    def _handle_output(self, stdout: str, stderr: str):
        """Accumulate output from process."""
        if stdout:
            self._stdout_buffer += stdout
        if stderr:
            self._stderr_buffer += stderr
        l.debug(f"Process output - stdout: {stdout}, stderr: {stderr}")

    def _handle_error(self, error: str):
        result = TaskResult(self._task_type, TaskStatus.FAILED, error)
        self.taskResultReady.emit(result)

    def _handle_finished(self, exit_code: int):
        elapsed_time = time.monotonic() - self.start_time

        l.debug(f"Process finished with exit code {exit_code}")
        l.debug(f"Final stdout: {self._stdout_buffer}")
        l.debug(f"Final stderr: {self._stderr_buffer}")

        result = self._process_output(self._stdout_buffer, self._task_type, exit_code)
        result.elapsed_time = elapsed_time
        result.output = self._stderr_buffer or result.output

        self._stdout_buffer = ""
        self._stderr_buffer = ""

        self.taskResultReady.emit(result)
        self._current_process_id = None

    def _process_output(
        self, output: str, task_type: str, exit_code: int = 0
    ) -> TaskResult:
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
        elif output in {"illegal-sexp-in-test/answer", "parse-error-in-test/answer"}:
            status = TaskStatus.SYNTAX_ERROR
            message = "Syntax Error in test"

        elif output == "fail":
            status = TaskStatus.FAILED
            message = "Failed"
        else:
            status = TaskStatus.SUCCESS
            message = "Success"

        return TaskResult(task_type, status, message, output)
