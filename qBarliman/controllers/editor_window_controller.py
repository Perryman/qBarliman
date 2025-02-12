import os

from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QMainWindow

from qBarliman.constants import (
    DEFAULT_DEFINITIONS,
    DEFAULT_TEST_EXPECTED_OUTPUTS,
    DEFAULT_TEST_INPUTS,
    TMP_DIR,
    info,
    warn,
)
from qBarliman.models.scheme_document import SchemeDocument
from qBarliman.models.scheme_document_data import SchemeDocumentData
from qBarliman.operations.scheme_execution_service import (
    SchemeExecutionService,
)
from qBarliman.utils.load_interpreter import load_interpreter_code
from qBarliman.utils.query_builder import QueryBuilder
from qBarliman.views.editor_window_ui import EditorWindowUI


class EditorWindowController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.mainWindow = QMainWindow()
        self.view = EditorWindowUI()
        self.mainWindow.setCentralWidget(self.view)

        self.interpreter_code = load_interpreter_code()
        if self.interpreter_code:
            self.query_builder = QueryBuilder(self.interpreter_code)
            info("Initialized EditorWindowController")
        else:
            warn("Interpreter code not loaded")
            raise RuntimeError("Interpreter load failed")

        self.execution_service = SchemeExecutionService()
        # Initialize the model *after* setting up connections, and using default parameters
        self.model = SchemeDocument(
            definition_text="\n".join(DEFAULT_DEFINITIONS),
            test_inputs=DEFAULT_TEST_INPUTS.copy(),
            test_expected=DEFAULT_TEST_EXPECTED_OUTPUTS.copy(),
        )
        self.setup_connections()
        self.initialize_ui()  # Added
        self.mainWindow.show()

    def initialize_ui(self):
        # Trigger initial UI update.
        self.view.update_ui("definition_text", self.model.definition_text)
        self.view.update_ui(
            "test_cases", (self.model.test_inputs, self.model.test_expected)
        )

    def update_model(self, updater):
        """Applies an updater function to a *copy* of the model's data."""
        new_data: SchemeDocumentData = updater(self.model._data)
        if isinstance(new_data, SchemeDocumentData):
            self.model._data = new_data  # Update the model's internal data
            # Now, instead of calling runCodeFromEditPane, we emit the signals.
            if new_data.definition_text != self.model.definition_text:
                self.model.definitionTextChanged.emit(new_data.definition_text)
            if (
                new_data.test_inputs != self.model.test_inputs
                or new_data.test_expected != self.model.test_expected
            ):
                self.model.testCasesChanged.emit(
                    new_data.test_inputs, new_data.test_expected
                )
        else:
            raise TypeError(
                "updater function must return a SchemeDocumentData instance"
            )

    def run_code(self, task_type: str):
        """Runs the Scheme code based on the current model."""
        if self.model.validate():
            # Use the query builder to generate the script.
            if task_type == "simple":
                script = self.query_builder.build_simple_query(self.model._data)
            elif task_type == "allTests":
                script = self.query_builder.build_all_tests_query(self.model._data)
            # ... other task types ...
            else:
                return  # Or raise an exception

            # Create a temporary file for the script.
            script_path = os.path.join(TMP_DIR, f"temp_script_{task_type}.scm")
            with open(script_path, "w") as f:
                f.write(script)

            self.execution_service.execute_scheme(script_path, task_type)

    def setup_connections(self):
        # --- Connect Model Signals to View Slots ---
        self.model.definitionTextChanged.connect(
            lambda text: self.view.update_ui("definition_text", text)
        )
        self.model.testCasesChanged.connect(
            lambda inputs, expected: self.view.update_ui(
                "test_cases", (inputs, expected)
            )
        )
        # self.model.statusChanged.connect(...) # Connect if you have status updates

        # --- Connect View Signals to Controller (Model Updates) ---
        self.view.schemeDefinitionView.textChanged.connect(
            lambda: self.update_model(
                lambda m: m.update_definition_text(
                    self.view.schemeDefinitionView.toPlainText()
                )
            )
        )
        for i, input_field in enumerate(self.view.testInputs):
            input_field.textChanged.connect(
                lambda text, idx=i: self.update_model(
                    lambda m: m.update_test_input(idx, text)
                )
            )
        for i, output_field in enumerate(self.view.testExpectedOutputs):
            output_field.textChanged.connect(
                lambda text, idx=i: self.update_model(
                    lambda m: m.update_test_expected(idx, text)
                )
            )

        # --- Connect Execution Service Signals ---
        self.execution_service.processStarted.connect(
            lambda task_type: info(f"Process started: {task_type}")
        )  # Simple example
        self.execution_service.processOutput.connect(self._handle_process_output)
        self.execution_service.processFinished.connect(self._handle_process_finished)
        self.execution_service.processError.connect(
            lambda task_type, error: self.view.update_ui("error_output", error)
        )

    @Slot(str, str, str)
    def _handle_process_output(self, task_type: str, stdout: str, stderr: str):
        if stderr:
            self.view.update_ui("error_output", stderr)
        if stdout:
            result = self.execution_service._process_output(stdout, task_type)
            if task_type == "simple":
                self.view.update_ui(
                    "definition_status",
                    (
                        result.message,
                        self.execution_service.colors.get(
                            result.status.name.lower(),
                            self.execution_service.colors["default"],
                        ).name(),
                    ),
                )
            elif task_type == "allTests":
                self.view.update_ui("best_guess", result.output)
                self.view.update_ui(
                    "best_guess_status",
                    (
                        result.message,
                        self.execution_service.colors.get(
                            result.status.name.lower(),
                            self.execution_service.colors["default"],
                        ).name(),
                    ),
                )

            elif task_type.startswith("test"):
                try:
                    index = int(task_type[4:]) - 1  # Extract and convert to 0-indexed
                    if 0 <= index < len(self.view.testStatusLabels):
                        self.view.update_ui(
                            "test_status",
                            (
                                index,
                                result.message,
                                self.execution_service.colors.get(
                                    result.status.name.lower(),
                                    self.execution_service.colors["default"],
                                ).name(),
                            ),
                        )
                except ValueError:
                    warn(f"Invalid test index: {task_type[4:]}")

    @Slot(str, int)
    def _handle_process_finished(self, task_type: str, exit_code: int):
        if exit_code != 0:
            self.view.update_ui(
                "error_output", f"Process for {task_type} exited with code {exit_code}"
            )
        else:
            # If we're not already handling the output elsewhere, process it here
            if task_type not in ["simple", "allTests"] and not task_type.startswith(
                "test"
            ):
                result = self.execution_service._process_output("", task_type)
                self.view.update_ui(
                    f"{task_type}_status", (result.message, result.status.name.lower())
                )

        # Notify that the process has completed
        self.view.update_ui("process_status", f"{task_type} completed")
