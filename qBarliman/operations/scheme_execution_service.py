import os
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtGui import QColor

# trunk-ignore(ruff/F401)
from qBarliman.constants import SCHEME_EXECUTABLE, debug, good, info, warn
from qBarliman.operations.process_manager import ProcessManager


class TaskStatus(Enum):
    SUCCESS = auto()
    PARSE_ERROR = auto()
    SYNTAX_ERROR = auto()
    EVALUATION_FAILED = auto()
    THINKING = auto()
    FAILED = auto()
    TERMINATED = auto()
    # Add other status types as needed


@dataclass
class TaskResult:
    status: TaskStatus
    message: str
    output: str = ""
    elapsed_time: Optional[float] = None


class SchemeExecutionService(QObject):
    """Service for executing Scheme code."""

    processOutput = Signal(str, str, str)  # task_type, stdout, stderr
    processFinished = Signal(str, int)  # task_type, exit_code
    processError = Signal(str, str)  # task_type, error_message
    processStarted = Signal(str)  # task_type

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self.process_manager = ProcessManager()
        self._task_type = ""
        self.start_time = 0
        self.colors = {
            "default": QColor(Qt.GlobalColor.black),
            "syntax_error": QColor(Qt.GlobalColor.darkYellow),
            "parse_error": QColor(Qt.GlobalColor.yellow),
            "failed": QColor(Qt.GlobalColor.red),
            "success": QColor(Qt.GlobalColor.green),
            "thinking": QColor(Qt.GlobalColor.magenta),
        }

        self.process_manager.processOutput.connect(
            lambda stdout, stderr: self.processOutput.emit(
                self._task_type, stdout, stderr
            )
        )
        self.process_manager.processFinished.connect(
            lambda exit_code: self.processFinished.emit(self._task_type, exit_code)
        )
        self.process_manager.processError.connect(
            lambda error_msg: self.processError.emit(self._task_type, error_msg)
        )

        # Simplified and unified output rules.
        self._output_rules = {
            "parse-error-in-defn": (TaskStatus.PARSE_ERROR, "Parse error"),
            "illegal-sexp-in-defn": (TaskStatus.SYNTAX_ERROR, "Illegal sexpression"),
            "()": (TaskStatus.EVALUATION_FAILED, "Evaluation Failed"),
            "illegal-sexp-in-test/answer": (
                TaskStatus.SYNTAX_ERROR,
                "Illegal sexpression",
            ),
            "parse-error-in-test/answer": (
                TaskStatus.SYNTAX_ERROR,
                "Illegal sexpression",
            ),
            "fail": (TaskStatus.FAILED, "Failed"),
            "__default_success__": (
                TaskStatus.SUCCESS,
                "Success",
            ),  # One default for success
            "__thinking__": (TaskStatus.THINKING, "Thinking..."),
            "__default__": (
                TaskStatus.FAILED,
                "Unknown task type",
            ),  # And a fail default
        }

    def execute_scheme(self, script_path: str, task_type: str):
        """Execute a Scheme script."""

        if not os.path.exists(script_path):
            self.processError.emit(task_type, "Script file not found.")
            return
        if not SCHEME_EXECUTABLE:
            self.processError.emit(task_type, "SCHEME_EXECUTABLE not set.")
            return

        self._task_type = task_type
        self.start_time = time.monotonic()
        self.processStarted.emit(task_type)
        command = SCHEME_EXECUTABLE
        arguments = ["--script", script_path]
        self.process_manager.run_process(command, arguments)

    def kill_process(self):
        self.process_manager.kill_process()

    @Slot(str, str, str)
    def _handle_output(self, task_type: str, stdout: str, stderr: str):
        elapsed_time = time.monotonic() - self.start_time
        result = self._process_output(stdout, task_type)
        result.elapsed_time = elapsed_time

        # Now instead of emitting more signals, we could have a slot in the controller
        # that connects to processFinished and there we can call _handle_output to process the
        # output of the execution.

    @Slot(str, int)
    def _handle_finish(self, task_type: str, exit_code: int):
        # Process the output to generate a TaskResult if you need to consolidate the results
        pass

    def _process_output(self, output: str, task_type: str) -> TaskResult:
        """Processes the output string using a unified rule set."""
        output = output.strip()

        # Check for thinking status first
        if (
            output
            in [
                "illegal-sexp-in-defn",
                "parse-error-in-defn",
                "illegal-sexp-in-test/answer",
                "parse-error-in-test/answer",
            ]
            and task_type != "simple"
        ):  # "thinking" applies to all but "simple"
            status, message = self._output_rules["__thinking__"]
            return TaskResult(status, message, output)

        # Direct matches
        if output in self._output_rules:
            status, message = self._output_rules[output]
            return TaskResult(status, message, output)

        # Default success or global default based on task type
        if task_type in ("simple", "test", "allTests"):
            status, message = self._output_rules["__default_success__"]
            return TaskResult(status, message, output)

        # Global default
        status, message = self._output_rules["__default__"]
        return TaskResult(status, message, output)
