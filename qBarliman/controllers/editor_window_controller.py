import os
import subprocess
import time
import traceback

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QTextEdit, QLineEdit, QLabel, QVBoxLayout, QGridLayout, 
    QSplitter, QProgressBar, QMessageBox, QHBoxLayout
)
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal

from qBarliman.operations.run_scheme_operation import RunSchemeOperation
from qBarliman.utils.constrained_splitter import ConstrainedSplitter 
from qBarliman.widgets.scheme_editor_text_view import SchemeEditorTextView
from qBarliman.widgets.spinner_widget import SpinnerWidget


class EditorWindowController(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Barliman")
        self.setupUI()
        self.runCodeTimer = QTimer(self)
        self.runCodeTimer.setSingleShot(True)
        self.runCodeTimer.timeout.connect(self.runCodeFromEditPane)
        self.interpreter_code = ""
        self.processingQueue = []  # For concurrency, consider using QThreadPool
        self.schemeOperationAllTests = None
        self.loadInterpreterCode("interp")
        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.timeout.connect(self.cleanup)

    def setupUI(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        default_font = QFont("Monaco", 14)

        # --- Text Views (equivalent to NSTextView) ---
        self.schemeDefinitionView = SchemeEditorTextView(self)
        self.schemeDefinitionView.setPlaceholderText("Enter Scheme definitions...")
        self.schemeDefinitionView.setFont(default_font)
        self.schemeDefinitionView.setText(
            "(define ,A\n"
            "  (lambda ,B\n"
            ",C))\n\n"
        )
        # Disable rich text to mimic Swift's smart quotes disabled
        self.schemeDefinitionView.setAcceptRichText(False)
        self.schemeDefinitionView.textChanged.connect(self.setupRunCodeFromEditPaneTimer)

        self.bestGuessView = SchemeEditorTextView(self)
        self.bestGuessView.setPlaceholderText("Best guess output...")
        self.bestGuessView.setFont(default_font)
        self.bestGuessView.setAcceptRichText(False)

        # --- Splitter (equivalent to NSSplitView) ---
        self.definitionAndBestGuessSplitView = ConstrainedSplitter(
            Qt.Orientation.Vertical, self, min_sizes=[100, 100], max_sizes=[500, 500]
        )
        self.definitionAndBestGuessSplitView.addWidget(self.schemeDefinitionView)
        self.definitionAndBestGuessSplitView.addWidget(self.bestGuessView)
        layout.addWidget(self.definitionAndBestGuessSplitView)

        # --- Progress Indicators (equivalent to NSProgressIndicator) ---
        self.schemeDefinitionSpinner = SpinnerWidget(self)
        self.bestGuessSpinner = SpinnerWidget(self)
        
        # Add spinners to layout with proper alignment
        spinner_layout = QHBoxLayout()
        spinner_layout.addStretch()
        spinner_layout.addWidget(self.schemeDefinitionSpinner)
        layout.addLayout(spinner_layout)

        # --- Status Labels ---
        self.definitionStatusLabel = QLabel("", self)
        self.definitionStatusLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | 
                                                         Qt.TextInteractionFlag.TextSelectableByKeyboard)
        layout.addWidget(self.definitionStatusLabel)
        
        self.bestGuessStatusLabel = QLabel("", self)
        self.bestGuessStatusLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | 
                                                        Qt.TextInteractionFlag.TextSelectableByKeyboard)
        layout.addWidget(self.bestGuessStatusLabel)

        # --- Test Fields (equivalent to NSTextField) ---
        self.testInputs = []
        self.testExpectedOutputs = []
        self.testStatusLabels = []
        self.testSpinners = []
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
            status_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | 
                                               Qt.TextInteractionFlag.TextSelectableByKeyboard)
            self.testStatusLabels.append(status_label)
            grid.addWidget(status_label, i, 3)

            spinner = SpinnerWidget(self)
            self.testSpinners.append(spinner)
            # Add to grid layout in last column
            grid.addWidget(spinner, i, 4, Qt.AlignmentFlag.AlignRight)
            spinner.hide()  # Initially hidden
        layout.addLayout(grid)

        # --- Default Test Examples ---
        default_test_inputs = [
            "(append '() '5)",
            "(append '(a) '6)",
            "(append '(e f) '(g h))",
            "",
            "",
            ""
        ]
        default_test_expected = [
            "5",
            "'(a . 6)",
            "'(e f g h)",
            "",
            "",
            ""
        ]
        for i in range(6):
            self.testInputs[i].setText(default_test_inputs[i])
            self.testExpectedOutputs[i].setText(default_test_expected[i])

        # --- Tab Order Fix (Test 3 Expected -> Test 4 Input) ---
        QWidget.setTabOrder(self.testExpectedOutputs[2], self.testInputs[3])

    # --- Timer and Code Execution Methods ---
    def setupRunCodeFromEditPaneTimer(self):
        # Restart timer with a 500ms delay on text changes
        self.runCodeTimer.start(500)

    def runCodeFromEditPane(self):
        print("Running code from edit pane...")
        tmp_dir = os.path.join(os.environ.get("TMP", "/tmp"), "barliman_tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        print(f"runCodeFromEditPane: Temporary directory at {tmp_dir}")
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # Old paths:
        # mk_vicare_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
        #                              "qBarliman", "minikanren", "core", "mk", "mk-vicare.scm")
        # mk_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
        #                         "qBarliman", "minikanren", "core", "mk", "mk.scm")
        # New correct paths (assuming mk files are located under "minikanren/mk/"):
        mk_vicare_path = os.path.join(base_dir, "qBarliman", "minikanren", "core", "mk-vicare.scm")
        mk_path = os.path.join(base_dir, "qBarliman", "minikanren", "core", "mk.scm")
        print(f"runCodeFromEditPane: mk_vicare_path: {mk_vicare_path}, mk_path: {mk_path}")
        
        definitionText = self.schemeDefinitionView.toPlainText()
        interp_string = self.interpreter_code
        
        query_simple = self.makeQuerySimpleForMondoSchemeFileString(
            interp_string, 
            mk_vicare_path_string=mk_vicare_path,
            mk_path_string=mk_path
        )
        query_alltests = self.makeAllTestsQueryString()
        print("runCodeFromEditPane: Query strings generated")
        
        # Write temporary files
        with open(os.path.join(tmp_dir, "barliman-query-simple.scm"), "w") as f:
            f.write(query_simple)
            print("runCodeFromEditPane: Written barliman-query-simple.scm")
        with open(os.path.join(tmp_dir, "barliman-query-alltests.scm"), "w") as f:
            f.write(query_alltests)
            print("runCodeFromEditPane: Written barliman-query-alltests.scm")
        
        # Create RunSchemeOperations
        runSchemeOpSimple = RunSchemeOperation(self, os.path.join(tmp_dir, "barliman-query-simple.scm"), "simple")
        runSchemeOpAllTests = RunSchemeOperation(self, os.path.join(tmp_dir, "barliman-query-alltests.scm"), "allTests")
        print("runCodeFromEditPane: Created RunSchemeOperation instances")
        
        # Connect signals
        runSchemeOpSimple.finishedSignal.connect(self.handleOperationFinished)
        runSchemeOpSimple.statusUpdateSignal.connect(self.handleStatusUpdate)
        runSchemeOpSimple.spinnerUpdateSignal.connect(self.handleSpinnerUpdate)

        runSchemeOpAllTests.finishedSignal.connect(self.handleOperationFinished)
        runSchemeOpAllTests.statusUpdateSignal.connect(self.handleStatusUpdate)
        runSchemeOpAllTests.spinnerUpdateSignal.connect(self.handleSpinnerUpdate)
        
        # Add operations to processing queue
        # Cancel existing operations
        for op in self.processingQueue:
            if op.isRunning():
                op.cancel()
        self.processingQueue.clear()

        self.processingQueue = [runSchemeOpSimple, runSchemeOpAllTests]
        print("runCodeFromEditPane: Starting operations")

        # Start spinners
        self.startSpinner(self.schemeDefinitionSpinner)
        self.startSpinner(self.bestGuessSpinner)
        for spinner in self.testSpinners:
            self.startSpinner(spinner)

        for op in self.processingQueue:
            op.start()

    def cleanup(self):
        if self.runCodeTimer.isActive():
            self.runCodeTimer.stop()
        for op in self.processingQueue:
            if op.isRunning():
                op.cancel()
        self.processingQueue.clear()
        print("Cleanup complete.")
        # Stop all spinners
        self.stopSpinner(self.schemeDefinitionSpinner)
        self.stopSpinner(self.bestGuessSpinner)
        for spinner in self.testSpinners:
            self.stopSpinner(spinner)

    def loadInterpreterCode(self, interpFileName: str):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # Old path:
        # file_path = os.path.join(base_dir, "qBarliman", "minikanren", "core", f"{interpFileName}.scm")
        # New correct path:
        file_path = os.path.join(base_dir, "qBarliman", "minikanren", "rel-interp", f"{interpFileName}.scm")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.interpreter_code = f.read()
            self.definitionStatusLabel.setText("Interpreter code loaded.")
        except Exception as e:
            error_message = f"Error loading interpreter code: {e}"
            print(error_message)
            self.definitionStatusLabel.setText(error_message)
            self.interpreter_code = ""

    def getInterpreterCode(self) -> str:
        # Ported from Swift's getInterpreterCode()
        return self.interpreter_code


    # --- Cleanup ---
    def cleanup(self):
        print("cleaning up!")
        # Stop the timer used for delayed code execution
        self.runCodeTimer.stop()
        
        # Cancel all operations in the processing queue.
        # Assuming each op in self.processingQueue is a QThread or has a cancel() method.
        for op in self.processingQueue:
            try:
                op.cancel()  # if defined in RunSchemeOperation
            except AttributeError:
                pass
        
        # Wait for any operations that support waiting (e.g., QThread)
        for op in self.processingQueue:
            if hasattr(op, 'wait'):
                op.wait()
        
        print(f"Operation count after cleanup: {len(self.processingQueue)}")
        if self.processingQueue:
            print("$$$$  Oh noes!  Looks like there is a Scheme process still running!")
        # Stop all spinners
        self.stopSpinner(self.schemeDefinitionSpinner)
        self.stopSpinner(self.bestGuessSpinner)
        for spinner in self.testSpinners:
            self.stopSpinner(spinner)

    # --- Timer for Code Execution ---
    def setupRunCodeFromEditPaneTimer(self):
        # Invalidate any existing timer and start a new one with 1 second delay,
        # matching the Swift behavior.
        self.runCodeTimer.stop()
        self.runCodeTimer.start(1000)  # 1000 milliseconds = 1 second

    # --- Text Change Handlers ---
    # Although the QTextEdit and QLineEdit signals are already connected to setupRunCodeFromEditPaneTimer,
    # you can add these methods if you want to log the changes as done in Swift.
    def textDidChange(self):
        print("@@@@@@@@@@@@@@@@@@@ textDidChange")
        self.setupRunCodeFromEditPaneTimer()

    def controlTextDidChange(self):
        print("@@@@@@@@@@@@@@@@@@@ controlTextDidChange")
        self.setupRunCodeFromEditPaneTimer()



    def makeQuerySimpleForMondoSchemeFileString(self, interp_string: str, mk_vicare_path_string: str, mk_path_string: str) -> str:



        
        # Build load commands
        load_mk_vicare = f"(load \"{mk_vicare_path_string}\")"
        load_mk = f"(load \"{mk_path_string}\")"
        # Get the scheme definition text
        definitionText = self.schemeDefinitionView.toPlainText()
        # Create the simple query using makeQueryString (simple=True)
        querySimple = self.makeQueryString(definitionText, body=",_", expectedOut="q", simple=True, name="-simple")
        full_string = f"{load_mk_vicare}\n{load_mk}\n{interp_string}\n{querySimple}"
        return full_string
    def makeAllTestsQueryString(self) -> str:
        # Gather test inputs and outputs
        processTest = [False] * 6
        testInputs = [""] * 6
        testOutputs = [""] * 6
        for i in range(6):
            processTest[i] = (self.testInputs[i].text() != "" and 
                            self.testExpectedOutputs[i].text() != "")
            testInputs[i] = self.testInputs[i].text() if processTest[i] else ""
            testOutputs[i] = self.testExpectedOutputs[i].text() if processTest[i] else ""
        allTestInputs = (testInputs[0] + " " + testInputs[1] + " " +
                        testInputs[2] + " " + testInputs[3] + " " +
                        testInputs[4] + " " + testInputs[5] + " ")
        allTestOutputs = (testOutputs[0] + " " + testOutputs[1] + " " +
                        testOutputs[2] + " " + testOutputs[3] + " " +
                        testOutputs[4] + " " + testOutputs[5] + " ")

        definitionText = self.schemeDefinitionView.toPlainText()

        # Load query string parts from files
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        part1_path = os.path.join(base_dir, "mk-and-rel-interp", "interp-alltests-query-string-part-1.scm")
        part2_path = os.path.join(base_dir, "mk-and-rel-interp", "interp-alltests-query-string-part-2.scm")
        try:
            with open(part1_path, "r", encoding="utf-8") as f:
                alltests_string_part_1 = f.read()
        except Exception:
            alltests_string_part_1 = ""
        try:
            with open(part2_path, "r", encoding="utf-8") as f:
                alltests_string_part_2 = f.read()
        except Exception:
            alltests_string_part_2 = ""
        
        eval_flags_fast = "(allow-incomplete-search)"
        eval_flags_complete = "(disallow-incomplete-search)"
        eval_string_fast = f"(begin {eval_flags_fast} (results))"
        eval_string_complete = f"(begin {eval_flags_complete} (results))"

        allTestWriteString = (
            f"(define (ans-allTests)\n"
            f"  (define (results)\n"
            f"{alltests_string_part_1}\n"
            f"        (== `({definitionText}) defn-list)\n\n"
            f"{alltests_string_part_2}\n"
            f"(== `({definitionText}) defns) (appendo defns `(((lambda x x) {allTestInputs})) begin-body) (evalo `(begin . ,begin-body) (list {allTestOutputs})))\n"
            f"(let ((results-fast {eval_string_fast}))\n"
            f"  (if (null? results-fast)\n"
            f"    {eval_string_complete}\n"
            f"    results-fast)))"
        )


        full_string = f";; allTests\n{allTestWriteString}"

        print(f"Generated allTestWriteString:\n{full_string}")
        return full_string

    def makeQueryString(self, defns: str, body: str, expectedOut: str, simple: bool, name: str) -> str:
        if simple:
            parse_ans_string = (
                f"(define (parse-ans{name}) (run 1 (q)\n"
                f" (let ((g1 (gensym \"g1\")) (g2 (gensym \"g2\")) (g3 (gensym \"g3\")) "
                f"(g4 (gensym \"g4\")) (g5 (gensym \"g5\")) (g6 (gensym \"g6\")) "
                f"(g7 (gensym \"g7\")) (g8 (gensym \"g8\")) (g9 (gensym \"g9\")) "
                f"(g10 (gensym \"g10\")) (g11 (gensym \"g11\")) (g12 (gensym \"g12\")) "
                f"(g13 (gensym \"g13\")) (g14 (gensym \"g14\")) (g15 (gensym \"g15\")) "
                f"(g16 (gensym \"g16\")) (g17 (gensym \"g17\")) (g18 (gensym \"g18\")) "
                f"(g19 (gensym \"g19\")) (g20 (gensym \"g20\")))\n"
                f" (fresh (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z _) (parseo `(begin {defns} {body}))))))"
            )
        else:
            parse_ans_string = (
                f"(define (parse-ans{name}) (run 1 (q)\n"
                f" (let ((g1 (gensym \"g1\")) (g2 (gensym \"g2\")) (g3 (gensym \"g3\")) "
                f"(g4 (gensym \"g4\")) (g5 (gensym \"g5\")) (g6 (gensym \"g6\")) "
                f"(g7 (gensym \"g7\")) (g8 (gensym \"g8\")) (g9 (gensym \"g9\")) "
                f"(g10 (gensym \"g10\")) (g11 (gensym \"g11\")) (g12 (gensym \"g12\")) "
                f"(g13 (gensym \"g13\")) (g14 (gensym \"g14\")) (g15 (gensym \"g15\")) "
                f"(g16 (gensym \"g16\")) (g17 (gensym \"g17\")) (g18 (gensym \"g18\")) "
                f"(g19 (gensym \"g19\")) (g20 (gensym \"g20\")))\n"
                f" (fresh (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z _) "
                f"(fresh (names dummy-expr) (extract-nameso `( {defns} ) names) (parseo `((lambda ,names {body}) ,dummy-expr)))))))"
            )

        # Load the eval query string parts from files
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        part1_path = os.path.join(base_dir, "mk-and-rel-interp", "interp-eval-query-string-part-1.swift")
        part2_path = os.path.join(base_dir, "mk-and-rel-interp", "interp-eval-query-string-part-2.swift")
        try:
            with open(part1_path, "r", encoding="utf-8") as f:
                eval_string_part_1 = f.read()
        except Exception:
            print("!!!!!  LOAD_ERROR -- can't load eval_string_part_1")
            eval_string_part_1 = ""
        try:
            with open(part2_path, "r", encoding="utf-8") as f:
                eval_string_part_2 = f.read()
        except Exception:
            print("!!!!!  LOAD_ERROR -- can't load eval_string_part_2")
            eval_string_part_2 = ""

        eval_string = (
            eval_string_part_1 + "\n" +
            "        (== `( " + defns + " ) defn-list)\n" +
            eval_string_part_2 + "\n" +
            " (evalo `(begin " + defns + " " + body + " ) " + expectedOut + "))))"
        )
        
        eval_flags_fast = "(allow-incomplete-search)"
        eval_flags_complete = "(disallow-incomplete-search)"
        
        eval_string_fast = f"(begin {eval_flags_fast} {eval_string})"
        eval_string_complete = f"(begin {eval_flags_complete} {eval_string})"
        eval_string_both = (f"(let ((results-fast {eval_string_fast}))\n"
                            f"  (if (null? results-fast)\n"
                            f"    {eval_string_complete}\n"
                            f"     results-fast))")
        
        define_ans_string = (
            f"(define (query-val{name})\n"
            "  (if (null? (parse-ans" + name + "))\n"
            "      'parse-error\n"
            "      " + eval_string_both + "))   "
        )
        
        full_string = ((";; simple query" if simple else ";; individual test query") + "\n\n" +
                    (parse_ans_string) + "\n\n" +
                    define_ans_string + "\n\n")
        print(f"Generated query string:\n{full_string}\n")
        return full_string

    def startSpinner(self, spinner):
        if isinstance(spinner, SpinnerWidget):
            spinner.startAnimation()
        
    def stopSpinner(self, spinner):
        if isinstance(spinner, SpinnerWidget):
            spinner.stopAnimation()

    def updateBestGuess(self, taskType: str, output: str):
        if taskType == "simple":
            self.bestGuessView.setPlainText(output)
            self.stopSpinner(self.bestGuessSpinner)
            
    def updateAllTestsResults(self, taskType: str, output: str):
        if taskType == "allTests":
            try:
                lines = output.strip().split('\n')
                results = [line.split(':', 1)[1].strip() for line in lines if ":" in line]
                print(f"Extracted results: {results}")

                for i in range(min(6, len(results))):
                    self.testStatusLabels[i].setText(results[i])
                    if "ERROR" in results[i]:
                        self.testStatusLabels[i].setStyleSheet("color: red;")
                    else:
                        self.testStatusLabels[i].setStyleSheet("color: green;")
                    self.stopSpinner(self.testSpinners[i])
            except Exception as e:
                print(f"Error processing all tests results: {e}")
                traceback.print_exc()
            finally:
                for spinner in self.testSpinners:
                    self.stopSpinner(spinner)
                self.stopSpinner(self.schemeDefinitionSpinner)
            
    def setupRunCodeFromEditPaneTimer(self):
        if not hasattr(self, "runCodeTimer"):
            self.runCodeTimer = QTimer(self)
            self.runCodeTimer.setSingleShot(True)
        if self.runCodeTimer.isActive():
            self.runCodeTimer.stop()
        self.runCodeTimer.start(1000)
        
    def cleanup(self):
        if self.runCodeTimer.isActive():
            self.runCodeTimer.stop()
        for op in self.processingQueue:
            if op.isRunning():
                op.cancel()
        self.processingQueue.clear()
        print("Cleanup complete.")
        # Stop all spinners
        self.stopSpinner(self.schemeDefinitionSpinner)
        self.stopSpinner(self.bestGuessSpinner)
        for spinner in self.testSpinners:
            self.stopSpinner(spinner)
        
    def cancel_all_operations(self):
        # Cancel and join all operations
        for op in self.processingQueue:
            try:
                op.cancel()
            except Exception:
                pass
        for op in self.processingQueue:
            if hasattr(op, "wait"):
                op.wait()
        self.processingQueue.clear()

    def handleOperationFinished(self, taskType: str, output: str):
        """Handle operation completion - runs on main thread"""
        if taskType == "simple":
            self.bestGuessView.setPlainText(output)
            self.stopSpinner(self.bestGuessSpinner)
        elif taskType == "allTests":
            self.updateAllTestsResults(taskType, output)  # Changed from handleAllTestsResults to updateAllTestsResults

    def handleStatusUpdate(self, taskType: str, status: str, color: str):
        """Handle status updates - runs on main thread"""
        if taskType == "simple":
            self.definitionStatusLabel.setText(status)
            self.definitionStatusLabel.setStyleSheet(f"color: {color};")
        # ...handle other status updates...

    def handleSpinnerUpdate(self, taskType: str, isSpinning: bool):
        """Handle spinner state changes - runs on main thread"""
        if taskType == "simple":
            if isSpinning:
                self.startSpinner(self.schemeDefinitionSpinner)
            else:
                self.stopSpinner(self.schemeDefinitionSpinner)
        # ...handle other spinners...
