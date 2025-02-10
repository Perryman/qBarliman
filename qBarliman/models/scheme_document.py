from typing import Optional, List
from PySide6.QtCore import QObject, Signal, Property


class SchemeDocument(QObject):
    """Model representing a Scheme document with definition and test cases"""

    definitionTextChanged = Signal(str)
    testCasesChanged = Signal(list, list)  # Emits test_inputs and test_expected
    statusChanged = Signal(str)  # Emits current evaluation status

    def __init__(
        self,
        definition_text: str = "",
        test_inputs: Optional[List[str]] = None,
        test_expected: Optional[List[str]] = None,
    ):
        super().__init__()
        self._definition_text = definition_text
        self._test_inputs = test_inputs if test_inputs is not None else [""] * 6
        self._test_expected = test_expected if test_expected is not None else [""] * 6
        self._status = ""
        self._is_valid = True

    @Property(str, notify=definitionTextChanged)
    def definition_text(self) -> str:
        """The main Scheme definition text"""
        return self._definition_text

    @definition_text.setter
    def definition_text(self, value: str) -> None:
        if value != self._definition_text:
            self._definition_text = value
            self.definitionTextChanged.emit(value)

    @Property(list, notify=testCasesChanged)
    def test_inputs(self) -> List[str]:
        """Test input cases"""
        return self._test_inputs.copy()

    @Property(list, notify=testCasesChanged)
    def test_expected(self) -> List[str]:
        """Expected test outputs"""
        return self._test_expected.copy()

    @Property(str, notify=statusChanged)
    def status(self) -> str:
        """Current evaluation status"""
        return self._status

    @status.setter
    def set_status(self, value: str) -> None:
        if value != self._status:
            self._status = value
            self.statusChanged.emit(value)

    @Property(bool)
    def is_valid(self) -> bool:
        """Whether the current Scheme code is valid"""
        return self._is_valid

    def setTestInput(self, test_number: int, value: str) -> None:
        """Set a specific test input"""
        if 1 <= test_number <= len(self._test_inputs):
            if self._test_inputs[test_number - 1] != value:
                self._test_inputs[test_number - 1] = value
                self.testCasesChanged.emit(
                    self._test_inputs.copy(), self._test_expected.copy()
                )

    def setTestExpected(self, test_number: int, value: str) -> None:
        """Set a specific test expected output"""
        if 1 <= test_number <= len(self._test_expected):
            if self._test_expected[test_number - 1] != value:
                self._test_expected[test_number - 1] = value
                self.testCasesChanged.emit(
                    self._test_inputs.copy(), self._test_expected.copy()
                )

    def updateTests(self, inputs: List[str], expected: List[str]) -> None:
        """Update all test cases at once"""
        if inputs != self._test_inputs or expected != self._test_expected:
            self._test_inputs = inputs.copy()
            self._test_expected = expected.copy()
            self.testCasesChanged.emit(self._test_inputs, self._test_expected)

    def validate(self) -> bool:
        """Validate the current Scheme code and test cases"""
        # Basic validation - could be extended with more sophisticated checks
        self._is_valid = bool(self._definition_text.strip())
        return self._is_valid
