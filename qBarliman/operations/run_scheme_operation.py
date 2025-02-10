import time
import os
from PySide6.QtCore import QThread, Signal, QProcess, Slot
from PySide6.QtGui import QColor
from qBarliman.constants import *


class RunSchemeOperation(QThread):
    finishedSignal = Signal(str, str)  # (taskType, output)
    statusUpdateSignal = Signal(str, str, str)  # (taskType, status, color)
    timerUpdateSignal = Signal(str, bool)  # (taskType, isRunning) # Changed to boolean

    def __init__(self, editor_window_controller, schemeScriptPathString, taskType):
        super().__init__()
        self.editor_window_controller = editor_window_controller
        self.schemeScriptPathString = schemeScriptPathString
        self.taskType = taskType
        self._isCanceled = False
        self.process = None
        self.start_time = time.monotonic()

        # Basic status constants - use QColor for consistency if needed later
        self.DEFAULT_COLOR = "black" #QColor(0, 0, 0) # Black
        self.SYNTAX_ERROR_COLOR = "orange" #QColor(255, 165, 0) # Orange
        self.PARSE_ERROR_COLOR = "magenta" #QColor(255, 0, 255) # Magenta
        self.FAILED_ERROR_COLOR = "red" #QColor(255, 0, 0) # Red
        self.THINKING_COLOR = "purple" #QColor(128, 0, 128) # Purple

        self.ILLEGAL_SEXPR_STRING = "Illegal sexpression"
        self.PARSE_ERROR_STRING = "Syntax error"
        self.EVALUATION_FAILED_STRING = "Evaluation failed"
        self.THINKING_STRING = "???"


    def run(self):
        if self._isCanceled:
            print("RunSchemeOperation: Operation was canceled before start")
            return

        try:
            print(f"RunSchemeOperation: Creating process for {self.taskType}")
            self.process = QProcess()
            self.process.finished.connect(self.handleProcessFinished)
            self.process.readyReadStandardOutput.connect(self.readStandardOutput)
            self.process.readyReadStandardError.connect(self.readStandardError)
            self.process.errorOccurred.connect(self.handleProcessError)

            print(
                f"RunSchemeOperation: Starting process with script {self.schemeScriptPathString}"
            )
            self.process.start(SCHEME_EXECUTABLE, [self.schemeScriptPathString])
            print("RunSchemeOperation: Process started.")
            self.timerUpdateSignal.emit(self.taskType, True) # Timer starts

            # Wait briefly for process to start
            if not self.process.waitForStarted(1000):
                print("RunSchemeOperation: Process failed to start within timeout!")
            else:
                print(
                    f"RunSchemeOperation: Process state after start: {self.process.state()}"
                )

        except Exception as e:
            print(f"RunSchemeOperation: Exception during process start: {e}")
            self.finishedSignal.emit(self.taskType, f"Error: {e}")
            self.timerUpdateSignal.emit(self.taskType, False) # Timer stops on error

    def cancel(self):
        debug(
            f"RunSchemeOperation.cancel: entry - Canceling operation for taskType={self.taskType}"
        )
        if self.process:
            debug(
                f"RunSchemeOperation.cancel: - Process state before terminate: {self.process.state()}"
            )
            debug(
                f"RunSchemeOperation.cancel: - Process ID: {self.process.processId()}"
            )

        self._isCanceled = True
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            debug("RunSchemeOperation.cancel: Attempting graceful termination")
            self.process.terminate()  # Try terminate first
            if not self.process.waitForFinished(1000):  # Wait up to 1 second
                debug(
                    "RunSchemeOperation.cancel: Process didn't terminate, forcing kill"
                )
                self.process.kill()  # Force kill if terminate doesn't work
                debug("RunSchemeOperation.cancel: Kill successful")
            else:
                debug("RunSchemeOperation.cancel: Terminate successful")
        else:
            debug("RunSchemeOperation.cancel: Process is not running or does not exist")

        if self.process:
            debug(
                f"RunSchemeOperation.cancel: - Process state after terminate: {self.process.state()}"
            )
        self.timerUpdateSignal.emit(self.taskType, False) # Timer stops on cancel


    @Slot()
    def handleProcessFinished(self):
        debug("RunSchemeOperation.handleProcessFinished: ENTRY - handler called!")
        debug(
            f"RunSchemeOperation.handleProcessFinished: Process finished at {time.time():.3f}"
        )
        output = self.process.readAllStandardOutput().data().decode()
        err = self.process.readAllStandardError().data().decode()
        exit_code = self.process.exitCode()
        exit_status = self.process.exitStatus()

        debug(
            f"RunSchemeOperation.handleProcessFinished: Exit code: {exit_code}"
        )
        debug(
            f"RunSchemeOperation.handleProcessFinished: Exit status: {exit_status}"
        )

        debug(
            f"RunSchemeOperation.handleProcessFinished: Output size: {len(output)} bytes"
        )
        if output:
            debug(
                f"RunSchemeOperation.handleProcessFinished: First 100 chars: {output[:100]}"
            )
        if err:
            debug(f"RunSchemeOperation.handleProcessFinished: Error: {err}")

        self.timerUpdateSignal.emit(self.taskType, False) # Timer stops on finish

        datastring = output
        errorDatastring = err
        taskType = self.taskType
        ewc = self.editor_window_controller


        if exit_code == 0: # Exit status 0 means ran to completion, but could still be errors in query
            debug(f"RunSchemeOperation.handleProcessFinished: Process finished successfully with exit code 0.")
            # print the output
            debug(f"Output: {datastring}")
            if self.taskType == "simple":
                if datastring.strip() == "parse-error-in-defn":
                    self.parseErrorInDefn()
                elif datastring.strip() == "illegal-sexp-in-defn":
                    self.illegalSexpInDefn()
                elif datastring.strip() == "()":
                    self.evaluationFailedInDefn() # New function to handle evaluation failure
                else:
                    self.defaultDefnStatus()
            elif taskType.startswith("test"): # "test1", "test2", ..., "test6"
                self.onTestCompletion(datastring)
            elif self.taskType == "allTests":
                if datastring.strip() == "fail":
                    self.onBestGuessFailure()
                else:
                    self.onBestGuessSuccess(datastring)

        elif exit_code == 15: # SIGTERM - Canceled
            debug(f"RunSchemeOperation.handleProcessFinished: Process was canceled with SIGTERM.")
            print(f"SIGTERM !!!  taskType = {self.taskType}")
            if self.taskType == "allTests":
                self.onBestGuessKilled()
            elif taskType.startswith("test"):
                self.onTestSuccess() #Assume tests succeed if allTests cancelled them

        else: # Other exit codes indicate Chez Scheme error (syntax, etc)
            debug(f"RunSchemeOperation.handleProcessFinished: Process finished with error exit code {exit_code}.")
            if self.taskType == "simple":
                print(f"exitStatus = {exit_code}")
                self.illegalSexpInDefn()
            elif taskType.startswith("test"):
                self.onTestSyntaxError()
            elif taskType == "allTests":
                self.onSyntaxErrorBestGuess()

        print(f"datastring for process {self.process.processId()}: {datastring.strip()}")
        print(f"error datastring for process {self.process.processId()}: {errorDatastring.strip()}")
        if self.process:
            self.process.close()


    def readStandardOutput(self):
        # In this version, output is processed in handleProcessFinished
        pass

    def readStandardError(self):
        # In this version, errors are processed in handleProcessFinished
        pass

    def handleProcessError(self, error):
        debug(
            f"RunSchemeOperation.handleProcessError: ENTRY - handler called! error={error}")
        debug(f"RunSchemeOperation.handleProcessError: State={self.process.state()}")
        debug(f"RunSchemeOperation.handleProcessError: Error={self.process.error()}")
        debug(
            f"RunSchemeOperation.handleProcessError: ExitCode={self.process.exitCode()}")
        self.finishedSignal.emit(
            self.taskType, f"Process error: {self.process.error()}")
        self.timerUpdateSignal.emit(self.taskType, False) # Timer stops on error
        if self.process:
            self.process.close()


    # --- UI Update Functions (Python version using signals) ---

    def illegalSexpInDefn(self):
        self.statusUpdateSignal.emit(self.taskType, self.ILLEGAL_SEXPR_STRING, self.SYNTAX_ERROR_COLOR)

    def parseErrorInDefn(self):
        self.statusUpdateSignal.emit(self.taskType, self.PARSE_ERROR_STRING, self.PARSE_ERROR_COLOR)
        self.editor_window_controller.cancel_all_operations() # Cancel all tests

    def evaluationFailedInDefn(self): # New function
        self.statusUpdateSignal.emit(self.taskType, self.EVALUATION_FAILED_STRING, self.FAILED_ERROR_COLOR)
        self.editor_window_controller.cancel_all_operations() # Cancel all tests

    def defaultDefnStatus(self):
        self.statusUpdateSignal.emit(self.taskType, "", self.DEFAULT_COLOR) # Clear status, default color

    def thinkingColorAndLabel(self):
        self.statusUpdateSignal.emit(self.taskType, self.THINKING_STRING, self.THINKING_COLOR)

    def onTestCompletion(self, datastring):
        ewc = self.editor_window_controller
        test_num = int(self.taskType[4:]) # Extract test number from "testN"
        input_field = ewc.testInputs[test_num-1]
        output_field = ewc.testExpectedOutputs[test_num-1]
        label = ewc.testStatusLabels[test_num-1]

        if datastring.strip() == "illegal-sexp-in-test/answer":
            self.onTestSyntaxErrorUI(input_field, output_field, label, self.ILLEGAL_SEXPR_STRING, self.SYNTAX_ERROR_COLOR)
            ewc.cancel_all_operations()
        elif datastring.strip() == "parse-error-in-test/answer":
            self.onTestParseErrorUI(input_field, output_field, label, self.PARSE_ERROR_STRING, self.PARSE_ERROR_COLOR)
            ewc.cancel_all_operations()
        elif datastring.strip() in ["illegal-sexp-in-defn", "parse-error-in-defn", "()"]: # Definition errors or eval fail
            self.onTestThinkingUI(input_field, output_field, label, self.THINKING_STRING, self.THINKING_COLOR)
        elif datastring.strip() == "()": # Evaluator query failed!
            self.onTestFailure()
        else: # Parsed, and evaluator query succeeded!
            self.onTestSuccess()


    def onTestSuccess(self):
        ewc = self.editor_window_controller
        test_num = int(self.taskType[4:]) # e.g., from "test1" get 1
        label = ewc.testStatusLabels[test_num-1]
        elapsed_time = time.monotonic() - self.start_time
        status_message = f"Succeeded ({elapsed_time:.2f} s)"
        self.statusUpdateSignal.emit(self.taskType, status_message, self.DEFAULT_COLOR)


    def onTestFailure(self):
        ewc = self.editor_window_controller
        test_num = int(self.taskType[4:])
        label = ewc.testStatusLabels[test_num-1]
        elapsed_time = time.monotonic() - self.start_time
        status_message = f"Failed ({elapsed_time:.2f} s)"
        self.statusUpdateSignal.emit(self.taskType, status_message, self.FAILED_ERROR_COLOR)
        ewc.cancel_all_operations() # Cancel all tests if one fails

    def onTestSyntaxError(self):
        ewc = self.editor_window_controller
        test_num = int(self.taskType[4:])
        label = ewc.testStatusLabels[test_num-1]
        self.onTestSyntaxErrorUI(ewc.testInputs[test_num-1], ewc.testExpectedOutputs[test_num-1], label, self.ILLEGAL_SEXPR_STRING, self.SYNTAX_ERROR_COLOR)


    def onBestGuessSuccess(self, guess):
        ewc = self.editor_window_controller
        elapsed_time = time.monotonic() - self.start_time

        if guess.strip() in ["illegal-sexp-in-defn", "parse-error-in-defn", "illegal-sexp-in-test/answer", "parse-error-in-test/answer"]:
            ewc.updateBestGuess(self.taskType, "") # Clear best guess view
            self.statusUpdateSignal.emit(self.taskType, self.THINKING_STRING, self.THINKING_COLOR) # Thinking color/label
        else:
            ewc.updateBestGuess(self.taskType, guess)
            status_message = f"Succeeded ({elapsed_time:.2f} s)"
            self.statusUpdateSignal.emit(self.taskType, status_message, self.DEFAULT_COLOR)
            ewc.cancel_all_operations() # Cancel other operations if best guess succeeds


    def onBestGuessFailure(self):
        ewc = self.editor_window_controller
        elapsed_time = time.monotonic() - self.start_time
        ewc.updateBestGuess(self.taskType, "") # Clear best guess view
        status_message = f"Failed ({elapsed_time:.2f} s)"
        self.statusUpdateSignal.emit(self.taskType, status_message, self.FAILED_ERROR_COLOR)
        ewc.cancel_all_operations() # Cancel other operations if best guess fails

    def onBestGuessKilled(self):
        ewc = self.editor_window_controller
        ewc.updateBestGuess(self.taskType, "") # Clear best guess view
        self.statusUpdateSignal.emit(self.taskType, "", self.DEFAULT_COLOR) # Clear status, default color


    def onSyntaxErrorBestGuess(self):
        ewc = self.editor_window_controller
        ewc.updateBestGuess(self.taskType, "") # Clear best guess view
        self.statusUpdateSignal.emit(self.taskType, "", self.DEFAULT_COLOR) # Clear status, default color


    # --- UI Helper functions ---
    def onTestSyntaxErrorUI(self, input_field, output_field, label, message, color):
        self.setTestFieldColor(input_field, color)
        self.setTestFieldColor(output_field, color)
        self.setTestLabelStatus(label, message, color)

    def onTestParseErrorUI(self, input_field, output_field, label, message, color):
        self.setTestFieldColor(input_field, color)
        self.setTestFieldColor(output_field, color)
        self.setTestLabelStatus(label, message, color)

    def onTestThinkingUI(self, input_field, output_field, label, message, color):
        self.setTestFieldColor(input_field, color)
        self.setTestFieldColor(output_field, color)
        self.setTestLabelStatus(label, message, color)

    def setTestFieldColor(self, field, color_str):
        field.setStyleSheet(f"color: {color_str};")

    def setTestLabelStatus(self, label, status_str, color_str):
        label.setText(status_str)
        label.setStyleSheet(f"color: {color_str};")