# qBarliman/utils/query_builder.py
from qBarliman.models.scheme_document_data import SchemeDocumentData
from qBarliman.templates import (
    ALL_TEST_WRITE_T,
    DEFINE_ANS_T,
    EVAL_BOTH_T,
    EVAL_COMPLETE_T,
    EVAL_FAST_T,
    EVAL_T,
    FULL_T,
    PARSE_ANS_T,
    QUERY_SIMPLE_T,
    SIMPLE_PARSE_ANS_T,
)


class QueryBuilder:
    def __init__(self, interpreter_code):
        self.interpreter_code = interpreter_code

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
        # Prepare inputs and outputs for substitution.
        all_test_inputs = " ".join(
            [f"'{x}" if x else "()" for x in scheme_document.test_inputs]
        )
        all_test_outputs = " ".join(
            [f"'{x}" if x else "()" for x in scheme_document.test_expected]
        )

        return ALL_TEST_WRITE_T.substitute(
            definitionText=scheme_document.definition_text,
            allTestInputs=all_test_inputs,
            allTestOutputs=all_test_outputs,
        )

    def _build_query(
        self, scheme_document: SchemeDocumentData, query_type: str, test_number: int = 0
    ) -> str:
        """Helper function to build queries."""

        if query_type == "simple":
            body = ",_"
            expected_out = "q"
            name = "-simple"
            parse_ans_string = SIMPLE_PARSE_ANS_T.substitute(
                name=name, defns=scheme_document.definition_text, body=body
            )
            query_simple = self._make_query_string(
                scheme_document.definition_text, body, expected_out, name
            )
            return QUERY_SIMPLE_T.substitute(
                interp_string=self.interpreter_code,
                query_simple=query_simple,
            )

        elif query_type == "test":
            body = scheme_document.test_inputs[test_number - 1]
            expected_out = scheme_document.test_expected[test_number - 1]
            name = f"-test{test_number}"
            parse_ans_string = PARSE_ANS_T.substitute(
                name=name, defns=scheme_document.definition_text, body=body
            )

        else:
            raise ValueError(f"Invalid query type: {query_type}")

        # Common query building logic (using the templates)
        eval_string = EVAL_T.substitute(
            defns=scheme_document.definition_text, body=body, expectedOut=expected_out
        )
        eval_string_fast = EVAL_FAST_T.substitute(eval_string=eval_string)
        eval_string_complete = EVAL_COMPLETE_T.substitute(eval_string=eval_string)
        eval_string_both = EVAL_BOTH_T.substitute(
            eval_string_fast=eval_string_fast, eval_string_complete=eval_string_complete
        )
        define_ans_string = DEFINE_ANS_T.substitute(
            name=name, eval_string_both=eval_string_both
        )

        return FULL_T.substitute(
            query_type=query_type,
            parse_ans_string=parse_ans_string,
            define_ans_string=define_ans_string,
        )

    def _make_query_string(
        self, defns: str, body: str, expectedOut: str, name: str
    ) -> str:
        parse_ans_string = SIMPLE_PARSE_ANS_T.substitute(
            name=name, defns=defns, body=body
        )
        eval_string = EVAL_T.substitute(defns=defns, body=body, expectedOut=expectedOut)
        eval_string_fast = EVAL_FAST_T.substitute(eval_string=eval_string)
        eval_string_complete = EVAL_COMPLETE_T.substitute(eval_string=eval_string)
        eval_string_both = EVAL_BOTH_T.substitute(
            eval_string_fast=eval_string_fast, eval_string_complete=eval_string_complete
        )
        define_ans_string = DEFINE_ANS_T.substitute(
            name=name, eval_string_both=eval_string_both
        )
        return FULL_T.substitute(
            query_type="simple",
            parse_ans_string=parse_ans_string,
            define_ans_string=define_ans_string,
        )
