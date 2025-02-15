from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QUndoStack
from PySide6.QtWidgets import QTextEdit


class SchemeEditorTextView(QTextEdit):
    # List of logic variables to cycle through
    logic_vars = [f",{chr(c)}" for c in range(65, 91)]  # ,A ... ,Z
    codeTextChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setAcceptRichText(False)

        # Set up undo stack
        self.undo_stack = QUndoStack(self)

        # Configure editor settings
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.setTabStopDistance(20)  # Equivalent to 4 spaces
        self._block_text_changed_signal = False  # Add flag to block signal emission

    def keyPressEvent(self, event: QKeyEvent):
        # Disable listener while proessing key event
        self.setUpdatesEnabled(False)

        # Detect Control+Space
        if (
            event.modifiers() == Qt.KeyboardModifier.ControlModifier
            and event.key() == Qt.Key.Key_Space
        ):
            var_to_insert = self.findNextUnusedLogicVar()
            if var_to_insert:
                cursor = self.textCursor()
                # Insert with undo support
                cursor.beginEditBlock()
                cursor.insertText(var_to_insert)
                cursor.endEditBlock()
                self.setTextCursor(cursor)
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

        # Re-enable listener and emit signal if not blocked
        self.setUpdatesEnabled(True)
        if not self._block_text_changed_signal:
            self.codeTextChanged.emit(self.toPlainText())

    def findNextUnusedLogicVar(self) -> str:
        current_text = self.toPlainText()
        for lv in self.logic_vars:
            if lv not in current_text:
                return lv
        return ""  # If all variables are used, return empty string

    def canUndo(self) -> bool:
        return self.document().isUndoAvailable()

    def canRedo(self) -> bool:
        return self.document().isRedoAvailable()

    # Ensure tab behavior matches the original
    def insertFromMimeData(self, source):
        # Convert tabs to spaces on paste
        if source.hasText():
            text = source.text()
            text = text.replace("\t", "    ")
            cursor = self.textCursor()
            cursor.insertText(text)
        else:
            super().insertFromMimeData(source)

    def setPlainText(self, text: str, cursor_pos=None):
        """Override setPlainText to preserve cursor and emit signal."""
        self._block_text_changed_signal = True  # Block signal before change
        old_cursor_pos = self.textCursor().position()
        super().setPlainText(text)
        if cursor_pos is not None:
            cursor = self.textCursor()  # Get the current cursor
            cursor.setPosition(cursor_pos)  # Set the position
            self.setTextCursor(cursor)  # Apply the modified cursor
        else:
            cursor = self.textCursor()  # Get the current cursor
            cursor.setPosition(old_cursor_pos)  # Restore old position
            self.setTextCursor(cursor)  # Apply the modified cursor
        self._block_text_changed_signal = False  # Re-enable signal
