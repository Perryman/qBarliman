from PySide6.QtCore import QObject, Signal, Property

class SchemeDocument(QObject):
    definitionTextChanged = Signal(str)
    testCasesChanged = Signal(list, list)  # Emits test_inputs and test_expected

    def __init__(self, definition_text: str = "", test_inputs: list[str] = None, test_expected: list[str] = None):
        super().__init__()
        self._definition_text = definition_text
        self._test_inputs = test_inputs if test_inputs is not None else [""] * 6
        self._test_expected = test_expected if test_expected is not None else [""] * 6

    @Property(str, notify=definitionTextChanged)
    def get_definitionText(self):
        return self._definition_text

    @get_definitionText.setter
    def set_definitionText(self, value: str):
        self._definition_text = value
        self.definitionTextChanged.emit(value)

    @Property(list, notify=testCasesChanged)
    def get_testInputs(self):
        return self._test_inputs.copy()

    @Property(list, notify=testCasesChanged)
    def get_testExpected(self):
        return self._test_expected.copy()

    def setTestInput(self, test_number: int, value: str):
        if 1 <= test_number <= len(self._test_inputs):
            self._test_inputs[test_number - 1] = value
            self.testCasesChanged.emit(self._test_inputs.copy(), self._test_expected.copy())

    def setTestExpected(self, test_number: int, value: str):
        if 1 <= test_number <= len(self._test_expected):
            self._test_expected[test_number - 1] = value
            self.testCasesChanged.emit(self._test_inputs.copy(), self._test_expected.copy())

    def updateTests(self, inputs: list[str], expected: list[str]):
        self._test_inputs = inputs.copy()
        self._test_expected = expected.copy()
        self.testCasesChanged.emit(self._test_inputs, self._test_expected)
