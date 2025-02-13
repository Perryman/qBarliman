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
    TaskStatus
)
from qBarliman.utils.query_builder import QueryBuilder
from qBarliman.views.editor_window_ui import EditorWindowUI


class EditorWindowController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.mainWindow = QMainWindow()
        self.view = EditorWindowUI(self.mainWindow)
        self.mainWindow.setCentralWidget(self.view)

        self.query_builder = QueryBuilder()
        info("Initialized EditorWindowController")

        self.execution_service = SchemeExecutionService()

        # Initialize model
        self.model = SchemeDocument(
            definition_text="\n".join(DEFAULT_DEFINITIONS),
            test_inputs=DEFAULT_TEST_INPUTS.copy(),
            test_expected=DEFAULT_TEST_EXPECTED_OUTPUTS.copy(),
        )

        # Debounce timer
        self.run_code_timer = QTimer()
        self.run_code_timer.setSingleShot(True)
        self.run_code_timer.timeout.connect(self._run_code_debounce)
        self._debounce_interval = 0.5  # seconds
        self._pending_task_types = []  # List of task types to run
        self._current_task_type = None
        self._all_tests_task_id = None

        # Set up signals and UI
        self.setup_connections()
        self.mainWindow.show()
        self.initialize_ui()
        self.run_code("simple")  # Initial run

        # Declarative UI update mappings: TaskResult -> UI Action
        self._ui_actions = {
            ("simple", TaskStatus.SUCCESS): lambda r: (
                self.view.update_ui("definition_status", (r.message, r.status)),
            ),
            ("simple", TaskStatus.SYNTAX_ERROR): lambda r: (
                self.view.update_ui("definition_status", (r.message, r.status)),
                self.maybe_kill_alltests(),
            ),
            ("simple", TaskStatus.PARSE_ERROR): lambda r: (
                self.view.update_ui("definition_status", (r.message, r.status)),
                self.maybe_kill_alltests(),
            ),
            ("simple", TaskStatus.EVALUATION_FAILED): lambda r: (
                self.view.update_ui("definition_status", (r.message, r.status)),
                 self.maybe_kill_alltests()
            ),
            ("simple", TaskStatus.FAILED): lambda r: (
                self.view.update_ui("definition_status", (r.message, r.status)),
                self.maybe_kill_alltests()
            ),
            ("allTests", TaskStatus.SUCCESS): lambda r: (
                self.view.update_ui("best_guess", r.output),
                self.view.update_ui("best_guess_status", (f"Succeeded ({r.elapsed_time:.2f} s)", r.status)),
            ),
            ("allTests", TaskStatus.FAILED): lambda r: (
                self.view.update_ui("best_guess", ""),
                self.view.update_ui("best_guess_status", (f"Failed ({r.elapsed_time:.2f} s)", r.status)),
            ),
             ("allTests", TaskStatus.SYNTAX_ERROR): lambda r:(
                self.view.update_ui("best_guess_status", (f"Failed ({r.elapsed_time:.2f} s)", r.status)),
            ),

            # Use a generic "test" prefix for individual tests
            ("test", TaskStatus.SUCCESS): lambda r: (
                self.view.update_ui("test_status", (int(r.task_type[4:]) - 1, f"Succeeded ({r.elapsed_time:.2f} s)", r.status)),
            ),
            ("test", TaskStatus.FAILED): lambda r: (
                self.view.update_ui("test_status", (int(r.task_type[4:]) - 1, f"Failed ({r.elapsed_time:.2f} s)", r.status)),
                self.maybe_kill_alltests(),
            ),
             ("test", TaskStatus.SYNTAX_ERROR): lambda r: (
                 self.view.update_ui("test_status", (int(r.task_type[4:]) - 1, r.message, r.status)),
                self.maybe_kill_alltests(),
            ),
        }

    def maybe_kill_alltests(self):
        """Helper function to avoid repetition"""
        if self._all_tests_task_id is not None:
            self.execution_service.kill_process(self._all_tests_task_id)
            self._all_tests_task_id = None

    def initialize_ui(self):
        # Initial UI setup, now uses update_ui
        self.view.update_ui("definition_text", self.model.definition_text)
        self.view.update_ui("test_cases", (self.model.test_inputs, self.model.test_expected))
        self.view.reset_test_ui()

    def update_model(self, updater):
        """Applies an updater function and runs necessary tests."""

        new_data: SchemeDocumentData = updater(self.model._data)
        if not isinstance(new_data, SchemeDocumentData):
            raise TypeError(
                "updater function must return a SchemeDocumentData instance"
            )

        old_data = self.model._data  # Store *before* update
        self.model._data = new_data  # Update the model

        # Determine which tasks to schedule.
        if new_data.definition_text != old_data.definition_text:
            self._schedule_run_code("simple")

        if (
            new_data.test_inputs != old_data.test_inputs
            or new_data.test_expected != old_data.test_expected
        ):
            self.model.testCasesChanged.emit(
                new_data.test_inputs, new_data.test_expected
            )
            # Schedule allTests if any test inputs/expected are non-empty.
            if any(new_data.test_inputs) or any(new_data.test_expected):
                self._schedule_run_code("allTests")

        # Schedule individual tests *only* if input/expected changed AND non-empty.
        for i in range(len(new_data.test_inputs)):
            if (
                i < len(old_data.test_inputs)
                and new_data.test_inputs[i] != old_data.test_inputs[i]
            ) or (
                i < len(old_data.test_expected)
                and new_data.test_expected[i] != old_data.test_expected[i]
            ):
                if (
                    new_data.test_inputs[i] and new_data.test_expected[i]
                ):  # BOTH must be non-empty
                    self._schedule_run_code(f"test{i + 1}")

    def _schedule_run_code(self, task_type):
        """Schedules a task, avoiding duplicates."""
        if task_type not in self._pending_task_types:
            self._pending_task_types.append(task_type)
        self.run_code_timer.start(int(self._debounce_interval * 1000))

    @Slot()
    def _run_code_debounce(self):
        """Executes pending tasks."""
        for task_type in self._pending_task_types:
            self.run_code(task_type)
        self._pending_task_types = []

    def run_code(self, task_type):
        """Runs the Scheme code for a given task type."""
        self.view.clear_error_output()  # Clear errors
        if task_type == "simple":
            script = self.query_builder.build_simple_query(self.model._data)
        elif task_type == "allTests":
            script = self.query_builder.build_all_tests_query(self.model._data)
            self._all_tests_task_id = None  # Reset before potentially setting.
        elif task_type.startswith("test"):
            index = int(task_type[4:]) - 1
            script = self.query_builder.build_test_query(
                self.model._data, index + 1
            )  # Adjust for 1-based indexing

        else:
            warn(f"Invalid task type: {task_type}")
            return

        if script:
            self._current_task_type = task_type
            script_path = os.path.join(TMP_DIR, f"{task_type}.scm")
            with open(script_path, "w") as f:
                f.write(script)
            task_id = self.execution_service.execute_scheme(script_path, task_type)
            if task_type == "allTests":
                self._all_tests_task_id = task_id  # Store task ID

        # No else needed.  If !script, it's handled by error callbacks.

    def setup_connections(self):
        # Model to View
        self.model.testCasesChanged.connect(
            lambda inputs, expected: self.view.update_ui("test_cases", (inputs, expected))
        )

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

        # Connect to the *unified* taskResultReady signal.
        self.execution_service.taskResultReady.connect(self._handle_task_result)
        self.execution_service.processStarted.connect(self._handle_process_started)

    @Slot(str)
    def _handle_process_started(self, task_type):
        status = TaskStatus.THINKING
        if task_type == "simple":
            self.view.update_ui("definition_status", ("???", status))
        elif task_type == "allTests":
            self.view.update_ui("best_guess_status", ("???", status))
        elif task_type.startswith("test"):
            index = int(task_type[4:]) - 1
            self.view.update_ui("test_status", (index, "???", status))


    @Slot(TaskResult)
    def _handle_task_result(self, result: TaskResult):
        """Handles the TaskResult and updates the UI."""
        debug(f"Task result received: {result}")

        # --- Get UI update action based on task type and status ---
        # First, try to get a specific action for the (task_type, status)
        action = self._ui_actions.get((result.task_type, result.status))

        # If not found, try to get a generic action for "test" prefix
        if action is None and result.task_type.startswith("test"):
            action = self._ui_actions.get(("test", result.status))

        # If still not found, do nothing
        if action is not None:
            action(result)  # Execute the UI update action
        self.view.update_ui("error_output", result.output)  # Always set error output