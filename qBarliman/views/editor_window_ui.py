from PySide6.QtWidgets import (
    QMainWindow,
    QTextEdit,
    QLineEdit,
    QLabel,
    QGridLayout,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Signal, Qt

from qBarliman.widgets.scheme_editor_text_view import SchemeEditorTextView


class EditorWindowUI(QWidget):  # Changed from QMainWindow to QWidget
    # Signals for user interactions
    definitionTextChanged = Signal(str)
    testInputsChanged = Signal(list, list)  # (test_inputs, expected_outputs)
    testInputChanged = Signal(int, str)  # test number (1-based)
    testOutputChanged = Signal(int, str)  # test number (1-based)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buildUI()

    def setMainWindow(self, mainWindow: QMainWindow) -> None:
        """Set up this widget as the central widget of a QMainWindow"""
        if not isinstance(mainWindow, QMainWindow):
            raise TypeError("mainWindow must be a QMainWindow")
        self.setParent(mainWindow)
        mainWindow.setCentralWidget(self)

    def _buildUI(self):
        default_font = QFont("Monospace", 16)
        default_font.setStyleHint(QFont.StyleHint.Monospace)

        self.mainLayout = QVBoxLayout(self)

        # Scheme definition and best guess area in a splitter.
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

        # Status labels area.
        self.definitionStatusLabel = QLabel("", self)
        self.bestGuessStatusLabel = QLabel("", self)
        self.mainLayout.addWidget(self.definitionStatusLabel)
        self.mainLayout.addWidget(self.bestGuessStatusLabel)

        # Create grid for test inputs, expected outputs and status labels.
        self.testInputs = []
        self.testExpectedOutputs = []
        self.testStatusLabels = []
        self.testsGrid = QGridLayout()
        for i in range(6):
            self.testsGrid.addWidget(QLabel(f"Test {i+1}:"), i, 0)
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

            # Connect individual test field signals
            input_field.textChanged.connect(
                lambda text, idx=i: self.testInputChanged.emit(idx + 1, text)
            )
            expected_field.textChanged.connect(
                lambda text, idx=i: self.testOutputChanged.emit(idx + 1, text)
            )

        self.mainLayout.addLayout(self.testsGrid)

        # Connect definition text change
        self.schemeDefinitionView.textChanged.connect(
            lambda: self.definitionTextChanged.emit(
                self.schemeDefinitionView.toPlainText()
            )
        )

        # Connect overall test changes
        for inp, exp in zip(self.testInputs, self.testExpectedOutputs):
            inp.textChanged.connect(self._emitTestChange)
            exp.textChanged.connect(self._emitTestChange)

    def _emitTestChange(self):
        """Emit signal when any test input/output changes"""
        inputs = [inp.text() for inp in self.testInputs]
        expected = [exp.text() for exp in self.testExpectedOutputs]
        self.testInputsChanged.emit(inputs, expected)

    # UI update helpers
    def setBestGuess(self, text: str):
        self.bestGuessView.setPlainText(text)

    def setDefinitionStatus(self, status: str, color: str):
        self.definitionStatusLabel.setText(status)
        self.definitionStatusLabel.setStyleSheet(f"color: {color};")

    def setBestGuessStatus(self, status: str, color: str):
        self.bestGuessStatusLabel.setText(status)
        self.bestGuessStatusLabel.setStyleSheet(f"color: {color};")

    def setTestStatus(self, index: int, status: str, color: str):
        if 0 <= index < len(self.testStatusLabels):
            self.testStatusLabels[index].setText(status)
            self.testStatusLabels[index].setStyleSheet(f"color: {color};")

    def showErrorOutput(self, text: str):
        self.errorOutputView.setPlainText(text)
        self.errorOutputView.show()

    def clearErrorOutput(self):
        self.errorOutputView.clear()
        self.errorOutputView.hide()
