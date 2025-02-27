from enum import Enum, auto
from typing import Any, Dict, Optional, Protocol

from PySide6.QtCore import QObject, Signal

from config.constants import INTERP_SCM, LOAD_MK_SCM, LOAD_MK_VICARE_SCM
from config.templates import (
    ALL_TEST_WRITE_T,
    EVAL_STRING_BOTH_T,
    MAKE_NEW_TEST_N_QUERY_STRING_T,
    MAKE_QUERY_SIMPLE_FOR_MONDO_SCHEME_T,
    MAKE_QUERY_STRING_T,
    PARSE_ANS_STRING_T,
    PARSE_FAKE_DEFNS_ANS_T,
    unroll,
)
from models.scheme_document_data import SchemeDocumentData
from utils import log as l
from utils.rainbowp import rainbowp


class SchemeQueryType(Enum):
    SIMPLE = auto()
    TEST = auto()
    ALL_TESTS = auto()


class QueryStrategy(Protocol):
    """Strategy protocol for building different types of queries"""

    def build_query(self, data: Any) -> str: ...


class BaseQueryStrategy:  # Keep this for consistent structure
    def __init__(self):
        pass


class SimpleQueryStrategy(BaseQueryStrategy, QueryStrategy):
    def build_query(self, document_data: SchemeDocumentData) -> str:
        subs = {
            "load_mk_vicare": LOAD_MK_VICARE_SCM,
            "load_mk": LOAD_MK_SCM,
            "interp_scm": INTERP_SCM,
            "name": "-simple",
            "defns": document_data.definition_text,
            "body": ",_",
            "expectedOut": "q",
            "query_type": "simple",
            "parse_ans": PARSE_ANS_STRING_T.safe_substitute(),
            "define_ans": "",  # No define_ans for simple
            "eval_string_fast": PARSE_ANS_STRING_T.template,
        }
        res = unroll(MAKE_QUERY_SIMPLE_FOR_MONDO_SCHEME_T, subs)
        l.scheme(f"Simple query strategy:\n{rainbowp(res)}")
        return res


class TestQueryStrategy(BaseQueryStrategy, QueryStrategy):
    def build_query(self, data: tuple[SchemeDocumentData, int]) -> str:
        document_data, test_number = data
        subs = {
            "load_mk_vicare": LOAD_MK_VICARE_SCM,
            "load_mk": LOAD_MK_SCM,
            "interp_scm": INTERP_SCM,
            "name": f"-test-{test_number}",  # Include "test" in the name
            # "loadFileString": "",  # Not used
            "n": test_number,
            "defns": document_data.definition_text,
            "body": document_data.test_inputs[test_number - 1],
            "expectedOut": document_data.test_expected[test_number - 1],
            "query_type": "individual test",
            "new_test_query_template_string": MAKE_QUERY_STRING_T.template,  # Correct template
            "parse_ans": PARSE_FAKE_DEFNS_ANS_T.safe_substitute(),  # Use fake defns
            "define_ans": "",  # Included in the main template
            "eval_string_fast": EVAL_STRING_BOTH_T.template,
            "eval_string_complete": EVAL_STRING_BOTH_T.template,
        }
        res = unroll(MAKE_NEW_TEST_N_QUERY_STRING_T, subs)
        l.scheme(f"Test query strategy:\n{rainbowp(res)}")
        return res


class AllTestsQueryStrategy(BaseQueryStrategy, QueryStrategy):
    def build_query(self, document_data: SchemeDocumentData) -> str:
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
            "interp_scm": INTERP_SCM,
            "defns": document_data.definition_text,
            "body": ",_",
            "expectedOut": "q",
            "all_tests_query": ALL_TEST_WRITE_T.template,
            "all_test_inputs": " ".join(all_test_inputs),
            "all_test_outputs": " ".join(all_test_outputs),
            "definitionText": document_data.definition_text,
        }

        res = unroll(ALL_TEST_WRITE_T, subs)
        l.scheme(f"All tests query strategy:\n{rainbowp(res)}")
        return res


class QueryBuilder(QObject):
    """Builds Scheme queries using strategy pattern."""

    queryBuilt = Signal(str, SchemeQueryType)

    def __init__(self, interpreter_code: Optional[str] = None):
        super().__init__()
        # Don't need to load interpreter code here anymore
        self._strategies: Dict[SchemeQueryType, QueryStrategy] = {
            SchemeQueryType.SIMPLE: SimpleQueryStrategy(),
            SchemeQueryType.TEST: TestQueryStrategy(),
            SchemeQueryType.ALL_TESTS: AllTestsQueryStrategy(),
        }

    def build_query(self, query_type: SchemeQueryType, data: Any) -> str:
        l.debug(f"Building query of type {query_type}")
        strategy = self._strategies.get(query_type)
        if not strategy:
            raise ValueError(f"Unknown query type: {query_type}")

        query = strategy.build_query(data)
        self.queryBuilt.emit(query, query_type)
        return query
