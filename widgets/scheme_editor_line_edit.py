from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QLineEdit


class SchemeEditorLineEdit(QLineEdit):
    """Custom QLineEdit for test inputs/outputs, handling programmatic updates."""

    textChanged = Signal(int, str)

    def __init__(self, parent=None, test_num=None):
        super().__init__(parent)
        self.test_num = test_num
        self._block_signals = False
        self.textEdited.connect(self._on_text_edited)

    @Slot(str)
    def setText(self, text: str):
        """Sets the text, blocking signals to prevent recursion."""
        if self.text() != text:
            self._block_signals = True
            cursor_pos = self.cursorPosition()
            super().setText(text)
            self.setCursorPosition(min(cursor_pos, len(text)))
            self._block_signals = False

    @Slot(str)
    def _on_text_edited(self, text: str):
        """Handles the built-in textEdited signal, emits our custom signal."""
        if not self._block_signals:
            self.textChanged.emit(self.test_num, text)
