import subprocess
import time
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QTextCharFormat

class RunSchemeOperation(QThread):
    # Signal to report when the task is finished: (taskType, output)
    finishedSignal = pyqtSignal(str, str)

    def __init__(self, editorWindowController, schemeScriptPathString, taskType):
        super().__init__()
        self.editorWindowController = editorWindowController
        self.schemeScriptPathString = schemeScriptPathString
        self.taskType = taskType
        self._isCanceled = False
        self.process = None
        
        # Color constants (using names; in production, use proper QPalettes)
        self.kDefaultColor = "black"
        self.kSyntaxErrorColor = "orange"
        self.kParseErrorColor = "magenta"
        self.kFailedErrorColor = "red"
        self.kThinkingColor = "purple"
        
        self.kIllegalSexprString = "Illegal sexpression"
        self.kParseErrorString = "Syntax error"
        self.kEvaluationFailedString = "Evaluation failed"
        self.kThinkingString = "???"
        
        # Add font settings
        self.defaultFont = QFont("Monaco", 12)  # Match EditorWindowController.fontName()
        

    def start_spinner(self):
        if self.taskType.startswith("test"):
            test_num = int(self.taskType[-1])
            if 1 <= test_num <= 6:
                getattr(self.editorWindowController, f"test{test_num}Spinner").show()
                return
        
        def show_spinner():
            ed = self.editorWindowController
            if self.taskType == "simple":
                ed.schemeDefinitionSpinner.show()
                ed.schemeDefinitionSpinner.start()
            elif self.taskType == "allTests":
                ed.bestGuessSpinner.show()
                ed.bestGuessSpinner.start()
            elif self.taskType.startswith("test"):
                test_num = self.taskType[-1]
                spinner = getattr(ed, f"test{test_num}Spinner", None)
                if spinner:
                    spinner.show()
                    spinner.start()
        QTimer.singleShot(0, show_spinner)

    def stop_spinner(self):
        if self.taskType.startswith("test"):
            test_num = int(self.taskType[-1])
            if 1 <= test_num <= 6:
                getattr(self.editorWindowController, f"test{test_num}Spinner").hide()
                return
                
        def hide_spinner():
            ed = self.editorWindowController
            if self.taskType == "simple":
                ed.schemeDefinitionSpinner.stop()
                ed.schemeDefinitionSpinner.hide()
            elif self.taskType == "allTests":
                ed.bestGuessSpinner.stop() 
                ed.bestGuessSpinner.hide()
            elif self.taskType.startswith("test"):
                test_num = self.taskType[-1]
                spinner = getattr(ed, f"test{test_num}Spinner", None)
                if spinner:
                    spinner.stop()
                    spinner.hide()
        QTimer.singleShot(0, hide_spinner)

    def set_font_and_size(self, view):
        fmt = QTextCharFormat()
        fmt.setFont(self.defaultFont)
        view.setCurrentCharFormat(fmt)

    def on_best_guess_success(self, best_guess_view, label, guess):
        def update_ui():
            if guess in ["illegal-sexp-in-defn", "parse-error-in-defn", 
                        "illegal-sexp-in-test/answer", "parse-error-in-test/answer"]:
                best_guess_view.clear()
                self.set_font_and_size(best_guess_view)
                label.setStyleSheet(f"color: {self.kThinkingColor};")
                label.setText(self.kThinkingString)
            else:
                best_guess_view.setPlainText(guess)
                self.set_font_and_size(best_guess_view)
                label.setStyleSheet(f"color: {self.kDefaultColor};")
                elapsed = time.monotonic() - self.start_time
                label.setText(f"Succeeded ({elapsed:.2f}s)")
                self.editorWindowController.cancel_all_operations()
        QTimer.singleShot(0, update_ui)

    def on_best_guess_failure(self, best_guess_view, label):
        def update_ui():
            best_guess_view.clear()
            self.set_font_and_size(best_guess_view)
            label.setStyleSheet(f"color: {self.kFailedErrorColor};")
            elapsed = time.monotonic() - self.start_time
            label.setText(f"Failed ({elapsed:.2f}s)")
            self.editorWindowController.cancel_all_operations()
        QTimer.singleShot(0, update_ui)

    def on_best_guess_killed(self, best_guess_view, label):
        def update_ui():
            best_guess_view.clear()
            self.set_font_and_size(best_guess_view)
            label.setStyleSheet(f"color: {self.kDefaultColor};")
            label.setText("")
        QTimer.singleShot(0, update_ui)

    def on_syntax_error_best_guess(self, best_guess_view, label):
        def update_ui():
            # Set default color on full range
            best_guess_view.setStyleSheet(f"color: {self.kDefaultColor};")
            best_guess_view.clear()
            self.set_font_and_size(best_guess_view)
            label.setStyleSheet(f"color: {self.kDefaultColor};")
            label.setText("")
        QTimer.singleShot(0, update_ui)

    def show_error_in_defn(self, error_text):
        def update_ui():
            ed = self.editorWindowController
            ed.schemeDefinitionView.setStyleSheet(f"color: {self.kFailedErrorColor};")
            ed.definitionStatusLabel.setStyleSheet(f"color: {self.kFailedErrorColor};")
            ed.definitionStatusLabel.setText(error_text)
        QTimer.singleShot(0, update_ui)

    def run(self):
        if self._isCanceled:
            print(f"RunSchemeOperation: Operation {self.taskType} canceled before start.")
            return
        print(f"RunSchemeOperation: Starting operation for task '{self.taskType}'")
        self.start_time = time.monotonic()
        self.start_spinner()
        self.thinking_color_and_label()
        
        try:
            print("RunSchemeOperation: Launching subprocess")
            self.process = subprocess.Popen(
                ['scheme', self.schemeScriptPathString],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(f"RunSchemeOperation: Process started with PID {self.process.pid}")
            output, err = self.process.communicate()
            if err:
                output += f"\nErrors: {err}"
                print(f"RunSchemeOperation: Subprocess reported errors: {err.strip()}")
        except Exception as e:
            output = f"Error: {e}"
            print(f"RunSchemeOperation: Exception occurred: {e}")
        finally:
            self.stop_spinner()
            exit_status = self.process.returncode if self.process else -1
            print(f"RunSchemeOperation: Process exited with status {exit_status}")
            
            def update_ui_post():
                ed = self.editorWindowController
                print(f"RunSchemeOperation: Updating UI for task '{self.taskType}'")
                if exit_status == 0:
                    if self.taskType == "simple":
                        if output.strip() == "parse-error-in-defn":
                            self.parse_error_in_defn()
                        elif output.strip() == "illegal-sexp-in-defn":
                            self.illegal_sexp_in_defn()
                        elif output.strip() == "()":
                            ed.schemeDefinitionView.setStyleSheet(f"color: {self.kFailedErrorColor};")
                            ed.definitionStatusLabel.setStyleSheet(f"color: {self.kFailedErrorColor};")
                            ed.definitionStatusLabel.setText(self.kEvaluationFailedString)
                        else:
                            ed.schemeDefinitionView.setStyleSheet(f"color: {self.kDefaultColor};")
                            ed.definitionStatusLabel.setStyleSheet(f"color: {self.kDefaultColor};")
                            ed.definitionStatusLabel.setText("")
                    elif self.taskType.startswith("test"):
                        test_num = self.taskType[-1]
                        input_field = getattr(ed, f"test{test_num}InputField", None)
                        output_field = getattr(ed, f"test{test_num}ExpectedOutputField", None)
                        label = getattr(ed, f"test{test_num}StatusLabel", None)
                        
                        if output.strip() == "illegal-sexp-in-test/answer" or output.strip() == "parse-error-in-test/answer":
                            self.on_test_syntax_error(input_field, output_field, label)
                        elif output.strip() == "illegal-sexp-in-defn" or output.strip() == "parse-error-in-defn":
                            input_field.setStyleSheet(f"color: {self.kThinkingColor};")
                            output_field.setStyleSheet(f"color: {self.kThinkingColor};")
                            label.setStyleSheet(f"color: {self.kThinkingColor};")
                            label.setText(self.kThinkingString)
                        elif output.strip() == "()":
                            self.on_test_failure(input_field, output_field, label)
                        else:
                            self.on_test_success(input_field, output_field, label)
                    elif self.taskType == "allTests":
                        if output.strip() == "fail":
                            self.on_best_guess_failure(ed.bestGuessView, ed.bestGuessStatusLabel)
                        else:
                            self.on_best_guess_success(ed.bestGuessView, ed.bestGuessStatusLabel, output.strip())
                elif exit_status == 15:
                    print(f"RunSchemeOperation: SIGTERM received for task: {self.taskType}")
                    if self.taskType == "allTests":
                        self.on_best_guess_killed(ed.bestGuessView, ed.bestGuessStatusLabel)
                    if self.taskType.startswith("test"):
                        self.on_test_success(getattr(ed, f"test{self.taskType[-1]}InputField", None),
                                         getattr(ed, f"test{self.taskType[-1]}ExpectedOutputField", None),
                                         getattr(ed, f"test{self.taskType[-1]}StatusLabel", None))
                else:
                    if self.taskType == "simple":
                        print(f"RunSchemeOperation: Non-zero exit for 'simple': {exit_status}")
                        self.show_error_in_defn(output.strip())
                    elif self.taskType.startswith("test"):
                        input_field = getattr(ed, f"test{self.taskType[-1]}InputField", None)
                        output_field = getattr(ed, f"test{self.taskType[-1]}ExpectedOutputField", None)
                        label = getattr(ed, f"test{self.taskType[-1]}StatusLabel", None)
                        self.on_test_syntax_error(input_field, output_field, label)
                    elif self.taskType == "allTests":
                        self.on_syntax_error_best_guess(ed.bestGuessView, ed.bestGuessStatusLabel)
                
                elapsed = time.monotonic() - self.start_time
                print(f"RunSchemeOperation: Task {self.taskType} completed in {elapsed:.2f} seconds.")
                self.finishedSignal.emit(self.taskType, output)
            
            QTimer.singleShot(0, update_ui_post)

    def cancel(self):
        self._isCanceled = True
        if self.process:
            try:
                self.process.kill()
                print(f"Process for {self.taskType} killed.")
            except Exception as e:
                print(f"Error killing process for {self.taskType}: {e}")
        print(f"Operation {self.taskType} canceled.")

    def illegal_sexp_in_defn(self):
        def update_ui():
            ed = self.editorWindowController
            ed.schemeDefinitionView.setStyleSheet(f"color: {self.kSyntaxErrorColor};")
            ed.definitionStatusLabel.setStyleSheet(f"color: {self.kSyntaxErrorColor};")
            ed.definitionStatusLabel.setText(self.kIllegalSexprString)
        QTimer.singleShot(0, update_ui)

    def parse_error_in_defn(self):
        def update_ui():
            ed = self.editorWindowController
            ed.schemeDefinitionView.setStyleSheet(f"color: {self.kParseErrorColor};")
            ed.definitionStatusLabel.setStyleSheet(f"color: {self.kParseErrorColor};")
            ed.definitionStatusLabel.setText(self.kParseErrorString)
            if hasattr(ed, "schemeOperationAllTests") and ed.schemeOperationAllTests:
                ed.schemeOperationAllTests.cancel()
        QTimer.singleShot(0, update_ui)

    def thinking_color_and_label(self):
        def update_ui():
            ed = self.editorWindowController
            if self.taskType == "simple":
                ed.definitionStatusLabel.setStyleSheet(f"color: {self.kThinkingColor};")
                ed.definitionStatusLabel.setText(self.kThinkingString)
            elif self.taskType == "allTests":
                ed.bestGuessStatusLabel.setStyleSheet(f"color: {self.kThinkingColor};")
                ed.bestGuessStatusLabel.setText(self.kThinkingString)
                ed.bestGuessView.setStyleSheet(f"color: {self.kThinkingColor};")
            elif self.taskType.startswith("test"):
                test_num = self.taskType[-1]
                label = getattr(ed, f"test{test_num}StatusLabel", None)
                input_field = getattr(ed, f"test{test_num}InputField", None)
                output_field = getattr(ed, f"test{test_num}ExpectedOutputField", None)
                if label:
                    label.setStyleSheet(f"color: {self.kThinkingColor};")
                    label.setText(self.kThinkingString)
                if input_field:
                    input_field.setStyleSheet(f"color: {self.kThinkingColor};")
                if output_field:
                    output_field.setStyleSheet(f"color: {self.kThinkingColor};")
        QTimer.singleShot(0, update_ui)

    def on_test_success(self, input_field, output_field, label):
        def update_ui():
            input_field.setStyleSheet(f"color: {self.kDefaultColor};")
            output_field.setStyleSheet(f"color: {self.kDefaultColor};")
            label.setStyleSheet(f"color: {self.kDefaultColor};")
            elapsed = time.monotonic() - self.start_time
            label.setText(f"Succeeded ({elapsed:.2f}s)")
        QTimer.singleShot(0, update_ui)

    def on_test_failure(self, input_field, output_field, label):
        def update_ui():
            input_field.setStyleSheet(f"color: {self.kFailedErrorColor};")
            output_field.setStyleSheet(f"color: {self.kFailedErrorColor};")
            label.setStyleSheet(f"color: {self.kFailedErrorColor};")
            elapsed = time.monotonic() - self.start_time
            label.setText(f"Failed ({elapsed:.2f}s)")
        QTimer.singleShot(0, update_ui)

    def on_test_syntax_error(self, input_field, output_field, label):
        def update_ui():
            input_field.setStyleSheet(f"color: {self.kSyntaxErrorColor};")
            output_field.setStyleSheet(f"color: {self.kSyntaxErrorColor};")
            label.setStyleSheet(f"color: {self.kSyntaxErrorColor};")
            label.setText(self.kIllegalSexprString)
        QTimer.singleShot(0, update_ui)
