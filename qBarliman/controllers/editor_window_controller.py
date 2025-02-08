import os
import traceback

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QTextEdit,
    QLineEdit,
    QLabel,
    QVBoxLayout,
    QGridLayout,
    QSplitter,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy,
    QPushButton,
)
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtCore import (
    QTimer,
    Qt,
    QThread,
    Signal,
    QThreadPool,
    QRunnable,
    Slot,
    QProcess,
)
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl

from qBarliman.operations.run_scheme_operation import RunSchemeOperation
from qBarliman.widgets.scheme_editor_text_view import SchemeEditorTextView
from qBarliman.utils.constrained_splitter import ConstrainedSplitter
from qBarliman.constants import *  # warn, good, info, logging fns from here
from qBarliman.templates import *
from qBarliman.utils.rainbowp import rainbowp


class RunSchemeWorker(QRunnable):
    def __init__(self, operation):
        super().__init__()
        self.operation = operation

    @Slot()
    def run(self):
        self.operation.start()


class EditorWindowController(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initialization_complete = False
        self.setWindowTitle("qBarliman")
        self.setupUI()
        self.runCodeTimer = QTimer()
        self.runCodeTimer.setParent(self)
        self.runCodeTimer.setSingleShot(True)
        self.runCodeTimer.timeout.connect(self.executeRunCodeTimer)
        self.interpreter_code = EVAL_STRING_PART_1 + EVAL_STRING_PART_2
        self.threadPool = QThreadPool()
        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.timeout.connect(self.cleanup)
        self.initialization_complete = True
        self.scheme_operations = []
        self.processes = []
        self.processingQueue = []

    def closeEvent(self, event):
        """Clean up threads before closing, but don't wait for them to finish."""
        self.cleanup()
        event.accept()

    def setupUI(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        default_font = QFont("Monospace", 16)
        default_font.setStyleHint(QFont.StyleHint.Monospace)

        self.schemeDefinitionView = SchemeEditorTextView(central)
        self.schemeDefinitionView.setPlaceholderText("Enter Scheme definitions...")
        self.schemeDefinitionView.setFont(default_font)
        self.schemeDefinitionView.setText("\n".join(DEFAULT_DEFINITIONS))
        self.schemeDefinitionView.setAcceptRichText(False)
        self.schemeDefinitionView.textChanged.connect(
            self.setupRunCodeFromEditPaneTimer
        )
        self.bestGuessView = QTextEdit(self)
        self.bestGuessView.setReadOnly(True)
        self.bestGuessView.setFont(default_font)
        self.bestGuessView.setPlaceholderText("No best guess available.")
        self.errorOutputView = QTextEdit(self)
        self.errorOutputView.setReadOnly(True)
        self.errorOutputView.hide()

        self.definitionAndBestGuessSplitView = ConstrainedSplitter(
            Qt.Orientation.Vertical, self, min_sizes=[100, 100], max_sizes=[500, 500]
        )
        self.definitionAndBestGuessSplitView.addWidget(self.schemeDefinitionView)
        self.definitionAndBestGuessSplitView.addWidget(self.bestGuessView)
        self.definitionAndBestGuessSplitView.addWidget(self.errorOutputView)
        layout.addWidget(self.definitionAndBestGuessSplitView)

        self.schemeDefinitionTimer = QTimer(self)
        self.bestGuessTimer = QTimer(self)

        timer_layout = QHBoxLayout()
        timer_layout.addStretch()
        layout.addLayout(timer_layout)

        # --- Status Labels ---
        self.definitionStatusLabel = QLabel("", self)
        self.definitionStatusLabel.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        layout.addWidget(self.definitionStatusLabel)

        self.bestGuessStatusLabel = QLabel("", self)
        self.bestGuessStatusLabel.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        layout.addWidget(self.bestGuessStatusLabel)

        self.testInputs = []
        self.testExpectedOutputs = []
        self.testStatusLabels = []
        self.testTimers = []
        grid = QGridLayout()
        for i in range(6):
            grid.addWidget(QLabel(f"Test {i+1}:"), i, 0)
            input_field = QLineEdit(self)
            input_field.setFont(default_font)
            input_field.textChanged.connect(self.setupRunCodeFromEditPaneTimer)
            self.testInputs.append(input_field)
            grid.addWidget(input_field, i, 1)

            expected_output = QLineEdit(self)
            expected_output.setFont(default_font)
            expected_output.textChanged.connect(self.setupRunCodeFromEditPaneTimer)
            self.testExpectedOutputs.append(expected_output)
            grid.addWidget(expected_output, i, 2)

            status_label = QLabel("", self)
            status_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
                | Qt.TextInteractionFlag.TextSelectableByKeyboard
            )
            self.testStatusLabels.append(status_label)
            grid.addWidget(status_label, i, 3)

            timer = QTimer(self)
            self.testTimers.append(timer)
            # Replace the empty QWidget with a container widget that uses a right-aligned layout:
            container = QWidget(self)
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            # container_layout.addStretch()  # Pushes any future widget to the right
            timer_button = QPushButton("Timeout", self)
            timer_button.setEnabled(False)
            container_layout.addWidget(timer_button)
            container_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
            grid.addWidget(container, i, 4)
        layout.addLayout(grid)

        default_test_inputs = DEFAULT_TEST_INPUTS
        default_test_expected = DEFAULT_TEST_EXPECTED_OUTPUTS
        for i in range(6):
            self.testInputs[i].setText(default_test_inputs[i])
            self.testExpectedOutputs[i].setText(default_test_expected[i])

        for timer in self.testTimers:
            timer.setSingleShot(True)
            timer.timeout.connect(self.handleTestTimeout)

    def setupRunCodeFromEditPaneTimer(self):
        if self.initialization_complete:
            self.runCodeTimer.stop()
            for op in self.scheme_operations:  # Cancel existing operations
                op.cancel()
            self.scheme_operations = []  # Clear the list
            self.runCodeTimer.start(1000)

    def runCodeFromEditPane(self):
        fn = "runCodeFromEditPane"
        info(self.__class__.__name__)
        info("Running code from edit pane...")
        info(f"{fn}: Temporary directory at {TMP_DIR}")
        info(f"{fn}: mk_vicare_path: {MK_VICARE}")
        info(f"{fn}: mk_path: {MK}")

        interp_string = self.interpreter_code

        query_simple = self.makeQuerySimpleForMondoSchemeFileString(interp_string)
        query_alltests = self.makeAllTestsQueryString()
        info(f"{fn}: Query strings generated")

        # Write temporary files
        with open(os.path.join(TMP_DIR, BARLIMAN_QUERY_SIMPLE_SCM), "w") as f:
            f.write(query_simple)
            info(f"{fn}: Written {BARLIMAN_QUERY_SIMPLE_SCM}")
        with open(os.path.join(TMP_DIR, BARLIMAN_QUERY_ALLTESTS_SCM), "w") as f:
            f.write(query_alltests)
            info(f"{fn}: Written {BARLIMAN_QUERY_ALLTESTS_SCM}")

        runSchemeOpSimple = RunSchemeOperation(
            self, os.path.join(TMP_DIR, BARLIMAN_QUERY_SIMPLE_SCM), "simple"
        )
        runSchemeOpAllTests = RunSchemeOperation(
            self, os.path.join(TMP_DIR, BARLIMAN_QUERY_ALLTESTS_SCM), "allTests"
        )
        info(f"{fn}: Created RunSchemeOperation instances")

        # Connect signals
        runSchemeOpSimple.finishedSignal.connect(self.handleOperationFinished)
        runSchemeOpSimple.statusUpdateSignal.connect(self.handleStatusUpdate)
        runSchemeOpSimple.timerUpdateSignal.connect(self.handleTimerUpdate)

        runSchemeOpAllTests.finishedSignal.connect(self.handleOperationFinished)
        runSchemeOpAllTests.statusUpdateSignal.connect(self.handleStatusUpdate)
        runSchemeOpAllTests.timerUpdateSignal.connect(self.handleTimerUpdate)

        # Add operations to thread pool
        self.threadPool.start(RunSchemeWorker(runSchemeOpSimple))
        self.threadPool.start(RunSchemeWorker(runSchemeOpAllTests))

        # Store RunSchemeOperation objects
        self.scheme_operations = [runSchemeOpSimple, runSchemeOpAllTests]
        self.processingQueue.extend(
            self.scheme_operations
        )  # Add operations to processingQueue

        info(f"{fn}: Starting operations")

        self.startTimer(self.schemeDefinitionTimer)
        self.startTimer(self.bestGuessTimer)
        for timer in self.testTimers:
            self.startTimer(timer)

    def cleanup(self):
        info("cleaning up!")
        self.runCodeTimer.stop()

        for op in self.processingQueue:
            if hasattr(op, "cancel"):
                op.cancel()

        for op in self.processingQueue:
            if hasattr(op, "wait"):
                op.wait()

        info(f"Operation count after cleanup: {len(self.processingQueue)}")
        if self.processingQueue:
            warn("$$$$  Oh noes!  Looks like there is a Scheme process still running!")
            # Kill all subprocesses
            for op in self.processingQueue:
                try:
                    op.process.kill()
                except AttributeError:
                    warn(f"$$$$  Could not kill process for {op}")
        # Stop all timers
        self.stopTimer(self.schemeDefinitionTimer)
        self.stopTimer(self.bestGuessTimer)
        for timer in self.testTimers:
            self.stopTimer(timer)

    def makeQuerySimpleForMondoSchemeFileString(self, interp_string: str) -> str:

        # Get the scheme definition text
        definitionText = self.schemeDefinitionView.toPlainText()
        # Create the simple query using makeQueryString (simple=True)
        querySimple = self.makeQueryString(
            definitionText, body=",_", expectedOut="q", simple=True, name="-simple"
        )

        return QUERY_SIMPLE_T.substitute(
            load_mk_vicare=LOAD_MK_VICARE,
            load_mk=LOAD_MK,
            interp_string=interp_string,
            query_simple=querySimple,
        )

    def makeAllTestsQueryString(self) -> str:
        # Gather test inputs and outputs
        processTest = [False] * 6
        testInputs = [""] * 6
        testOutputs = [""] * 6
        for i in range(6):
            processTest[i] = (
                self.testInputs[i].text() != ""
                and self.testExpectedOutputs[i].text() != ""
            )
            testInputs[i] = self.testInputs[i].text() if processTest[i] else ""
            testOutputs[i] = (
                self.testExpectedOutputs[i].text() if processTest[i] else ""
            )

        allTestInputs = " ".join(testInputs)
        allTestOutputs = " ".join(testOutputs)

        definitionText = self.schemeDefinitionView.toPlainText()

        full_string = ALL_TEST_WRITE_T.substitute(
            definitionText=definitionText,
            allTestInputs=allTestInputs,
            allTestOutputs=allTestOutputs,
        )

        print(f"Generated allTestWriteString:\n{rainbowp(full_string)}")
        return full_string

    def makeQueryString(
        self, defns: str, body: str, expectedOut: str, simple: bool, name: str
    ) -> str:
        if simple:
            parse_ans_string = SIMPLE_PARSE_ANS_T.substitute(
                name=name, defns=defns, body=body
            )
        else:
            parse_ans_string = PARSE_ANS_T.substitute(name=name, defns=defns, body=body)

        # Load the eval query string parts from constants
        eval_string = EVAL_T.substitute(defns=defns, body=body, expectedOut=expectedOut)

        eval_string_fast = EVAL_FAST_T.substitute(eval_string=eval_string)
        eval_string_complete = EVAL_COMPLETE_T.substitute(eval_string=eval_string)
        eval_string_both = EVAL_BOTH_T.substitute(
            eval_string_fast=eval_string_fast, eval_string_complete=eval_string_complete
        )

        define_ans_string = DEFINE_ANS_T.substitute(
            name=name, eval_string_both=eval_string_both
        )

        query_type = SIMPLE_Q if simple else INDIVIDUAL_Q

        full_string = FULL_T.substitute(
            query_type=query_type,
            parse_ans_string=parse_ans_string,
            define_ans_string=define_ans_string,
        )

        print(f"Generated query string:\n{rainbowp(full_string)}\n")
        return full_string

    def startTimer(self, timer):
        if isinstance(timer, QTimer):
            timer.start(50)

    def stopTimer(self, timer):
        if isinstance(timer, QTimer):
            timer.stop()

    def updateBestGuess(self, taskType: str, output: str):
        if taskType == "simple":
            self.bestGuessView.setPlainText(output)
            self.stopTimer(self.bestGuessTimer)

    def updateAllTestsResults(self, taskType: str, output: str):
        if taskType == "allTests":
            try:
                lines = output.strip().split("\n")
                results = [
                    line.split(":", 1)[1].strip() for line in lines if ":" in line
                ]
                print(f"Extracted results: {results}")

                for i in range(min(6, len(results))):
                    self.testStatusLabels[i].setText(results[i])
                    if "ERROR" in results[i] or "Exception" in results[i]:
                        self.testStatusLabels[i].setStyleSheet("color: red;")
                        self.errorOutputView.setPlainText(output)
                        self.errorOutputView.show()
                    else:
                        self.testStatusLabels[i].setStyleSheet("color: green;")
                    self.stopTimer(self.testTimers[i])
            except Exception as e:
                print(f"Error processing all tests results: {e}")
                traceback.print_exc()
                self.errorOutputView.setPlainText(f"Error processing results: {e}")
                self.errorOutputView.show()
            finally:
                for timer in self.testTimers:
                    self.stopTimer(timer)
                self.stopTimer(self.schemeDefinitionTimer)
                if self.runCodeTimer.isActive():
                    self.runCodeTimer.stop()
                self.runCodeTimer.start(1000)

    def handleOperationFinished(self, taskType: str, output: str):
        """Handle operation completion - runs on main thread"""
        if taskType == "simple":
            self.bestGuessView.setPlainText(output)
            self.stopTimer(self.bestGuessTimer)
        elif taskType == "allTests":
            self.updateAllTestsResults(
                taskType, output
            )  # Changed from handleAllTestsResults to updateAllTestsResults
        elif taskType == "error":  # Handle errors
            self.errorOutputView.setPlainText(output)
            self.errorOutputView.show()  # Show error output view when errors occur

    def handleStatusUpdate(self, taskType: str, status: str, color: str):
        """Handle status updates - runs on main thread"""
        if taskType == "simple":
            self.definitionStatusLabel.setText(status)
            self.definitionStatusLabel.setStyleSheet(f"color: {color};")
        elif taskType == "allTests":
            self.bestGuessStatusLabel.setText(status)
            self.bestGuessStatusLabel.setStyleSheet(f"color: {color};")

    def handleTimerUpdate(self, taskType: str, isRunning: bool):
        """Handle timer state changes - runs on main thread"""
        if taskType == "simple":
            if isRunning:
                self.startTimer(self.schemeDefinitionTimer)
            else:
                self.stopTimer(self.schemeDefinitionTimer)
        elif taskType == "allTests":
            if isRunning:
                self.startTimer(self.bestGuessTimer)
            else:
                self.stopTimer(self.bestGuessTimer)

    def executeRunCodeTimer(self):
        """Run code from the edit pane after a delay."""
        self.runCodeTimer.stop()
        self.runCodeFromEditPane()

    def handleTestTimeout(self):
        """Handle timeout for test execution."""
        print("Test timed out!")
        for i, timer in enumerate(self.testTimers):
            if timer.isActive():
                self.testStatusLabels[i].setText("Timeout")
                self.testStatusLabels[i].setStyleSheet("color: red;")

        self.cancel_all_operations()

        self.errorOutputView.setPlainText("Test execution timed out.")
        self.errorOutputView.show()
