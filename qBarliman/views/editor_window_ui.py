from PySide6.QtCore import Qt, Slot
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

from qBarliman.constants import debug, warn
from qBarliman.widgets.scheme_editor_text_view import SchemeEditorTextView


class EditorWindowUI(QWidget):
    """Main editor window UI component (declarative and reactive)."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        main_window.setWindowTitle("qBarliman")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self._buildUI()
        self._widget_map = {  # Key: signal name, Value: (widget, setter_method)
            "definition_text": (
                self.schemeDefinitionView,
                lambda widget, text: widget.setPlainText(text),
            ),
            "best_guess": (self.bestGuessView, self.bestGuessView.setPlainText),
            "definition_status": (self.definitionStatusLabel, self._set_labeled_text),
            "best_guess_status": (self.bestGuessStatusLabel, self._set_labeled_text),
            "error_output": (self.errorOutputView, self._set_error_text),
        }

    def _buildUI(self):
        default_font = QFont("Monospace", 16)
        default_font.setStyleHint(QFont.StyleHint.Monospace)

        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
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

    @Slot(str, object)
    def update_ui(self, signal_name: str, data: object):
        """Generic UI update slot."""
        if signal_name in self._widget_map:
            widget, setter = self._widget_map[signal_name]
            setter(widget, data)
        elif signal_name == "test_cases":
            self._set_test_cases(data)
        elif signal_name == "test_status":
            index, message, color = data
            self._set_test_status(index, message, color)  # Use the new method
        elif signal_name == "debug":
            debug(f"{signal_name=}")
            debug(f"{data=}")
        else:
            warn(f"Warning: Unhandled signal '{signal_name}'")

    def _set_labeled_text(self, label: QLabel, data: tuple[str, str]):
        """Helper to set text and color on a label."""
        text, color = data
        label.setText(text)
        label.setStyleSheet(f"color: {color};")

    def _set_error_text(self, view: QTextEdit, data: str):
        if data:
            # Append the new error message with a newline.
            view.append(data)
            view.show()
        else:
            view.clear()
            view.hide()

    @Slot(list, list)
    def _set_test_cases(self, data: tuple[list[str], list[str]]):
        """Update all test input and expected output fields."""
        inputs, expected = data
        for i, (inp, exp) in enumerate(zip(inputs, expected)):
            if i < len(self.testInputs):
                self.testInputs[i].setText(inp)
            if i < len(self.testExpectedOutputs):
                self.testExpectedOutputs[i].setText(exp)

    def _set_test_status(self, index: int, status: str, color: str):
        """Helper to set text and color on a test status label."""
        if 0 <= index < len(self.testStatusLabels):
            label = self.testStatusLabels[index]
            label.setText(status)
            label.setStyleSheet(f"color: {color};")
