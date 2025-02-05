from PyQt6.QtWidgets import QTextEdit

class SchemeEditorTextView(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Disable rich text to simulate "smart quotes" being off
        self.setAcceptRichText(False)
        # ...existing code for additional customizations...
