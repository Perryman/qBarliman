import os

from PySide6.QtCore import QObject, QTimer, Slot
from PySide6.QtWidgets import QMainWindow

from qBarliman.constants import (
    DEFAULT_DEFINITIONS,
    DEFAULT_TEST_EXPECTED_OUTPUTS,
    DEFAULT_TEST_INPUTS,
    TMP_DIR,
    debug,
    info,
    warn,
)
from qBarliman.models.scheme_document import SchemeDocument
from qBarliman.models.scheme_document_data import SchemeDocumentData
from qBarliman.operations.scheme_execution_service import (
    SchemeExecutionService,
    TaskResult,
)  # Import TaskResult
from qBarliman.utils.load_interpreter import load_interpreter_code
from qBarliman.utils.query_builder import QueryBuilder
from qBarliman.views.editor_window_ui import EditorWindowUI


class EditorWindowController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.mainWindow = QMainWindow()
        self.view = EditorWindowUI(self.mainWindow)
        self.mainWindow.setCentralWidget(self.view)

        self.interpreter_code = load_interpreter_code()
        if self.interpreter_code:
            self.query_builder = QueryBuilder(self.interpreter_code)
            info("Initialized EditorWindowController")
        else:
            warn("Interpreter code not loaded")
            raise RuntimeError("Interpreter load failed")

        self.execution_service = SchemeExecutionService()

        # Initialize model *before* connections, but *after* other setup.
        self.model = SchemeDocument(
            definition_text="\n".join(DEFAULT_DEFINITIONS),
            test_inputs=DEFAULT_TEST_INPUTS.copy(),
            test_expected=DEFAULT_TEST_EXPECTED_OUTPUTS.copy(),
        )

        # Then setup connections after model exists
        self.setup_connections()
        self.mainWindow.show()
        self.run_code()
        # Define the output handling rules *declaratively*.
        self._output_handlers = {
            "simple": [
                (
                    "definition_status",
                    lambda r: (
                        r.message,
                        self._get_status_color(r.status.name),
                    ),
                ),
            ],
            "allTests": [
                ("best_guess", lambda r: r.output),
                (
                    "best_guess_status",
                    lambda r: (
                        r.message,
                        self._get_status_color(r.status.name),
                    ),
                ),
            ],
            "test": [  # Prefix match
                ("test_status", self._get_test_status_update),
            ],
            "__default__": [],  # Default: do nothing
        }
        # Debounce timer
        self.run_code_timer = QTimer()
        self.run_code_timer.setSingleShot(True)
        self.run_code_timer.timeout.connect(self._run_code_debounce)  # type: ignore
        self._debounce_interval = 0.5  # seconds
        self._pending_task_type = None
        self._current_task_type = None

    def _get_status_color(self, status_name: str) -> str:
        """Get color name for a given status."""
        return self.execution_service.colors.get(
            status_name.lower(), self.execution_service.colors["default"]
        ).name()

    def _get_test_status_update(self, result):
        try:
            index = int(
                self._current_task_type[4:]
            ) - 1  # Extract index and ensure it's 0-indexed
            if 0 <= index < len(self.view.testStatusLabels):
                return (  # Return only index, message and color
                    index,
                    result.message,
                    self._get_status_color(result.status.name),
                )
        except (ValueError, TypeError, AttributeError):
            return None

    def update_model(self, updater):
        """Applies an updater function and runs necessary tests."""
        new_data: SchemeDocumentData = updater(self.model._data)
        if not isinstance(new_data, SchemeDocumentData):
            raise TypeError(
                "updater function must return a SchemeDocumentData instance"
            )

        old_data = self.model._data  # Store *before* update
        self.model._data = new_data  # Update the model

        # Emit signals based on what changed.
        if new_data.definition_text != old_data.definition_text:
            self.model.definitionTextChanged.emit(new_data.definition_text)
            self._schedule_run_code()  # Run simple or allTests

        if (
            new_data.test_inputs != old_data.test_inputs
            or new_data.test_expected != old_data.test_expected
        ):
            self.model.testCasesChanged.emit(
                new_data.test_inputs, new_data.test_expected
            )
            # Find *which* test changed, and run *only* that test.
            for i in range(len(new_data.test_inputs)):
                if (
                    i < len(old_data.test_inputs)
                    and new_data.test_inputs[i] != old_data.test_inputs[i]
                ) or (
                    i < len(old_data.test_expected)
                    and new_data.test_expected[i] != old_data.test_expected[i]
                ):
                    self._schedule_run_code(task_type=f"test{i + 1}")
                    break  # Only run one test at a time

    def _schedule_run_code(self, task_type=None):
        """Schedules run_code to be called after a debounce interval."""
        # If no task_type is specified, determine based on model.
        if task_type is None:
            if any(self.model.test_inputs) or any(self.model.test_expected):
                task_type = "allTests"
            else:
                task_type = "simple"
        self._pending_task_type = task_type
        self.run_code_timer.start(int(self._debounce_interval * 1000))  # Convert to ms

    @Slot()
    def _run_code_debounce(self):
        """Executes run_code with the pending task type (if any)."""
        self.run_code(self._pending_task_type)
        self._pending_task_type = None

    def run_code(self, task_type=None):
        """Runs the Scheme code based on the current model."""
        # Clear error output at the start of each run
        self.view.update_ui("error_output", "")

        if self.model.validate():
            # Determine which query to run
            if task_type is None:  # If not already determined
                if any(self.model.test_inputs) or any(self.model.test_expected):
                    task_type = "allTests"
                    script = self.query_builder.build_all_tests_query(self.model._data)
                else:
                    task_type = "simple"
                    script = self.query_builder.build_simple_query(self.model._data)
            elif task_type.startswith("test"):
                script = self.query_builder.build_test_query(
                    self.model._data, int(task_type[4:])
                )
            else:  # Added error handling for invalid task_type
                warn(f"Invalid task type: {task_type}")
                return

            self._current_task_type = task_type

            # Create temporary file
            script_path = os.path.join(TMP_DIR, f"{task_type}.scm")
            with open(script_path, "w") as f:
                f.write(script)

            self.execution_service.execute_scheme(script_path, task_type)

    def setup_connections(self):
        # Model to View
        self.model.definitionTextChanged.connect(
            lambda text: self.view.update_ui("definition_text", text)
        )
        self.model.testCasesChanged.connect(
            lambda inputs, expected: self.view.update_ui(
                "test_cases", (inputs, expected)
            )
        )
        self.model.statusChanged.connect(
            lambda status: self.view.update_ui("status", status)
        )  # Not used, but good to have

        # View to Controller (Model Updates)
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

        # Execution Service Signals
        self.execution_service.processStarted.connect(
            lambda task_type: info(f"Process started: {task_type}")
        )
        self.execution_service.processOutput.connect(
            self._handle_process_output
        )  # Handle output AND errors
        self.execution_service.processError.connect(
            lambda task_type, error: self.view.update_ui("error_output", error)
        )  # We just update the UI, since we don't need to do anything else.

    @Slot(str, str, str)
    def _handle_process_output(self, task_type: str, stdout: str, stderr: str):
        """Handles process output, including errors, using a declarative approach."""
        debug(f"Process output: {task_type=}, {stdout=}, {stderr=}")

        if stderr:
            self.view.update_ui("error_output", stderr)
            return  # If we have an error, stop processing

        result = self.execution_service._process_output(stdout, task_type)
        info(f"{result=}")
        self._current_task_type = (
            task_type  # We store this to use it in _get_test_status_update
        )
        # Find and apply UI update handlers, same declarative logic as before.
        handlers = self._output_handlers.get(
            task_type, self._output_handlers["__default__"]
        )
        # Special handling for test cases, in order to update test UI properly
        if task_type.startswith("test") and handlers == self._output_handlers["__default__"]:
                handlers = self._output_handlers.get("test")

        for signal_name, handler_func in handlers:
            update_data = handler_func(result)
            if update_data is not None:
                if signal_name == "test_status":
                    index, message, color = update_data
                    self.view.update_ui(signal_name, (index, message, color))
                else:
                    self.view.update_ui(signal_name, update_data)