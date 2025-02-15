from qBarliman.constants import LOAD_MK_SCM, LOAD_MK_VICARE_SCM, debug
from qBarliman.models.scheme_document_data import SchemeDocumentData
from qBarliman.templates import (
    ALL_TEST_WRITE_T,
    MAKE_QUERY_STRING_T,
)
from qBarliman.utils.load_interpreter import load_interpreter_code
from qBarliman.utils.rainbowp import rainbowp


class QueryBuilder:

    def __init__(self):
        self.interpreter_code = load_interpreter_code()

    def build_simple_query(self, scheme_document: SchemeDocumentData) -> str:
        """Build query for simple evaluation."""
        return self._build_query(scheme_document, "simple")

    def build_test_query(
        self, scheme_document: SchemeDocumentData, test_number: int
    ) -> str:
        """Build query for individual test."""
        if not 1 <= test_number <= len(scheme_document.test_inputs):
            raise ValueError(f"Invalid test number: {test_number}")
        return self._build_query(scheme_document, "test", test_number)

    def build_all_tests_query(self, scheme_document: SchemeDocumentData) -> str:
        """Build query for all tests."""
        all_test_inputs = " ".join(
            [self._format_scheme_value(x) for x in scheme_document.test_inputs]
        )
        all_test_outputs = " ".join(
            [self._format_scheme_value(x) for x in scheme_document.test_expected]
        )
        debug(f"All test inputs: {rainbowp(all_test_inputs)}")
        debug(f"All test outputs: {rainbowp(all_test_outputs)}")
        debug(f"All test definition text:\n{rainbowp(scheme_document.definition_text)}")
        debug(
            f"After substitution: {rainbowp(ALL_TEST_WRITE_T.substitute(definitionText=scheme_document.definition_text, allTestInputs=all_test_inputs, allTestOutputs=all_test_outputs))}"
        )
        return ALL_TEST_WRITE_T.substitute(
            load_mk_vicare=LOAD_MK_VICARE_SCM,
            load_mk=LOAD_MK_SCM,
            interp_string=self.interpreter_code,
            definitionText=scheme_document.definition_text,
            allTestInputs=all_test_inputs,
            allTestOutputs=all_test_outputs,
        )

    def _build_query(
        self, scheme_document: SchemeDocumentData, query_type: str, test_number: int = 0
    ) -> str:
        """Helper function to build queries."""

        if query_type == "simple":
            return MAKE_QUERY_STRING_T.safe_substitute()

        # elif query_type == "test":
        #     body = scheme_document.test_inputs[test_number - 1]
        #     expected_out = scheme_document.test_expected[test_number - 1]
        #     name = f"-test{test_number}"
        #     parse_ans_string = PARSE_FAKE_DEFNS_ANS_T.substitute(
        #         name=name, defns=scheme_document.definition_text, body=body
        #     )
        else:
            raise ValueError(f"Invalid query type: {query_type}")

    def _format_scheme_value(self, value: str) -> str:
        """Formats a Python string for use in Scheme code."""
        if not value.strip():  # Check for empty or whitespace-only strings
            return "'()"  # Return '() for empty inputs
        return f"{value}"  # User input will pass as is
