from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QKeyEvent, QUndoStack
from PySide6.QtWidgets import QTextEdit


class SchemeEditorTextEdit(QTextEdit):
    # List of logic variables to cycle through
    logic_vars = [f",{chr(c)}" for c in range(65, 91)]  # ,A ... ,Z
    textChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAcceptRichText(False)
        self.undo_stack = QUndoStack(self)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.setTabStopDistance(20)  # Equivalent to 4 spaces
        self._block_text_changed_signal = False

    @Slot(QKeyEvent)
    def keyPressEvent(self, event: QKeyEvent):
        self.setUpdatesEnabled(False)

        if (
            event.modifiers() == Qt.KeyboardModifier.ControlModifier
            and event.key() == Qt.Key.Key_Space
        ):
            if var_to_insert := self.findNextUnusedLogicVar():
                self._insert_gensym(var_to_insert)
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

        self.setUpdatesEnabled(True)
        if not self._block_text_changed_signal:
            self.textChanged.emit(self.toPlainText())

    @Slot(str)
    def _insert_gensym(self, var_to_insert):
        cursor = self.textCursor()
        current_pos = cursor.position()
        cursor.beginEditBlock()
        cursor.insertText(var_to_insert)
        cursor.endEditBlock()
        cursor.setPosition(current_pos + len(var_to_insert))
        self.setTextCursor(cursor)

    @Slot()
    def findNextUnusedLogicVar(self) -> str:
        current_text = self.toPlainText()
        return next((lv for lv in self.logic_vars if lv not in current_text), "")

    @Slot()
    def canUndo(self) -> bool:
        return self.document().isUndoAvailable()

    @Slot()
    def canRedo(self) -> bool:
        return self.document().isRedoAvailable()

    @Slot()
    def insertFromMimeData(self, source):
        if source.hasText():
            text = source.text()
            text = text.replace("\t", "    ")
            cursor = self.textCursor()
            cursor.insertText(text)
        else:
            super().insertFromMimeData(source)

    @Slot(str)
    def setPlainText(self, text: str):
        self._block_text_changed_signal = True
        old_cursor_pos = self.textCursor().position()
        super().setPlainText(text)
        cursor = self.textCursor()
        cursor.setPosition(old_cursor_pos)
        self.setTextCursor(cursor)
        self._block_text_changed_signal = False
