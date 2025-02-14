from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QKeyEvent, QTextCursor, QTextCharFormat, QUndoStack
from PySide6.QtCore import Qt


class SchemeEditorTextView(QTextEdit):
    # List of logic variables to cycle through
    logic_vars = [f",{chr(c)}" for c in range(65, 91)]  # ,A ... ,Z

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setAcceptRichText(False)

        # Set up undo stack
        self.undo_stack = QUndoStack(self)

        # Configure editor settings
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.setTabStopDistance(20)  # Equivalent to 4 spaces

    def keyPressEvent(self, event: QKeyEvent):
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
