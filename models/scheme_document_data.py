from dataclasses import dataclass, replace
from typing import List


@dataclass(frozen=True)
class SchemeDocumentData:
    definition_text: str
    test_inputs: List[str]
    test_expected: List[str]
    status: str = ""
    is_valid: bool = True

    def update_definition_text(self, new_text: str) -> "SchemeDocumentData":
        return replace(self, definition_text=new_text)

    def update_test_input(self, index: int, value: str) -> "SchemeDocumentData":
        new_inputs = self.test_inputs.copy()
        new_inputs[index] = value
        return replace(self, test_inputs=new_inputs)

    def update_test_expected(self, index: int, value: str) -> "SchemeDocumentData":
        new_expected = self.test_expected.copy()
        new_expected[index] = value
        return replace(self, test_expected=new_expected)

    def update_tests(
        self, inputs: List[str], expected: List[str]
    ) -> "SchemeDocumentData":
        return replace(self, test_inputs=inputs.copy(), test_expected=expected.copy())

    def validate(self) -> "SchemeDocumentData":
        # For simplicity, we mark valid if the definition text is non-empty.
        valid = bool(self.definition_text.strip())
        return replace(self, is_valid=valid)
