from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QGridLayout, QLabel, QSplitter, QVBoxLayout, QWidget

from services.scheme_execution_service import TaskStatus
from widgets.scheme_editor_line_edit import SchemeEditorLineEdit
from widgets.scheme_editor_text_edit import SchemeEditorTextEdit


class EditorWindowUI(QWidget):
    """Editor window UI with hierarchical component registry and path-based access."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        main_window.setWindowTitle("qBarliman")

        self.components = {
            "definition": {"view": None, "status": None},
            "best_guess": {"view": None, "status": None},
            "error_output": None,
            "tests": [],
            "layout": {"main": None, "tests": None, "splitter": None},
        }

        self.status_colors = {
            TaskStatus.SUCCESS: "green",
            TaskStatus.PARSE_ERROR: "magenta",
            TaskStatus.SYNTAX_ERROR: "orange",
            TaskStatus.EVALUATION_FAILED: "red",
            TaskStatus.THINKING: "purple",
            TaskStatus.FAILED: "red",
            TaskStatus.TERMINATED: "black",
            "IDLE": "grey",
        }

        self._setup_font()
        self._build_ui()

    def _setup_font(self):
        self.default_font = QFont("Source Code Pro", 16)
        self.default_font.setStyleHint(QFont.StyleHint.Monospace)
        self.default_font.setFixedPitch(True)
        self.default_font.setFamilies(
            ["Source Code Pro", "SF Mono", "Lucida Console", "Monaco", "Courier New"]
        )

    def _build_ui(self):
        self.setMinimumWidth(1000)
        self.setMinimumHeight(800)
        main_layout = QVBoxLayout(self)
        self.components["layout"]["main"] = main_layout

        definition_view = SchemeEditorTextEdit(self)
        definition_view.setFont(self.default_font)
        definition_view.setPlaceholderText("Enter Scheme definitions...")
        self.components["definition"]["view"] = definition_view

        best_guess_view = SchemeEditorTextEdit(self)
        best_guess_view.setReadOnly(True)
        best_guess_view.setFont(self.default_font)
        best_guess_view.setPlaceholderText("No best guess available.")
        self.components["best_guess"]["view"] = best_guess_view

        error_output_view = SchemeEditorTextEdit(self)
        error_output_view.setReadOnly(True)
        error_output_view.hide()
        self.components["error_output"] = error_output_view

        definition_status = QLabel("Ready", self)
        definition_status.setMaximumHeight(definition_status.sizeHint().height())
        best_guess_status = QLabel("Ready", self)
        best_guess_status.setMaximumHeight(best_guess_status.sizeHint().height())
        self.components["definition"]["status"] = definition_status
        self.components["best_guess"]["status"] = best_guess_status

        tests_grid = QGridLayout()
        self.components["layout"]["tests"] = tests_grid

        for i in range(6):
            test_component = {
                "input": {"view": None},
                "expected": {"view": None},
                "status": None,
                "index": i,
            }

            input_field = SchemeEditorLineEdit(self, test_num=i)
            input_field.setFont(self.default_font)
            tests_grid.addWidget(input_field, i + 1, 1)
            test_component["input"]["view"] = input_field

            output_field = SchemeEditorLineEdit(self, test_num=i)
            output_field.setFont(self.default_font)
            tests_grid.addWidget(output_field, i + 1, 2)
            test_component["expected"]["view"] = output_field

            status_label = QLabel("Idle", self)
            tests_grid.addWidget(status_label, i + 1, 3)
            test_component["status"] = status_label

            self.components["tests"].append(test_component)

        splitter = QSplitter(Qt.Orientation.Vertical, self)
        self.components["layout"]["splitter"] = splitter
        splitter.addWidget(definition_view)
        splitter.addWidget(definition_status)
        splitter.addWidget(best_guess_view)
        splitter.addWidget(best_guess_status)
        splitter.addWidget(error_output_view)

        tests_container = QWidget(self)
        self.components["layout"]["tests_container"] = tests_container
        tests_container.setLayout(tests_grid)
        splitter.addWidget(tests_container)

        main_layout.addWidget(splitter)

    def get_component(self, path):
        if isinstance(path, str):
            path = path.split(".")

        current = self.components
        for segment in path:
            try:
                if isinstance(segment, int) or segment.isdigit():
                    idx = int(segment)
                    current = current[idx]
                else:
                    current = current[segment]
            except (KeyError, IndexError, TypeError):
                return None

        return current

    def create_update_slot(self, component_path):
        component = self.get_component(component_path)

        if not component:
            return lambda *args: None

        if isinstance(component, QLabel):

            def update_status(data):
                text, status_type = data if isinstance(data, tuple) else (data, None)
                component.setText(text)
                if status_type:
                    color = self.status_colors.get(status_type.upper(), "IDLE")
                    component.setStyleSheet(f"color: {color};")

            return update_status

        elif hasattr(component, "setPlainText"):

            def update_text(text):
                if text != component.toPlainText():
                    component.setPlainText(text)
                if component == self.components["error_output"]:
                    component.setVisible(bool(text))

            return update_text

        elif hasattr(component, "setText"):

            def update_line(text):
                component.setText(text)

            return update_line

        return lambda *args: None  # Default no-op if no suitable updater found

    def _create_visibility_slot(self, component_path):
        def update_visibility(visible):
            component = self.get_component(component_path)
            if component:
                if visible:
                    component.show()
                else:
                    component.hide()

        return update_visibility

    def create_test_updater(self, test_index, component_type):
        if component_type == "status":
            path = ["tests", test_index, "status"]
        else:
            path = ["tests", test_index, component_type, "view"]
        return self.create_update_slot(path)

    def get_component_registry(self):
        registry = {
            "get_component": self.get_component,
            "create_slot": self.create_update_slot,
            "create_test_updater": self.create_test_updater,
            "get_signal": lambda path, signal_name: getattr(
                self.get_component(path), signal_name, None
            ),
            "definition_view": self.components["definition"]["view"],
            "best_guess_view": self.components["best_guess"]["view"],
            "error_output": self.components["error_output"],
            "definition_status": self.components["definition"]["status"],
            "best_guess_status": self.components["best_guess"]["status"],
            "create_visibility_slot": self._create_visibility_slot,
        }

        for i, test in enumerate(self.components["tests"]):
            registry[f"test_input_{i}"] = test["input"]["view"]
            registry[f"test_expected_{i}"] = test["expected"]["view"]
            registry[f"test_status_{i}"] = test["status"]

        return registry
