import os
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from PySide6.QtCore import QObject, Signal

from config.constants import SCHEME_EXECUTABLE, TMP_DIR
from services.process_manager import ProcessManager
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
    test_index: Optional[int] = field(default=None)  # Add test_index


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
        # No longer storing temp_file_path

        self.process_manager.processOutput.connect(self._handle_output)
        self.process_manager.processFinished.connect(self._handle_finished)
        self.process_manager.processError.connect(self._handle_error)

    def execute_scheme_query(
        self, query: str, task_type: str, test_index: int
    ):  # Add test index.
        """Executes a Scheme query given as a string."""
        if not SCHEME_EXECUTABLE:
            return self._handle_script_error(task_type, "SCHEME_EXECUTABLE not set.")

        self._task_type = task_type
        self.start_time = time.monotonic()
        self.processStarted.emit(task_type)

        # Create a temporary file *within* TMP_DIR, named by test number
        temp_file_path = os.path.join(
            TMP_DIR, f"test_{test_index + 1}.scm"
        )  # Use test index

        try:
            with open(temp_file_path, "w", encoding="utf-8") as temp_file:
                temp_file.write(query)

            # Enqueue the process, using the temporary file's path
            self.process_manager.enqueue_process(
                SCHEME_EXECUTABLE, ["--script", temp_file_path], task_type
            )
        except Exception as e:
            l.warn(f"Error writing to or enqueuing temp file: {e}")
            return self._handle_script_error(task_type, f"File Error: {e}")
        # Store file path for later deletion
        self.temp_file_path = temp_file_path
        self.test_index = test_index

    def _handle_script_error(self, task_type, error_message):
        """Handle errors that occur before execution can start."""
        result = TaskResult(task_type, TaskStatus.FAILED, error_message)
        self.taskResultReady.emit(result)
        return None

    def kill_process(self, pid=None):
        l.debug(f"Kill process, pid={pid}")
        if pid is not None:
            try:
                os.kill(pid, 15)  # SIGTERM
                self._current_process_id = None  # Clear the ID
                result = TaskResult(
                    self._task_type, TaskStatus.TERMINATED, "Process terminated"
                )
                self.taskResultReady.emit(result)
            except ProcessLookupError:
                l.warn(f"Process with PID {pid} not found.")
            except OSError as e:
                l.warn(f"Error killing process {pid}: {e}")

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

    def _handle_finished(self, exit_code: int, task_type: str):
        elapsed_time = time.monotonic() - self.start_time

        l.debug(f"Process finished with exit code {exit_code}")
        l.debug(f"Final stdout: {self._stdout_buffer}")
        l.debug(f"Final stderr: {self._stderr_buffer}")

        result = self._process_output(self._stdout_buffer, self._task_type, exit_code)
        result.elapsed_time = elapsed_time
        result.output = self._stderr_buffer or result.output
        result.test_index = self.test_index  # Set the test index!

        self._stdout_buffer = ""
        self._stderr_buffer = ""

        self.taskResultReady.emit(result)
        self._current_process_id = None
        try:
            os.remove(self.temp_file_path)  # Delete the temp file *after* processing
        except FileNotFoundError:
            l.warn(
                f"Tried to remove temp Scheme file, but it was not found: {self.temp_file_path}"
            )
        except OSError as e:
            l.warn(f"Error removing file: {e}")

        self.temp_file_path = ""  # Reset after deletion
        self.test_index = None  # Clear index.

    def _process_output(
        self, output: str, task_type: str, exit_code: int = 0
    ) -> TaskResult:
        """Processes output, determines status, and returns the appropriate TaskResult."""
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
