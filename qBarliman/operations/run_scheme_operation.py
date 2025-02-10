import os
import signal
import shutil
import time
import traceback
from dataclasses import dataclass
from typing import Optional, Any, cast, Protocol, List
from PySide6.QtCore import QObject, QRunnable, Signal, QProcess, Slot, Qt, QTimer, QMetaObject
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QTextEdit, QLineEdit, QLabel
from qBarliman.constants import *

@dataclass
class ProcessResult:
    output: str
    error: str
    exit_code: int
    crashed: bool

class EditorWindowInterface(Protocol):
    """Protocol defining required editor window interface"""
    def cancel_all_operations(self) -> None: ...
    def cleanup(self) -> None: ...
    def updateBestGuess(self, taskType: str, output: str) -> None: ...
    @property
    def schemeDefinitionView(self) -> QTextEdit: ...
    @property
    def bestGuessView(self) -> QTextEdit: ...
    @property
    def testInputs(self) -> List[QLineEdit]: ...
    @property
    def testExpectedOutputs(self) -> List[QLineEdit]: ...
    @property
    def testStatusLabels(self) -> List[QLabel]: ...

class RunSchemeOperation(QObject, QRunnable):
    """Operation that executes a scheme process"""

    # Signals
    finishedSignal = Signal(str, str)  # (taskType, output)
    statusUpdateSignal = Signal(str, str, str)  # (taskType, status, color)
    timerUpdateSignal = Signal(str, bool)  # (taskType, isRunning)

    # UI Status strings
    ILLEGAL_SEXPR_STRING = "Illegal sexpression"
    PARSE_ERROR_STRING = "Syntax error"
    EVALUATION_FAILED_STRING = "Evaluation failed"
    THINKING_STRING = "???"

    def __init__(self, editor_window_controller: EditorWindowInterface, schemeScriptPathString: str, taskType: str):
        QObject.__init__(self)
        QRunnable.__init__(self)
        self.editor_window_controller = editor_window_controller
        self.schemeScriptPathString = schemeScriptPathString
        self.taskType = taskType
        self.task: Optional[QProcess] = None
        self.start_time = time.monotonic()
        
        # Initialize output buffers
        self._stdout_data = bytearray()
        self._stderr_data = bytearray()
        self._killed = False
        self._interrupted = False
        self._process_result: Optional[ProcessResult] = None

        # Define colors once using Qt's color constants
        self.colors = {
            'default': QColor(Qt.GlobalColor.black),
            'syntax_error': QColor(Qt.GlobalColor.darkYellow),
            'parse_error': QColor(Qt.GlobalColor.yellow),
            'failed': QColor(Qt.GlobalColor.red),
            'thinking': QColor(Qt.GlobalColor.magenta)
        }

    def requestInterruption(self) -> None:
        """Request operation interruption"""
        self._interrupted = True

    def isInterruptionRequested(self) -> bool:
        """Check if interruption was requested"""
        return self._interrupted

    def isRunning(self) -> bool:
        """Check if operation is running"""
        return not self._killed and not self._interrupted

    def run(self) -> None:
        """Execute the scheme process"""
        if self.isInterruptionRequested():
            debug("*** cancelled immediately! ***")
            return

        try:
            self._stdout_data.clear()
            self._stderr_data.clear()
            self.start_time = time.monotonic()
            
            self._update_thinking_state()
            self.timerUpdateSignal.emit(self.taskType, True)

            self._setup_process()
            self._launch_process()
        except KeyboardInterrupt:
            debug("Received keyboard interrupt in run method")
            self._graceful_shutdown()
        except Exception as e:
            warn(f"Error in run method: {e}")
            debug(f"Traceback: {traceback.format_exc()}")
            self.handle_process_error(QProcess.ProcessError.FailedToStart)

    def _update_thinking_state(self) -> None:
        """Update UI elements to show thinking state"""
        self.statusUpdateSignal.emit(self.taskType, self.THINKING_STRING, self.colors['thinking'].name())

    def _graceful_shutdown(self) -> None:
        """Perform graceful shutdown operations"""
        try:
            self.editor_window_controller.cancel_all_operations()
            if self.task and self.task.state() != QProcess.ProcessState.NotRunning:
                self.capture_remaining_output()
                self._terminate_process()
            self.cleanupProcess()
        except Exception as e:
            warn(f"Error during graceful shutdown: {e}")
            debug(f"Traceback: {traceback.format_exc()}")
        finally:
            self.requestInterruption()

    def _setup_process(self) -> None:
        """Configure the QProcess for scheme execution"""
        # Clean up any existing process first
        if self.task:
            self.cleanupProcess()
            
        # Create process with proper parent
        self.task = QProcess(self)
        
        # Set up process configuration
        self.task.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        self.task.setInputChannelMode(QProcess.InputChannelMode.ManagedInputChannel)
        self.task.setWorkingDirectory(os.path.dirname(self.schemeScriptPathString))
        
        # Set process environment if needed
        env = QProcess.systemEnvironment()
        self.task.setEnvironment(env)
        
        # Connect signals using direct connections for better error handling
        self.task.finished.connect(self.handleProcessFinished, Qt.ConnectionType.DirectConnection)
        self.task.errorOccurred.connect(self.handle_process_error, Qt.ConnectionType.DirectConnection)
        self.task.readyReadStandardOutput.connect(self._handle_stdout, Qt.ConnectionType.DirectConnection)
        self.task.readyReadStandardError.connect(self._handle_stderr, Qt.ConnectionType.DirectConnection)
        
        # Set process state
        self.task.setProcessState(QProcess.ProcessState.NotRunning)

    def _verify_scheme_executable(self) -> bool:
        """Verify that the scheme executable exists and is accessible"""
        if not SCHEME_EXECUTABLE:
            warn("!!! SCHEME_EXECUTABLE not set")
            return False
            
        scheme_path = shutil.which(SCHEME_EXECUTABLE)
        if not scheme_path:
            warn(f"!!! Could not find {SCHEME_EXECUTABLE} in PATH")
            return False
            
        if not os.access(scheme_path, os.X_OK):
            warn(f"!!! {scheme_path} is not executable")
            return False
            
        good(f"Found Scheme executable at: {scheme_path}")  # Changed to good() for consistency
        return True

    def _launch_process(self) -> None:
        """Launch the scheme process with proper error recovery"""
        try:
            info("*** launching Scheme process")
            
            # Verify scheme executable and get its full path
            if not self._verify_scheme_executable():
                self._handle_process_error(QProcess.ProcessError.FailedToStart)
                return
                
            scheme_path = shutil.which(SCHEME_EXECUTABLE)
            if not scheme_path:  # Double check path
                warn("Scheme path is None after verification")
                self._handle_process_error(QProcess.ProcessError.FailedToStart)
                return
                
            debug(f"*** launchPath: {scheme_path}")
            debug(f"*** arguments: ['{self.schemeScriptPathString}']")

            # Verify script file exists
            if not os.path.exists(self.schemeScriptPathString):
                warn(f"!!! Script file not found: {self.schemeScriptPathString}")
                self._handle_process_error(QProcess.ProcessError.FailedToStart)
                return
                
            # Set up fresh process
            self._setup_process()
            if not self.task:
                warn("!!! Failed to create QProcess")
                self._handle_process_error(QProcess.ProcessError.FailedToStart)
                return

            # Set up process recovery timer
            recovery_timer = QTimer(self)
            recovery_timer.setSingleShot(True)
            recovery_timer.timeout.connect(self._handle_process_stall)
            recovery_timer.start(5000)  # 5 second timeout
            
            # Start process
            args = ["--script", self.schemeScriptPathString]
            debug(f"Starting process with args: {args}")
            self.task.start(scheme_path, args)
            
            if not self.task.waitForStarted(3000):
                warn("!!! Process failed to start within timeout")
                self._handle_process_error(QProcess.ProcessError.FailedToStart)
                return
            
            recovery_timer.stop()
            
            pid = self.task.processId()
            if pid:
                good(f"*** launched process {pid}")
                # Set up stall detection
                stall_timer = QTimer(self)
                stall_timer.timeout.connect(self._check_process_responsive)
                stall_timer.start(2000)  # Check every 2 seconds
            else:
                warn("!!! Process started but no PID obtained")
                
            if self.taskType == "simple" and not self.waitForSchemeProcess():
                warn("!!! Process timed out")
                self._handle_process_error(QProcess.ProcessError.Timedout)

        except Exception as e:
            warn(f"!!! Error launching process: {e}")
            debug(f"Traceback: {traceback.format_exc()}")
            self._handle_process_error(QProcess.ProcessError.FailedToStart)

    @Slot()
    def _handle_process_stall(self):
        """Handle case where process appears to be stalled"""
        if not self.task:
            return
            
        warn("Process appears to be stalled during startup")
        self._handle_process_error(QProcess.ProcessError.Timedout)

    @Slot()
    def _check_process_responsive(self):
        """Check if process is still responsive"""
        if not self.task or not self._is_process_running():
            return
            
        try:
            pid = self.task.processId()
            if pid:
                # On Unix systems, sending signal 0 tests process existence
                if os.name == 'posix':
                    try:
                        os.kill(pid, 0)
                    except ProcessLookupError:
                        warn(f"Process {pid} no longer exists")
                        self._handle_process_error(QProcess.ProcessError.Crashed)
                    except PermissionError:
                        warn(f"Process {pid} exists but we can't access it")
                        self._handle_process_error(QProcess.ProcessError.UnknownError)
                elif self.task.state() == QProcess.ProcessState.NotRunning:
                    warn(f"Process {pid} is not running")
                    self._handle_process_error(QProcess.ProcessError.Crashed)
        except Exception as e:
            warn(f"Error checking process responsiveness: {e}")
            debug(f"Traceback: {traceback.format_exc()}")

    def waitForSchemeProcess(self, timeout: int = 30000) -> bool:
        """Wait for the scheme process to complete with timeout"""
        if self._is_process_running() and self.task:
            return self.task.waitForFinished(timeout)
        return True

    @Slot()
    def _handle_stdout(self) -> None:
        """Handle stdout data safely using Qt's object system"""
        if not self.task or self._killed:
            return
        try:
            data = self.task.readAllStandardOutput().data()
            if data:
                # Use invokeMethod for thread-safe updates
                QMetaObject.invokeMethod(
                    self,
                    "_append_stdout",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(bytes, data)
                )
        except Exception as e:
            warn(f"Error handling stdout: {e}")

    @Slot()
    def _handle_stderr(self) -> None:
        """Handle stderr data safely using Qt's object system"""
        if not self.task or self._killed:
            return
        try:
            data = self.task.readAllStandardError().data()
            if data:
                # Use invokeMethod for thread-safe updates
                QMetaObject.invokeMethod(
                    self,
                    "_append_stderr",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(bytes, data)
                )
        except Exception as e:
            warn(f"Error handling stderr: {e}")

    @Slot(bytes)
    def _append_stdout(self, data: bytes):
        """Thread-safe stdout append"""
        if not self._killed:
            self._stdout_data.extend(data)

    @Slot(bytes)
    def _append_stderr(self, data: bytes):
        """Thread-safe stderr append"""
        if not self._killed:
            self._stderr_data.extend(data)

    @Slot()
    def handleProcessFinished(self) -> None:
        """Handle process completion with Qt's event system"""
        if not self.task:
            return
            
        try:
            # Capture process info before cleanup
            exit_code = self.task.exitCode()
            crash_signal = self.task.exitStatus() == QProcess.ExitStatus.CrashExit
            
            # Use invokeMethod for thread-safe updates
            QMetaObject.invokeMethod(
                self,
                "_handle_completion",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(int, exit_code),
                Q_ARG(bool, crash_signal)
            )

        except Exception as e:
            warn(f"Error in process completion handler: {e}")
            debug(f"Traceback: {traceback.format_exc()}")
        finally:
            self.cleanupProcess()

    @Slot(int, bool)
    def _handle_completion(self, exit_code: int, crash_signal: bool):
        """Thread-safe completion handling"""
        self.capture_remaining_output()

        output = self._stdout_data.decode().strip() if self._stdout_data else ""
        error = self._stderr_data.decode().strip() if self._stderr_data else ""

        debug(f"datastring: {output}")
        if error:
            warn(f"error datastring: {error}")

        self.timerUpdateSignal.emit(self.taskType, False)

        if crash_signal:
            warn("Process crashed")
            self._handle_process_error(QProcess.ProcessError.Crashed)
        elif exit_code == 0:
            self._handle_successful_completion(output)
        elif exit_code == 15:  # SIGTERM
            self._handle_termination()
        else:
            warn(f"Process exited with code {exit_code}")
            self._handle_failed_completion()

    def _handle_successful_completion(self, output: str):
        """Handle successful process completion"""
        if self.taskType == "simple":
            self._handle_simple_completion(output)
        elif self.taskType.startswith("test"):
            self._handle_test_completion(output)
        elif self.taskType == "allTests":
            self._handle_alltest_completion(output)

    def _handle_simple_completion(self, output: str):
        """Handle completion of simple evaluation task"""
        if output == "parse-error-in-defn":
            self._update_simple_ui(self.PARSE_ERROR_STRING, self.colors['parse_error'])
        elif output == "illegal-sexp-in-defn":
            self._update_simple_ui(self.ILLEGAL_SEXPR_STRING, self.colors['syntax_error'])
        elif output == "()":
            self._update_simple_ui(self.EVALUATION_FAILED_STRING, self.colors['failed'])
        else:
            self._update_simple_ui("", self.colors['default'])

    def _update_simple_ui(self, status: str, color: QColor):
        """Update UI for simple task completion"""
        self.statusUpdateSignal.emit(self.taskType, status, color.name())
        if hasattr(self.editor_window_controller, 'schemeDefinitionView'):
            self.editor_window_controller.schemeDefinitionView.setStyleSheet(
                f"color: {color.name()};")
        if status in [self.ILLEGAL_SEXPR_STRING, self.PARSE_ERROR_STRING, self.EVALUATION_FAILED_STRING]:
            self.editor_window_controller.cancel_all_operations()

    def _handle_test_completion(self, output: str):
        """Handle completion of test task"""
        try:
            test_num = int(self.taskType[4:])
            if 1 <= test_num <= len(self.editor_window_controller.testInputs):
                test_index = test_num - 1
                elapsed_time = time.monotonic() - self.start_time

                if output in ["illegal-sexp-in-test/answer", "parse-error-in-test/answer"]:
                    self._handle_test_syntax_error(test_index)
                elif output in ["illegal-sexp-in-defn", "parse-error-in-defn"]:
                    self._handle_test_thinking(test_index)
                elif output == "()":
                    self._handle_test_failure(test_index, elapsed_time)
                else:
                    self._handle_test_success(test_index, elapsed_time)
        except ValueError:
            print(f"!!!!!!!!!! ERROR: invalid test number in taskType: {self.taskType}")

    def _handle_test_syntax_error(self, test_index: int):
        """Handle syntax error in test"""
        self._update_test_ui(
            test_index,
            self.colors['syntax_error'],
            self.ILLEGAL_SEXPR_STRING
        )
        self.editor_window_controller.cancel_all_operations()

    def _handle_test_thinking(self, test_index: int):
        """Handle thinking state in test"""
        self._update_test_ui(
            test_index,
            self.colors['thinking'],
            self.THINKING_STRING
        )

    def _handle_test_failure(self, test_index: int, elapsed_time: float):
        """Handle test failure"""
        status = f"Failed ({elapsed_time:.2f} s)"
        self._update_test_ui(
            test_index,
            self.colors['failed'],
            status
        )
        self.editor_window_controller.cancel_all_operations()

    def _handle_test_success(self, test_index: int, elapsed_time: float):
        """Handle test success"""
        status = f"Succeeded ({elapsed_time:.2f} s)"
        self._update_test_ui(
            test_index,
            self.colors['default'],
            status
        )

    def _handle_alltest_completion(self, output: str):
        """Handle completion of allTests task"""
        elapsed_time = time.monotonic() - self.start_time
        ewc = self.editor_window_controller

        if output == "fail":
            self._handle_best_guess_failure(elapsed_time)
        elif output in ["illegal-sexp-in-defn", "parse-error-in-defn",
                       "illegal-sexp-in-test/answer", "parse-error-in-test/answer"]:
            self._handle_best_guess_thinking()
        else:
            self._handle_best_guess_success(output, elapsed_time)

    def _handle_best_guess_failure(self, elapsed_time: float):
        """Handle best guess failure"""
        self.editor_window_controller.updateBestGuess(self.taskType, "")
        status = f"Failed ({elapsed_time:.2f} s)"
        self.statusUpdateSignal.emit(self.taskType, status, self.colors['failed'].name())
        self.editor_window_controller.cancel_all_operations()

    def _handle_best_guess_thinking(self):
        """Handle best guess thinking state"""
        self.editor_window_controller.updateBestGuess(self.taskType, "")
        self.statusUpdateSignal.emit(self.taskType, self.THINKING_STRING, self.colors['thinking'].name())

    def _handle_best_guess_success(self, guess: str, elapsed_time: float):
        """Handle best guess success"""
        self.editor_window_controller.updateBestGuess(self.taskType, guess)
        self._set_best_guess_font()
        status = f"Succeeded ({elapsed_time:.2f} s)"
        self.statusUpdateSignal.emit(self.taskType, status, self.colors['default'].name())
        self.editor_window_controller.cancel_all_operations()

    def _set_best_guess_font(self):
        """Set the font for best guess view"""
        if hasattr(self.editor_window_controller, 'bestGuessView'):
            view = self.editor_window_controller.bestGuessView
            font = view.font()
            font.setFamily("Lucida Console")
            font.setPointSize(12)
            view.setFont(font)

    def _handle_termination(self):
        """Handle process termination"""
        debug(f"SIGTERM !!! taskType = {self.taskType}")
        
        if self.taskType == "allTests":
            self.editor_window_controller.updateBestGuess(self.taskType, "")
            self.statusUpdateSignal.emit(self.taskType, "", self.colors['default'].name())
        elif self.taskType.startswith("test"):
            # Individual tests succeed when killed by allTests success
            self._handle_test_success(int(self.taskType[4:]) - 1, time.monotonic() - self.start_time)

    def _handle_failed_completion(self):
        """Handle failed process completion"""
        if self.task:
            warn(f"exitStatus = {self.task.exitCode()}")
            if self.taskType == "simple":
                self._update_simple_ui(self.ILLEGAL_SEXPR_STRING, self.colors['syntax_error'])
            elif self.taskType.startswith("test"):
                test_num = int(self.taskType[4:])
                self._handle_test_syntax_error(test_num - 1)
            elif self.taskType == "allTests":
                self.editor_window_controller.updateBestGuess(self.taskType, "")
                self.statusUpdateSignal.emit(self.taskType, "", self.colors['default'].name())

    def cleanupProcess(self) -> None:
        """Clean up process resources using Qt's object hierarchy"""
        try:
            if self.task:
                task = self.task
                self.task = None
                
                if task.state() != QProcess.ProcessState.NotRunning:
                    debug("Cleaning up running process...")
                    self.capture_remaining_output()
                    self._terminate_process()
                
                task.close()
                # Let Qt's parent-child relationship handle deletion
                task.setParent(None)
                task.deleteLater()
                good("Process cleaned up successfully")
        except Exception as e:
            warn(f"Error during process cleanup: {e}")
            debug(f"Traceback: {traceback.format_exc()}")
        finally:
            self.task = None

    def _terminate_process(self) -> None:
        """Use Qt's built-in process management"""
        if not self.task:
            return
            
        try:
            pid = self.task.processId()
            if not pid:
                return
                
            debug(f"Attempting to terminate process {pid}")
            
            # Use Qt's built-in termination
            self.task.terminate()
            if not self.task.waitForFinished(1000):
                warn(f"Process {pid} didn't terminate gracefully, forcing kill")
                self.task.kill()
                
                # Let the event loop process the kill
                if not QThread.msleep(100) or not self.task.waitForFinished(1000):
                    warn(f"Process {pid} didn't respond to kill")
                    if os.name == 'posix':
                        try:
                            os.kill(pid, signal.SIGKILL)
                            debug(f"Sent SIGKILL to process {pid}")
                        except ProcessLookupError:
                            debug(f"Process {pid} already gone")
                        except Exception as e:
                            warn(f"Failed to force kill process {pid}: {e}")
                else:
                    debug(f"Process {pid} killed successfully")
            else:
                debug(f"Process {pid} terminated gracefully")
                
        except Exception as e:
            warn(f"Error terminating process: {e}")
            debug(f"Traceback: {traceback.format_exc()}")
        finally:
            self.capture_remaining_output()

    def capture_remaining_output(self) -> None:
        """Capture any remaining stdout/stderr data"""
        if not self.task:
            return
            
        try:
            if self.task.bytesAvailable():
                self._stdout_data.extend(self.task.readAllStandardOutput().data())
            stderr_bytes = self.task.readAllStandardError()
            if not stderr_bytes.isEmpty():
                self._stderr_data.extend(stderr_bytes.data())
        except Exception as e:
            warn(f"Error capturing output: {e}")
            debug(f"Traceback: {traceback.format_exc()}")

    @Slot(QProcess.ProcessError)
    def handle_process_error(self, error: QProcess.ProcessError) -> None:
        """Handle QProcess errors with strong typing"""
        if self._killed:
            return
            
        try:
            error_messages = {
                QProcess.ProcessError.FailedToStart: "Process failed to start. Check if Scheme is installed.",
                QProcess.ProcessError.Crashed: "Process crashed.",
                QProcess.ProcessError.Timedout: "Process timed out.",
                QProcess.ProcessError.WriteError: "Error writing to process.",
                QProcess.ProcessError.ReadError: "Error reading from process.",
                QProcess.ProcessError.UnknownError: "Unknown process error."
            }
            
            error_msg = error_messages.get(error, "Process error occurred")
            warn(f"!!! Process error: {error_msg}")
            
            QMetaObject.invokeMethod(
                self,
                "_emit_error_signals",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, error_msg)
            )
            
            if error not in [QProcess.ProcessError.WriteError, QProcess.ProcessError.ReadError]:
                QMetaObject.invokeMethod(
                    self.editor_window_controller,
                    "cancel_all_operations",
                    Qt.ConnectionType.QueuedConnection
                )
        except Exception as e:
            warn(f"Error handling process error: {e}")
            debug(f"Traceback: {traceback.format_exc()}")

    @Slot(str)
    def _emit_error_signals(self, error_msg: str) -> None:
        """Thread-safe error signal emission"""
        if not self._killed:
            self.statusUpdateSignal.emit(self.taskType, error_msg, self.colors['failed'].name())
            self.timerUpdateSignal.emit(self.taskType, False)

    def _store_process_result(self, output: str, error: str, exit_code: int, crashed: bool) -> None:
        """Thread-safe process result storage"""
        self._process_result = ProcessResult(
            output=output,
            error=error,
            exit_code=exit_code,
            crashed=crashed
        )
