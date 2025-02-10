import os
import traceback
from typing import Optional
from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import QThreadPool, Signal, Slot, QObject, QRunnable, QTimer

from qBarliman.models.scheme_document import SchemeDocument
from qBarliman.views.editor_window_ui import EditorWindowUI
from qBarliman.operations.run_scheme_operation import SchemeExecutionService
from qBarliman.utils.load_interpreter import load_interpreter_code
from qBarliman.utils.query_builder import QueryBuilder
from qBarliman.constants import warn, good, info, debug


class EditorWindowController(QObject):
    # Define signals
    definitionTextChanged = Signal(str)
    testInputChanged = Signal(int, str)
    testOutputChanged = Signal(int, str)
    statusUpdated = Signal(str, str, str)
    bestGuessUpdated = Signal(str, str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.model = SchemeDocument()
        self.mainWindow = QMainWindow()
        self.view = EditorWindowUI()
        self.view.setMainWindow(self.mainWindow)
        self.threadPool = QThreadPool()

        # Setup code execution timer
        self.run_code_timer = QTimer(self)
        self.run_code_timer.setInterval(1000)
        self.run_code_timer.timeout.connect(self.runCodeFromEditPane)

        # Load interpreter code and initialize query builder
        self.interpreter_code = load_interpreter_code()
        if self.interpreter_code:
            self.query_builder = QueryBuilder(self.interpreter_code)
            info("Editor window controller initialized")
        else:
            warn("Failed to load interpreter code. Exiting...")
            exit(1)

        self.setup_connections()

    def setup_connections(self) -> None:
        """Setup signal/slot connections"""
        # Connect signals to slots
        self.definitionTextChanged.connect(self._on_definition_text_changed)
        self.testInputChanged.connect(self._handle_test_input)
        self.testOutputChanged.connect(self._handle_test_output)
        self.statusUpdated.connect(self._handle_status_update)
        self.bestGuessUpdated.connect(self._handle_best_guess)

    @Slot()
    def _handle_test_input(self) -> None:
        """Internal slot for test input changes"""
        if (
            self.model
            and hasattr(self, "_last_test_number")
            and hasattr(self, "_last_test_text")
        ):
            self.handleTestInput(self._last_test_number, self._last_test_text)

    def handleTestInput(self, test_number: int, text: str) -> None:
        """Public method for handling test input changes"""
        self._last_test_number = test_number
        self._last_test_text = text
        if self.model:
            self.testInputChanged.emit(test_number, text)

    @Slot()
    def _handle_test_output(self) -> None:
        """Internal slot for test output changes"""
        if (
            self.model
            and hasattr(self, "_last_test_number")
            and hasattr(self, "_last_test_text")
        ):
            self.handleTestOutput(self._last_test_number, self._last_test_text)

    def handleTestOutput(self, test_number: int, text: str) -> None:
        """Public method for handling test output changes"""
        self._last_test_number = test_number
        self._last_test_text = text
        if self.model:
            self.testOutputChanged.emit(test_number, text)

    @Slot()
    def _on_definition_text_changed(self) -> None:
        """Internal slot for definition text changes"""
        if self.view and self.model:
            text = self.view.schemeDefinitionView.toPlainText()
            self.definitionTextChanged.emit(text)

    @Slot()
    def _handle_status_update(self) -> None:
        """Internal slot for status updates"""
        if (
            hasattr(self, "_last_task_type")
            and hasattr(self, "_last_status")
            and hasattr(self, "_last_color")
        ):
            self.handleStatusUpdate(
                self._last_task_type, self._last_status, self._last_color
            )

    def handleStatusUpdate(self, taskType: str, status: str, color: str) -> None:
        """Public method for handling status updates"""
        self._last_task_type = taskType
        self._last_status = status
        self._last_color = color
        if self.view:
            if taskType == "simple":
                self.view.setDefinitionStatus(status, color)
            elif taskType == "allTests":
                self.view.setBestGuessStatus(status, color)

    @Slot()
    def _handle_best_guess(self) -> None:
        """Internal slot for best guess updates"""
        if hasattr(self, "_last_task_type") and hasattr(self, "_last_output"):
            self.updateBestGuess(self._last_task_type, self._last_output)

    def updateBestGuess(self, taskType: str, output: str) -> None:
        """Public method for updating best guess"""
        self._last_task_type = taskType
        self._last_output = output
        if taskType == "allTests" and self.model:
            self.bestGuessUpdated.emit(taskType, output)

    def runCodeFromEditPane(self) -> None:
        """Run the Scheme code from edit pane"""
        try:
            if self.model and self.model.validate():
                simple_op = SchemeExecutionService(self)
                if isinstance(simple_op, QRunnable):
                    self.threadPool.start(simple_op)
                else:
                    warn("SchemeExecutionService must inherit from QRunnable")
        except Exception as e:
            warn(f"Error running code: {e}")
            warn(f"Traceback: {traceback.format_exc()}")

    def runAllTests(self) -> None:
        """Run all tests"""
        try:
            if self.model and self.model.validate():
                alltests_op = SchemeExecutionService(self)
                if isinstance(alltests_op, QRunnable):
                    self.threadPool.start(alltests_op)
                else:
                    warn("SchemeExecutionService must inherit from QRunnable")
        except Exception as e:
            warn(f"Error running tests: {e}")
            warn(f"Traceback: {traceback.format_exc()}")

    def cancel_all_operations(self) -> None:
        """Cancel all running operations"""
        if hasattr(self, "threadPool"):
            self.threadPool.clear()

    def cleanup(self) -> None:
        """Clean up resources"""
        self.cancel_all_operations()
        if hasattr(self, "run_code_timer"):
            self.run_code_timer.stop()
