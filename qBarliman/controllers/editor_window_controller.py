import os

from PySide6.QtCore import QObject, QTimer, Slot
from PySide6.QtWidgets import QMainWindow

from qBarliman.constants import (
    TMP_DIR,
    debug,
    info,
    warn,
)
from qBarliman.models.scheme_document import SchemeDocument
from qBarliman.operations.scheme_execution_service import (
    SchemeExecutionService,
    TaskResult,
    TaskStatus,
)
from qBarliman.utils.load_interpreter import load_interpreter_code
from qBarliman.utils.query_builder import QueryBuilder, SchemeQueryType
from qBarliman.views.editor_window_ui import EditorWindowUI


class EditorWindowController(QObject):
    def __init__(
        self,
        parent=None,
        query_builder: QueryBuilder = None,
        execution_service: SchemeExecutionService = None,
    ):  # Inject dependencies
        super().__init__(parent)

        self.main_window = QMainWindow()
        self.main_window.controller = self  # Add controller reference
        self.view = EditorWindowUI(self.main_window)
        self.main_window.setCentralWidget(self.view)

        # Use injected QueryBuilder or create a default one if not provided
        self.query_builder = query_builder or QueryBuilder(
            load_interpreter_code()
        )  # Default + load_interpreter_code moved

        info("Initialized EditorWindowController")

        # Use injected ExecutionService or create a default one if not provided
        self.execution_service = execution_service or SchemeExecutionService()

        # Initialize model
        self.model = SchemeDocument()

        # Debounce timer
        self.run_code_timer = QTimer()
        self.run_code_timer.setSingleShot(True)
        self.run_code_timer.timeout.connect(self._run_code_debounce)
        self._debounce_interval = 0.5  # seconds
        self._pending_task_types = []  # List of task types to run
        self._current_task_type = None
        self._all_tests_task_id = None

        self._config = {
            "simple": {
                "update": ("definition_status", lambda r: (r.message, r.status)),
                "kill": {"pass": False, "fail": True},
            },
            "allTests": {
                "update": [
                    ("best_guess", lambda r: r.output),
                    (
                        "best_guess_status",
                        lambda r: (f"{r.elapsed_time:.2f}s", r.status),
                    ),
                ],
                "kill": {"pass": False, "fail": False},
            },
            "test": {
                "update": {
                    "pass": (
                        "test_status",
                        lambda r: (
                            int(r.task_type[4:]) - 1,
                            f"{r.elapsed_time:.2f}s",
                            r.status,
                        ),
                    ),
                    "fail": (
                        "test_status",
                        lambda r: (
                            int(r.task_type[4:]) - 1,
                            (
                                f"Failed {r.elapsed_time:.2f}s"
                                if r.elapsed_time is not None
                                else "Failed"
                            ),
                            r.status,
                        ),
                    ),
                },
                "kill": {"pass": False, "fail": True},
            },
        }

        # Set up signals and UI
        self.setup_connections()
        self.main_window.show()
        self.initialize_ui()
        self.run_code("simple")  # Initial run

    def maybe_kill_alltests(self):
        """Kill all_tests if it is running."""
        if self._all_tests_task_id is not None:
            self.execution_service.kill_process(self._all_tests_task_id)
            self._all_tests_task_id = None

    def initialize_ui(self):
        self.view.update_ui("definition_text", self.model.definition_text)
        self.view.update_ui(
            "test_cases", (self.model.test_inputs, self.model.test_expected)
        )
        self.view.reset_test_ui()

    def update_model(self, updater):
        """Applies an updater function to the model and schedules necessary tasks."""
        old_data = self.model._data
        updater(self.model)
        new_data = self.model._data
        # Definition text change -> simple check
        if new_data.definition_text != old_data.definition_text:
            self._schedule_run_code("simple")
            # Schedule test1-n
            for i in range(1, len(new_data.test_inputs) + 1):
                self._schedule_run_code(f"test{i}")
            # Schedule allTests
            self._schedule_run_code("allTests")

    def _test_data_changed(self, old_data, new_data):
        """Check if test inputs or expected outputs have changed."""
        return (
            new_data.test_inputs != old_data.test_inputs
            or new_data.test_expected != old_data.test_expected
        )

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
        debug(f"Running code for task type: {task_type}")
        try:
            if task_type == "simple":
                script = self.query_builder.build_query(
                    SchemeQueryType.SIMPLE, self.model._data
                )
            elif task_type == "allTests":
                script = self.query_builder.build_query(
                    SchemeQueryType.ALL_TESTS, self.model._data
                )
                self._all_tests_task_id = None  # Reset before potentially setting
            elif task_type.startswith("test"):
                index = int(task_type[4:])  # Extract test number
                script = self.query_builder.build_query(
                    SchemeQueryType.TEST, (self.model._data, index)
                )
            else:
                warn(f"Invalid task type: {task_type}")
                return

            if script:
                self._current_task_type = task_type
                script_path = os.path.join(TMP_DIR, f"{task_type}.scm")
                debug(f"Writing script to {script_path}")
                with open(script_path, "w") as f:
                    f.write(script)
                task_id = self.execution_service.execute_scheme(script_path, task_type)
                if task_type == "allTests":
                    self._all_tests_task_id = task_id

        except Exception as e:
            warn(f"Error building/running query: {e}")
            self.view.update_ui("error_output", str(e))

    def setup_connections(self):
        self.model.definitionTextChanged.connect(
            lambda text: self.view.update_ui("definition_text", text)
        )
        self.model.testCasesChanged.connect(
            lambda inputs, expected: self.view.update_ui(
                "test_cases", (inputs, expected)
            )
        )

        self.view.schemeDefinitionView.textChanged.connect(
            lambda: self.update_model(
                lambda m: m.update_definition_text(
                    self.view.schemeDefinitionView.toPlainText()
                )
            )
        )
        # Update test input/output connections to use textModified instead of textChanged
        for i, input_field in enumerate(self.view.testInputs):
            input_field.textModified.connect(
                lambda text, idx=i: self.update_model(
                    lambda m: m.update_test_input(idx + 1, text)
                )
            )
        for i, output_field in enumerate(self.view.testExpectedOutputs):
            output_field.textModified.connect(
                lambda text, idx=i: self.update_model(
                    lambda m: m.update_test_expected(idx + 1, text)
                )
            )

        self.execution_service.taskResultReady.connect(self._handle_task_result)
        self.execution_service.processStarted.connect(self._handle_process_started)

    def execute_config(self, result):
        """Execute UI updates based on task configuration."""
        task = "test" if result.task_type.startswith("test") else result.task_type
        outcome = "pass" if result.status == TaskStatus.SUCCESS else "fail"
        cfg = self._config.get(task)

        if not cfg:
            warn(f"No config for task: {result.task_type}")
            return

        upd = cfg["update"]
        if isinstance(upd, dict):
            upd = upd[outcome]
        updates = upd if isinstance(upd, list) else [upd]

        for element, formatter in updates:
            self.view.update_ui(element, formatter(result))

        if cfg["kill"][outcome]:
            self.maybe_kill_alltests()

    @Slot(str)
    def _handle_process_started(self, task_type):
        if task_type == "simple":
            self.view.update_ui("definition_status", ("???", TaskStatus.THINKING))
        elif task_type == "allTests":
            self.view.update_ui("best_guess_status", ("???", TaskStatus.THINKING))
        elif task_type.startswith("test"):
            index = int(task_type[4:]) - 1
            self.view.update_ui("test_status", (index, "???", TaskStatus.THINKING))

    @Slot(TaskResult)
    def _handle_task_result(self, result: TaskResult):
        """Handles the TaskResult and updates the UI."""
        debug(f"Task result received: {result}")
        self.execute_config(result)
