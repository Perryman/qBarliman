import os

from PySide6.QtCore import QObject, QTimer, Slot
from PySide6.QtWidgets import QMainWindow

import qBarliman.utils.log as l
from qBarliman.constants import TMP_DIR
from qBarliman.models.scheme_document import SchemeDocument
from qBarliman.operations.scheme_execution_service import (
    SchemeExecutionService,
    TaskStatus,
)
from qBarliman.utils.load_interpreter import load_interpreter_code
from qBarliman.utils.query_builder import QueryBuilder, SchemeQueryType
from qBarliman.utils.rainbowp import rainbowp
from qBarliman.views.editor_window_ui import EditorWindowUI


class EditorWindowController(QObject):
    def __init__(
        self,
        parent=None,
        query_builder: QueryBuilder = None,
        execution_service: SchemeExecutionService = None,
    ):
        super().__init__(parent)

        self.main_window = QMainWindow()
        self.main_window.controller = self
        self.view = EditorWindowUI(self.main_window)
        self.main_window.setCentralWidget(self.view)

        self.query_builder = query_builder or QueryBuilder(load_interpreter_code())
        self.execution_service = execution_service or SchemeExecutionService()
        self.model = SchemeDocument()

        # Debounce timer
        self.run_code_timer = QTimer()
        self.run_code_timer.setSingleShot(True)
        self.run_code_timer.timeout.connect(self._run_code_debounce)
        self._debounce_interval = 0.5  # seconds

        self._pending_task_types = []  # List of task types to run
        self._current_task_type = None
        self._task_queue = []  # List of task pids

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

        self.model.definitionTextChanged.emit(self.model.definition_text)
        self.model.testCasesChanged.emit(
            self.model.test_inputs, self.model.test_expected
        )
        self.main_window.show()
        self.run_code("simple")  # Initial run

    def maybe_kill_alltests(self):
        """Kill all_tests if it is running."""
        while self._task_queue:
            l.info(f"Killing task ID: {self._task_queue[0]}")
            self.execution_service.kill_process(self._task_queue[0])
            self._task_queue.pop(0)

    @Slot()
    def _on_definition_text_changed(self):
        """Handles definition text changes and schedules tests."""
        l.info("Definition text changed")
        self.run_barliman()

    @Slot()
    def _on_tests_changed(self):
        """Handles test case changes and schedules tests."""
        l.info("Test cases changed")
        self.run_barliman()

    def _schedule_run_code(self, task_type):
        """Schedules a task, avoiding duplicates."""
        l.info(f"Scheduling task: {task_type}")
        if task_type not in self._pending_task_types:
            l.info(f"Task {task_type} not already scheduled")
            self._pending_task_types.append(task_type)
        self.run_code_timer.start(int(self._debounce_interval * 1000))

    @Slot()
    def _run_code_debounce(self):
        """Executes pending tasks."""
        l.info("Running code after debounce")
        for task_type in self._pending_task_types:
            l.info(f"Running task: {task_type}")
            self.run_code(task_type)
        self._pending_task_types = []

    def _execute_scheme_script(self, task_type, script):
        self._current_task_type = task_type
        script_path = os.path.join(TMP_DIR, f"{task_type}.scm")
        l.info(f"Writing script to {script_path}")
        with open(script_path, "w") as f:
            f.write(script)
        task_id = self.execution_service.execute_scheme(script_path, task_type)
        l.info(f"Spawned task_id pid {task_id}")
        self._task_queue.append(task_id)
        l.info(f"Task queue: {self._task_queue}")

    def run_barliman(self):
        """Queues simple, test1-n if not empty, and allTests for parallel execution."""
        self.maybe_kill_alltests()
        self.view.clear_error_output()
        l.good("Running Barliman")

        self._schedule_run_code("simple")

        test_inputs = [str(i) for i in self.model.test_inputs]
        test_expected = [str(o) for o in self.model.test_expected]

        for e, (i, o) in enumerate(zip(test_inputs, test_expected), start=1):
            if i.strip() and o.strip():
                l.info(f"Queuing test {e=}: {i=} {o=}")
                self._schedule_run_code(f"test{e}")

        self._schedule_run_code("allTests")

    def run_code(self, task_type):
        """Runs the Scheme code for a given task type."""
        self.view.clear_error_output()
        l.info(f"Running code for task type: {task_type}")
        try:
            if task_type == "simple":
                script = self.query_builder.build_query(
                    SchemeQueryType.SIMPLE, self.model._data
                )
            elif task_type.startswith("test"):
                index = int(task_type[4:])  # Extract test number
                script = self.query_builder.build_query(
                    SchemeQueryType.TEST, (self.model._data, index)
                )
            elif task_type == "allTests":
                script = self.query_builder.build_query(
                    SchemeQueryType.ALL_TESTS, self.model._data
                )
            else:
                l.warn(f"Invalid task type: {task_type}")
                return

            if script:
                l.good(f"Executing script for {task_type}")
                l.scheme(rainbowp(script))
                self._execute_scheme_script(task_type, script)
        except Exception as e:
            l.warn(f"Error building/running query: {e}")
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

        self.view.schemeDefinitionView.codeTextChanged.connect(
            self.model.update_definition_text
        )

        for i, input_field in enumerate(self.view.testInputs):
            input_field.textModified.connect(
                lambda text, idx=i: self.model.update_test_input(idx + 1, text)
            )
        for i, output_field in enumerate(self.view.testExpectedOutputs):
            output_field.textModified.connect(
                lambda text, idx=i: self.model.update_test_expected(idx + 1, text)
            )

        self.model.definitionTextChanged.connect(self._on_definition_text_changed)
        self.model.testCasesChanged.connect(self._on_tests_changed)

        self.execution_service.taskResultReady.connect(self._handle_task_result)
        self.execution_service.processStarted.connect(self._handle_process_started)

    def _handle_task_result(self, result):
        """Handles the TaskResult using config dictionary."""
        task = "test" if result.task_type.startswith("test") else result.task_type
        outcome = "pass" if result.status == TaskStatus.SUCCESS else "fail"
        cfg = self._config.get(task)

        if not cfg:
            l.warn(f"No config for task: {result.task_type}")
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
