from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLineEdit


class SchemeEditorLineEdit(QLineEdit):
    """Custom QLineEdit that maintains cursor position during programmatic updates."""

    textModified = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._block_signals = False
        self.textChanged.connect(self._on_text_changed)

    def setText(self, text: str):
        """Override setText to preserve cursor position."""
        if self.text() == text:
            return

        self._block_signals = True
        cursor_pos = self.cursorPosition()
        super().setText(text)
        self.setCursorPosition(min(cursor_pos, len(text)))
        self._block_signals = False

    def _on_text_changed(self, text: str):
        """Handle text changes and emit our custom signal."""
        if not self._block_signals:
            self.textModified.emit(text)
