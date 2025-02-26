from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QLineEdit


class SchemeEditorLineEdit(QLineEdit):
    """Custom QLineEdit that maintains cursor position during programmatic updates."""

    textEdited = Signal(int, str)

    def __init__(self, parent=None, test_num=None):
        super().__init__(parent)
        self._block_signals = False
        self.test_num = test_num
        self.textEdited.connect(self._on_text_edited)

    @Slot(str)
    def setText(self, text: str):
        """Override setText to preserve cursor position and emit signal."""
        if self.text() == text:
            return

        self._block_signals = True
        cursor_pos = self.cursorPosition()
        super().setText(text)
        self.setCursorPosition(min(cursor_pos, len(text)))
        self._block_signals = False

    @Slot(int, str)
    def _on_text_edited(self, index, text):
        if not self._block_signals:
            self.textEdited.emit(index, text)
