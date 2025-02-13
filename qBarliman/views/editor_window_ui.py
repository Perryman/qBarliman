from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QLineEdit,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from qBarliman.operations.scheme_execution_service import TaskStatus
from qBarliman.widgets.scheme_editor_text_view import SchemeEditorTextView


class EditorWindowUI(QWidget):
    """Main editor window UI component (declarative and reactive)."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        main_window.setWindowTitle("qBarliman")
        self._buildUI()

        # Declarative UI update map: signal_name -> (widget, update_function)
        self._widget_updaters = {
            "definition_text": (self.schemeDefinitionView, lambda w, text: w.setPlainText(text)),
            "best_guess": (self.bestGuessView, lambda w, text: w.setPlainText(text)),
            "definition_status": (self.definitionStatusLabel, self._set_labeled_text),
            "best_guess_status": (self.bestGuessStatusLabel, self._set_labeled_text),
            "error_output": (self.errorOutputView, self._set_error_text),
            "test_cases": (None, self._set_test_cases),  # Special case: no single widget
            "test_status": (None, self._set_test_status),  # Special case: indexed update
        }

        # Centralized color mapping (could also be a method)
        self.status_colors = {
            TaskStatus.SUCCESS: "green",
            TaskStatus.PARSE_ERROR: "magenta",
            TaskStatus.SYNTAX_ERROR: "orange",
            TaskStatus.EVALUATION_FAILED: "red",
            TaskStatus.THINKING: "purple",
            TaskStatus.FAILED: "red",
            TaskStatus.TERMINATED: "black",
        }

    def _buildUI(self):
        default_font = QFont("Monospace", 16)
        default_font.setStyleHint(QFont.StyleHint.Monospace)

        self.setMinimumWidth(1000)
        self.setMinimumHeight(800)
        self.mainLayout = QVBoxLayout(self)

        self.schemeDefinitionView = SchemeEditorTextView(self)
        self.schemeDefinitionView.setFont(default_font)
        self.schemeDefinitionView.setPlaceholderText("Enter Scheme definitions...")

        self.bestGuessView = SchemeEditorTextView(self)
        self.bestGuessView.setReadOnly(True)
        self.bestGuessView.setFont(default_font)
        self.bestGuessView.setPlaceholderText("No best guess available.")

        self.errorOutputView = SchemeEditorTextView(self)
        self.errorOutputView.setReadOnly(True)
        self.errorOutputView.hide()

        self.splitter = QSplitter(Qt.Orientation.Vertical, self)
        self.splitter.addWidget(self.schemeDefinitionView)
        self.splitter.addWidget(self.bestGuessView)
        self.splitter.addWidget(self.errorOutputView)
        self.mainLayout.addWidget(self.splitter)

        self.definitionStatusLabel = QLabel("", self)
        self.bestGuessStatusLabel = QLabel("", self)
        self.mainLayout.addWidget(self.definitionStatusLabel)
        self.mainLayout.addWidget(self.bestGuessStatusLabel)

        self.testInputs = []
        self.testExpectedOutputs = []
        self.testStatusLabels = []
        self.testsGrid = QGridLayout()

        for i in range(6):
            test_num = i + 1
            self.testsGrid.addWidget(QLabel(f"Test {test_num}:"), i, 0)
            input_field = QLineEdit(self)
            input_field.setFont(default_font)
            self.testInputs.append(input_field)
            self.testsGrid.addWidget(input_field, i, 1)
            expected_field = QLineEdit(self)
            expected_field.setFont(default_font)
            self.testExpectedOutputs.append(expected_field)
            self.testsGrid.addWidget(expected_field, i, 2)
            status_label = QLabel("", self)
            self.testStatusLabels.append(status_label)
            self.testsGrid.addWidget(status_label, i, 3)
        self.mainLayout.addLayout(self.testsGrid)

    def update_ui(self, update_type, data):
        """
        Declarative UI update method.

        Args:
            update_type (str):  The type of update (e.g., "definition_text", "test_status").
            data: The data associated with the update (can be different types).
        """
        updater = self._widget_updaters.get(update_type)
        if updater:
            widget, update_func = updater
            if widget:
                update_func(widget, data) #call the widget
            else:
                update_func(data) #directly call function

    def set_definition_text(self, text: str):
        self.schemeDefinitionView.setPlainText(text)

    def set_best_guess(self, text: str):
        self.bestGuessView.setPlainText(text)

    def set_definition_status(self, text: str, color: str):
        self.definitionStatusLabel.setText(text)
        self.definitionStatusLabel.setStyleSheet(f"color: {color};")

    def set_best_guess_status(self, text: str, color: str):
        self.bestGuessStatusLabel.setText(text)
        self.bestGuessStatusLabel.setStyleSheet(f"color: {color};")

    def set_error_output(self, text: str):
        if text:
            self.errorOutputView.setPlainText(text)
            self.errorOutputView.show()  # Show the view
        else:
            self.errorOutputView.clear()
            self.errorOutputView.hide()  # Hide the view

    def set_test_cases(self, inputs: list[str], expected: list[str]):
        for i, (inp, exp) in enumerate(zip(inputs, expected)):
            if i < len(self.testInputs):
                self.testInputs[i].setText(inp)
            if i < len(self.testExpectedOutputs):
                self.testExpectedOutputs[i].setText(exp)

    def set_test_status(self, index: int, status: str, color: str):
        if 0 <= index < len(self.testStatusLabels):
            label = self.testStatusLabels[index]
            label.setText(status)
            label.setStyleSheet(f"color: {color};")

    def _set_labeled_text(self, label: QLabel, data: tuple[str, TaskStatus]):
        """Helper to set text and color on a label."""
        text, status = data  # Receive status, not color
        color = self.status_colors.get(status, "black")  # Look up color
        label.setText(text)
        label.setStyleSheet(f"color: {color};")

    def _set_error_text(self, view: QTextEdit, text: str):
        """Helper to set the error text and show/hide the view."""
        if text:
            view.setPlainText(text)
            view.show()
        else:
            view.clear()
            view.hide()

    def _set_test_cases(self, data: tuple[list[str], list[str]]):
        """Update all test input and expected output fields."""
        inputs, expected = data
        for i, (inp, exp) in enumerate(zip(inputs, expected)):
            if i < len(self.testInputs):
                self.testInputs[i].setText(inp)
            if i < len(self.testExpectedOutputs):
                self.testExpectedOutputs[i].setText(exp)

    def _set_test_status(self, data: tuple[int, str, TaskStatus]):
        """Helper to set text and color on a test status label."""
        index, status_text, status = data
        color = self.status_colors.get(status, "black")

        if 0 <= index < len(self.testStatusLabels):
            label = self.testStatusLabels[index]
            label.setText(status_text)
            label.setStyleSheet(f"color: {color};")

    def reset_test_ui(self):
        """Resets the test UI elements to their default state."""
        for i in range(len(self.testInputs)):
            self._set_test_status((i, "", TaskStatus.SUCCESS))

    def clear_error_output(self):
        """Clears the error output text edit."""
        self.errorOutputView.clear()
        self.errorOutputView.hide()
