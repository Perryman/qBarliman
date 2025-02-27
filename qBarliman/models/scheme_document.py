from typing import List, Optional

from PySide6.QtCore import QObject, Signal

from qBarliman.utils import log as l

from ..constants import (
    DEFAULT_DEFINITIONS,
    DEFAULT_TEST_EXPECTED_OUTPUTS,
    DEFAULT_TEST_INPUTS,
)
from .scheme_document_data import SchemeDocumentData


class SchemeDocument(QObject):
    """QObject wrapper around an immutable SchemeDocumentData."""

    # Signals for changes.
    definitionTextChanged = Signal(str)
    testCasesChanged = Signal(list, list)
    statusChanged = Signal(str)

    def __init__(
        self,
        definition_text: str = "\n".join(DEFAULT_DEFINITIONS),
        test_inputs: Optional[List[str]] = None,
        test_expected: Optional[List[str]] = None,
    ):
        super().__init__()
        self._data = SchemeDocumentData(
            definition_text=definition_text,
            test_inputs=(
                test_inputs if test_inputs is not None else DEFAULT_TEST_INPUTS.copy()
            ),
            test_expected=(
                test_expected
                if test_expected is not None
                else DEFAULT_TEST_EXPECTED_OUTPUTS.copy()
            ),
        )
        self.definitionTextChanged.emit(self.definition_text)
        self.testCasesChanged.emit(self.test_inputs, self.test_expected)

    @property
    def definition_text(self) -> str:
        return self._data.definition_text

    @property
    def test_inputs(self) -> List[str]:
        l.info(f"{self._data.test_inputs=}")
        return self._data.test_inputs.copy()

    @property
    def test_expected(self) -> List[str]:
        l.info(f"{self._data.test_expected=}")
        return self._data.test_expected.copy()

    @property
    def status(self) -> str:
        return self._data.status

    @property
    def is_valid(self) -> bool:
        return self._data.is_valid

    def update_definition_text(self, new_text: str) -> None:
        if new_text != self._data.definition_text:  # Only update if text changed
            self._data = self._data.update_definition_text(new_text)
            self.definitionTextChanged.emit(new_text)

    def update_test_input(self, test_number: int, value: str) -> None:
        index = test_number - 1
        # Convert value to string and ensure we're storing string values
        str_value = value if value is not None else ""
        if (
            0 <= index < len(self._data.test_inputs)
            and self._data.test_inputs[index] != str_value
        ):
            self._data = self._data.update_test_input(index, str_value)
            self.testCasesChanged.emit(
                self._data.test_inputs.copy(), self._data.test_expected.copy()
            )

    def update_test_expected(self, test_number: int, value: str) -> None:
        index = test_number - 1
        # Convert value to string and ensure we're storing string values
        str_value = value if value is not None else ""
        if (
            0 <= index < len(self._data.test_expected)
            and self._data.test_expected[index] != str_value
        ):
            self._data = self._data.update_test_expected(index, str_value)
            self.testCasesChanged.emit(
                self._data.test_inputs.copy(), self._data.test_expected.copy()
            )

    def update_tests(self, inputs: List[str], expected: List[str]) -> None:
        # Convert inputs/expected to string lists
        str_inputs = [str(x.text() if hasattr(x, "text") else x) for x in inputs]
        str_expected = [str(x.text() if hasattr(x, "text") else x) for x in expected]

        if (
            str_inputs != self._data.test_inputs
            or str_expected != self._data.test_expected
        ):
            self._data = self._data.update_tests(str_inputs, str_expected)
            self.testCasesChanged.emit(
                self._data.test_inputs.copy(), self._data.test_expected.copy()
            )

    def validate(self) -> bool:
        new_data = self._data.validate()
        self._data = new_data
        return new_data.is_valid
