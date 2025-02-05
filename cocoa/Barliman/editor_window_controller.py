from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QTextEdit, QLineEdit, QLabel, QVBoxLayout, QGridLayout, QSplitter, QProgressBar
)
from PyQt6.QtGui import QFont, QAction  # Updated: importing QAction from QtGui
from PyQt6.QtCore import QTimer, Qt
import os

class EditorWindowController(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Barliman PyQt6 Port")
        self.setupUI()
        self.setupMenu()  # Initialize main menu based on MainMenu.xib
        self.runCodeTimer = QTimer(self)
        self.runCodeTimer.setSingleShot(True)
        self.runCodeTimer.timeout.connect(self.runCodeFromEditPane)
        self.loadInterpreterCode("interp")
    
    def setupMenu(self):
        menubar = self.menuBar()
        # Application menu (Barliman)
        appMenu = menubar.addMenu("Barliman")
        aboutAction = QAction("About Barliman", self)
        aboutAction.triggered.connect(lambda: print("About Barliman triggered"))
        appMenu.addAction(aboutAction)
        appMenu.addSeparator()
        prefAction = QAction("Preferences…", self)
        prefAction.triggered.connect(lambda: print("Preferences triggered"))
        appMenu.addAction(prefAction)
        appMenu.addSeparator()
        quitAction = QAction("Quit Barliman", self)
        quitAction.triggered.connect(self.close)
        appMenu.addAction(quitAction)
        
        # File menu
        fileMenu = menubar.addMenu("File")
        newAction = QAction("New", self)
        newAction.triggered.connect(lambda: print("New document"))
        fileMenu.addAction(newAction)
        openAction = QAction("Open…", self)
        openAction.triggered.connect(lambda: print("Open document"))
        fileMenu.addAction(openAction)
        fileMenu.addSeparator()
        saveAction = QAction("Save…", self)
        saveAction.triggered.connect(lambda: print("Save document"))
        fileMenu.addAction(saveAction)
        saveAsAction = QAction("Save As…", self)
        saveAsAction.triggered.connect(lambda: print("Save As document"))
        fileMenu.addAction(saveAsAction)
        fileMenu.addSeparator()
        closeAction = QAction("Close", self)
        closeAction.triggered.connect(lambda: print("Close document"))
        fileMenu.addAction(closeAction)
        
        # Edit menu
        editMenu = menubar.addMenu("Edit")
        undoAction = QAction("Undo", self)
        undoAction.triggered.connect(lambda: print("Undo"))
        editMenu.addAction(undoAction)
        redoAction = QAction("Redo", self)
        redoAction.triggered.connect(lambda: print("Redo"))
        editMenu.addAction(redoAction)
        editMenu.addSeparator()
        cutAction = QAction("Cut", self)
        cutAction.triggered.connect(lambda: print("Cut"))
        editMenu.addAction(cutAction)
        copyAction = QAction("Copy", self)
        copyAction.triggered.connect(lambda: print("Copy"))
        editMenu.addAction(copyAction)
        pasteAction = QAction("Paste", self)
        pasteAction.triggered.connect(lambda: print("Paste"))
        editMenu.addAction(pasteAction)
        
        # View menu
        viewMenu = menubar.addMenu("View")
        toggleToolbarAction = QAction("Toggle Toolbar", self)
        toggleToolbarAction.triggered.connect(lambda: print("Toggle Toolbar"))
        viewMenu.addAction(toggleToolbarAction)
        
        # Window menu
        windowMenu = menubar.addMenu("Window")
        minimizeAction = QAction("Minimize", self)
        minimizeAction.triggered.connect(lambda: self.showMinimized())
        windowMenu.addAction(minimizeAction)
        
        # Help menu
        helpMenu = menubar.addMenu("Help")
        helpAction = QAction("Barliman Help", self)
        helpAction.triggered.connect(lambda: print("Barliman Help"))
        helpMenu.addAction(helpAction)
    
    def setupUI(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        default_font = QFont("Monaco", 14)  # Matches Swift defaults

        # Create text views for Scheme Definition and Best Guess.
        self.schemeDefinitionView = QTextEdit(self)
        self.schemeDefinitionView.setPlaceholderText("Enter Scheme definitions...")
        # Update default example text with new examples
        self.schemeDefinitionView.setText(
            "(define ,A\n"
            "  (lambda ,B\n"
            ",C))\n\n"
        )
        self.schemeDefinitionView.setFont(default_font)
        self.bestGuessView = QTextEdit(self)
        self.bestGuessView.setPlaceholderText("Best guess output...")
        self.bestGuessView.setFont(default_font)
        
        # Use QSplitter to simulate the XIB split view (definitionAndBestGuessSplitView)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.schemeDefinitionView)
        splitter.addWidget(self.bestGuessView)
        layout.addWidget(splitter)
        
        # Add progress indicators (spinners) as per Swift/XIB details
        self.schemeDefinitionSpinner = QProgressBar(self)
        self.schemeDefinitionSpinner.setRange(0, 0)  # Indeterminate state
        self.bestGuessSpinner = QProgressBar(self)
        self.bestGuessSpinner.setRange(0, 0)
        layout.addWidget(QLabel("Scheme Definition Progress:"))
        layout.addWidget(self.schemeDefinitionSpinner)
        layout.addWidget(QLabel("Best Guess Progress:"))
        layout.addWidget(self.bestGuessSpinner)
        
        # Create test fields and labels (6 sets) as in Swift's outlets.
        self.testInputs = [QLineEdit(self) for _ in range(6)]
        self.testExpectedOutputs = [QLineEdit(self) for _ in range(6)]
        self.testStatusLabels = [QLabel("", self) for _ in range(6)]
        for field in self.testInputs + self.testExpectedOutputs:
            field.setFont(default_font)
        
        # Pre-populate default examples for test fields
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
        for i, field in enumerate(self.testInputs):
            field.setText(default_test_inputs[i])
        for i, field in enumerate(self.testExpectedOutputs):
            field.setText(default_test_expected[i])
        
        grid = QGridLayout()
        for i in range(6):
            grid.addWidget(QLabel(f"Test {i+1}:"), i, 0)
            grid.addWidget(self.testInputs[i], i, 1)
            grid.addWidget(self.testExpectedOutputs[i], i, 2)
            grid.addWidget(self.testStatusLabels[i], i, 3)
            self.testInputs[i].textChanged.connect(self.setupRunCodeFromEditPaneTimer)
            self.testExpectedOutputs[i].textChanged.connect(self.setupRunCodeFromEditPaneTimer)
        layout.addLayout(grid)
        
        # Connect changes in the Scheme Definition to trigger code execution (similar to text delegate methods)
        self.schemeDefinitionView.textChanged.connect(self.setupRunCodeFromEditPaneTimer)
        # ...existing UI customization...
    
    def loadInterpreterCode(self, interpFileName: str):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, "mk-and-rel-interp", f"{interpFileName}.scm")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.interpreter_code = f.read()
        except Exception as e:
            print("Error loading interpreter code:", e)
            self.interpreter_code = ""
    
    def runCodeFromEditPane(self):
        print("Running code from edit pane...")
        # Process each test field; update status accordingly
        for i in range(6):
            if self.testInputs[i].text() and self.testExpectedOutputs[i].text():
                self.testStatusLabels[i].setText("Running")
            else:
                self.testStatusLabels[i].setText("Skipped")
        # ...existing code to process tests and run operations...
        QTimer.singleShot(500, self.finishRun)
    
    def finishRun(self):
        for label in self.testStatusLabels:
            if label.text() == "Running":
                label.setText("Done")
        print("Finished processing tests.")
    
    def setupRunCodeFromEditPaneTimer(self):
        if self.runCodeTimer.isActive():
            self.runCodeTimer.stop()
        self.runCodeTimer.start(1000)
        # ...existing code...

    def cleanup(self):
        if self.runCodeTimer.isActive():
            self.runCodeTimer.stop()
        # ...additional cleanup as needed...
        print("Cleanup complete.")
