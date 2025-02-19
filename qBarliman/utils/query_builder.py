from enum import Enum, auto
from typing import Any, Dict, Optional, Protocol

from PySide6.QtCore import QObject, Signal

from qBarliman.constants import LOAD_MK_SCM, LOAD_MK_VICARE_SCM
from qBarliman.models.scheme_document_data import SchemeDocumentData
from qBarliman.templates import (
    ALL_TEST_WRITE_T,
    MAKE_NEW_TEST_N_QUERY_STRING_T,
    MAKE_QUERY_SIMPLE_FOR_MONDO_SCHEME_T,
    MAKE_QUERY_STRING_T,
    PARSE_ANS_STRING_T,
    unroll,
)
from qBarliman.utils import log as l
from qBarliman.utils.load_interpreter import (
    load_interpreter_code,
)
from qBarliman.utils.rainbowp import rainbowp


class SchemeQueryType(Enum):
    SIMPLE = auto()
    TEST = auto()
    ALL_TESTS = auto()


class QueryStrategy(Protocol):
    """Strategy protocol for building different types of queries"""

    interpreter_code: str  # Define as a property in the protocol

    def build_query(self, data: Any) -> str: ...


class BaseQueryStrategy:  # Abstract base class for common setup
    def __init__(self, interpreter_code: str):
        self.interpreter_code = interpreter_code


class SimpleQueryStrategy(BaseQueryStrategy, QueryStrategy):
    def build_query(self, document_data: SchemeDocumentData) -> str:
        subs = {
            "name": "-simple",
            "defns": document_data.definition_text,
            "body": ",_",
            "expectedOut": "q",
            "eval_string_fast": PARSE_ANS_STRING_T.template,
        }
        res = unroll(MAKE_QUERY_SIMPLE_FOR_MONDO_SCHEME_T, subs)
        l.debug(f"Simple query strategy:\n{rainbowp(res)}")
        return res


class TestQueryStrategy(BaseQueryStrategy, QueryStrategy):
    def build_query(self, data: tuple[SchemeDocumentData, int]) -> str:
        document_data, test_number = data
        subs = {
            "name": f"-{test_number}",
            "loadFileString": "loadFileString",
            # Remove actualQueryFilePath dependency
            "n": test_number,
            "new_test_query_template_string": MAKE_QUERY_STRING_T.template,
            "defns": document_data.definition_text,
            "body": ",_",
            "expectedOut": "q",
            "eval_string_fast": PARSE_ANS_STRING_T.template,
        }
        res = unroll(MAKE_NEW_TEST_N_QUERY_STRING_T, subs)
        l.debug(f"Test query strategy:\n{rainbowp(res)}")
        return res


class AllTestsQueryStrategy(BaseQueryStrategy, QueryStrategy):
    def build_query(self, document_data: SchemeDocumentData) -> str:
        # Filter out empty test cases and create pairs
        test_pairs = [
            (i, o)
            for i, o in zip(document_data.test_inputs, document_data.test_expected)
            if i.strip() and o.strip()
        ]

        for idx, (input_val, output_val) in enumerate(test_pairs):
            l.debug(f"all_test_inputs #{idx}: {rainbowp(input_val)}")
            l.debug(f"all_test_outputs #{idx}: {rainbowp(output_val)}")

        all_test_inputs = [pair[0] for pair in test_pairs]
        all_test_outputs = [pair[1] for pair in test_pairs]

        subs = {
            "load_mk_vicare": LOAD_MK_VICARE_SCM,
            "load_mk": LOAD_MK_SCM,
            "interp_scm": self.interpreter_code,
            "query_simple": MAKE_QUERY_STRING_T.template,
            "defns": document_data.definition_text,
            "body": ",_",
            "expectedOut": "q",
            "eval_string_fast": PARSE_ANS_STRING_T.template,
            "all_tests_query": ALL_TEST_WRITE_T.template,
            "all_test_inputs": " ".join(all_test_inputs),
            "all_test_outputs": " ".join(all_test_outputs),
            "definitionText": document_data.definition_text,
        }

        res = unroll(ALL_TEST_WRITE_T, subs)
        l.debug(f"All tests query strategy:\n{rainbowp(res)}")
        return res


class QueryBuilder(QObject):
    """Builds and executes Scheme queries using strategy pattern"""

    queryBuilt = Signal(str, SchemeQueryType)

    def __init__(self, interpreter_code: Optional[str] = None):
        super().__init__()
        # Load interpreter code here if not provided
        self.interpreter_code = (
            interpreter_code
            if interpreter_code is not None
            else load_interpreter_code()
        )

        # Initialize strategies with injected or loaded interpreter code
        self._strategies: Dict[SchemeQueryType, QueryStrategy] = {
            SchemeQueryType.SIMPLE: SimpleQueryStrategy(self.interpreter_code),
            SchemeQueryType.TEST: TestQueryStrategy(self.interpreter_code),
            SchemeQueryType.ALL_TESTS: AllTestsQueryStrategy(self.interpreter_code),
        }

    def build_query(self, query_type: SchemeQueryType, data: Any) -> str:
        l.debug(f"Building query of type {query_type}")
        strategy = self._strategies.get(query_type)
        if not strategy:
            raise ValueError(f"Unknown query type: {query_type}")

        query = strategy.build_query(data)
        self.queryBuilt.emit(query, query_type)
        return query

    def _format_scheme_value(self, value: str) -> str:
        """Formats a Python string for use in Scheme code."""
        return f"{value}" if value.strip() else ""
