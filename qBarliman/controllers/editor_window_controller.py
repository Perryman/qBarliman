import os
import traceback
from typing import List
from PySide6.QtWidgets import QMainWindow, QTextEdit, QLineEdit, QLabel
from PySide6.QtCore import QThreadPool, QTimer, Slot, Property, QObject, Signal

from qBarliman.operations.run_scheme_operation import RunSchemeOperation, EditorWindowInterface
from qBarliman.constants import *
from qBarliman.utils.query_builder import QueryBuilder
from qBarliman.models.scheme_document import SchemeDocument
from qBarliman.views.editor_window_ui import EditorWindowUI

class EditorWindowController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = SchemeDocument()
        self.mainWindow = QMainWindow()
        self.view = EditorWindowUI()
        self.mainWindow.setCentralWidget(self.view)
        self.query_builder = QueryBuilder("some_interpreter_code") # Replace with actual code loading
        self.threadPool = QThreadPool()
        self.run_code_timer = QTimer()
        self.run_code_timer.setInterval(1000)  # Adjust interval as needed
        self.run_code_timer.timeout.connect(self.runCodeFromEditPane)
        self.setup_connections()

    def setWindowTitle(self, title: str):
        self.mainWindow.setWindowTitle(title)

    def resize(self, width: int, height: int):
        self.mainWindow.resize(width, height)

    def show(self):
        self.mainWindow.show()

    def set_model(self, model: SchemeDocument):
        self.model = model
        self.setup_connections()

    def set_view(self, view: EditorWindowUI):
        self.view = view
        self.setup_connections()

    def setup_connections(self):
        if self.model and self.view:
            # Model to View
            self.model.definitionTextChanged.connect(self.view.setBestGuess)
            self.model.testCasesChanged.connect(self.view.setTestStatus)
            
            # View to Model
            self.view.definitionTextChanged.connect(self.on_definition_text_changed)
            self.view.testInputChanged.connect(self.on_test_input_changed)
            self.view.testOutputChanged.connect(self.on_test_output_changed)

    @Slot()
    def on_definition_text_changed(self) -> None:
        """Handle changes to the definition text"""
        self.model.set_definitionText(self.view.schemeDefinitionView.toPlainText())
        self.run_code_timer.start()
    
    @Slot()
    def on_test_inputs_changed(self) -> None:
        """Handle changes to test inputs/outputs"""
        inputs = [inp.text() for inp in self.view.testInputs]
        expected = [exp.text() for exp in self.view.testExpectedOutputs]
        self.model.updateTests(inputs, expected)
        self.run_code_timer.start()
    
    @Slot(int, str)
    def on_test_input_changed(self, test_number: int, text: str) -> None:
        """Handle changes to individual test inputs"""
        self.model.setTestInput(test_number, text)
        self.run_code_timer.start()
    
    @Slot(int, str)
    def on_test_output_changed(self, test_number: int, text: str) -> None:
        """Handle changes to individual test outputs"""
        self.model.setTestExpected(test_number, text)
        self.run_code_timer.start()

    @Slot()
    def runCodeFromEditPane(self) -> None:
        """Run code when timer expires"""
        debug("runCodeFromEditPane: starting code execution")
        try:
            # Build queries from model
            query_simple = self.query_builder.build_simple_query(self.model)
            query_alltests = self.query_builder.build_all_tests_query(self.model)
            
            # Write query files
            with open(os.path.join(TMP_DIR, BARLIMAN_QUERY_SIMPLE_SCM), "w") as f:
                f.write(query_simple)
            with open(os.path.join(TMP_DIR, BARLIMAN_QUERY_ALLTESTS_SCM), "w") as f:
                f.write(query_alltests)
            
            # Create and configure operations
            simple_op = RunSchemeOperation(
                self, 
                os.path.join(TMP_DIR, BARLIMAN_QUERY_SIMPLE_SCM), 
                "simple"
            )
            alltests_op = RunSchemeOperation(
                self,
                os.path.join(TMP_DIR, BARLIMAN_QUERY_ALLTESTS_SCM),
                "allTests"
            )
            
            # Connect operation signals
            simple_op.finishedSignal.connect(self.handleOperationFinished)
            simple_op.statusUpdateSignal.connect(self.handleStatusUpdate)
            
            alltests_op.finishedSignal.connect(self.handleOperationFinished)
            alltests_op.statusUpdateSignal.connect(self.handleStatusUpdate)
            
            # Start operations
            self.threadPool.start(simple_op)
            self.threadPool.start(alltests_op)
            
        except Exception as e:
            warn(f"Exception in runCodeFromEditPane: {e}")
            debug(f"Traceback: {traceback.format_exc()}")
            self.view.showErrorOutput(str(e))
    
    @Slot(str, str)
    def handleOperationFinished(self, taskType: str, output: str) -> None:
        """Handle operation completion"""
        if taskType == "simple":
            self.view.setBestGuess(output)
        elif taskType == "allTests":
            self.view.setBestGuessStatus("Finished all tests", "green")
        elif taskType == "error":
            self.view.showErrorOutput(output)
    
    @Slot(str, str, str)
    def handleStatusUpdate(self, taskType: str, status: str, color: str) -> None:
        """Handle status updates from operations"""
        if taskType == "simple":
            self.view.setDefinitionStatus(status, color)
        elif taskType == "allTests":
            self.view.setBestGuessStatus(status, color)
    
    def cleanup(self) -> None:
        """Clean up resources using Qt's built-in functionality"""
        debug("cleanup: entry - starting cleanup process")
        info("cleaning up!")
        try:
            # Stop all timers first
            for timer in self.mainWindow.findChildren(QTimer):
                if timer.isActive():
                    timer.stop()

            # Clean up processes
            for operation in self.mainWindow.findChildren(RunSchemeOperation):
                if operation is not None and operation.isRunning():
                    debug("!!! cancel called!")
                    try:
                        operation.cancel()
                    except Exception as e:
                        warn(f"Error cancelling operation: {e}")
                        debug(f"Traceback: {traceback.format_exc()}")
            
            # Clear thread pool
            self.threadPool.clear()
            self.threadPool.waitForDone()
        except Exception as e:
            warn(f"Error during cleanup: {e}")
            debug(f"Traceback: {traceback.format_exc()}")
    
    def closeEvent(self, event) -> None:
        """Handle window close gracefully"""
        debug("Editor Window closing...")
        try:
            self.cleanup()
            self.mainWindow.closeEvent(event)
            event.accept()
        except Exception as e:
            warn(f"Error during window close: {e}")
            debug(f"Traceback: {traceback.format_exc()}")
            event.ignore()

    def cancel_all_operations(self) -> None:
        """Cancel all running operations"""
        debug("Cancelling all operations")
        for operation in self.mainWindow.findChildren(RunSchemeOperation):
            if operation.isRunning():
                try:
                    operation.cancel()
                except Exception as e:
                    warn(f"Error cancelling operation: {e}")
                    debug(f"Traceback: {traceback.format_exc()}")
        self.threadPool.clear()
        self.threadPool.waitForDone()

    def updateBestGuess(self, taskType: str, output: str) -> None:
        """Update best guess text from RunSchemeOperation"""
        if taskType == "simple":
            self.view.setBestGuess(output)
        elif taskType == "allTests":
            self.view.setBestGuessStatus(output, "green")

    @property
    def schemeDefinitionView(self) -> QTextEdit:
        return self.view.schemeDefinitionView

    @property
    def bestGuessView(self) -> QTextEdit:
        return self.view.bestGuessView

    @property
    def testInputs(self) -> list[QLineEdit]:
        return self.view.testInputs

    @property
    def testExpectedOutputs(self) -> list[QLineEdit]:
        return self.view.testExpectedOutputs

    @property
    def testStatusLabels(self) -> list[QLabel]:
        return self.view.testStatusLabels

    def loadInterpreterCode(self, code: str) -> None:
        """Load the interpreter code"""
        self.query_builder = QueryBuilder(code)
