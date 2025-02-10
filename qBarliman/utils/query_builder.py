from qBarliman.templates import QUERY_SIMPLE_T, ALL_TEST_WRITE_T, SIMPLE_PARSE_ANS_T, PARSE_ANS_T, EVAL_T, EVAL_FAST_T, EVAL_COMPLETE_T, EVAL_BOTH_T, DEFINE_ANS_T, FULL_T
from qBarliman.constants import LOAD_MK_VICARE, LOAD_MK, TEST_TIMEOUT_MS

class QueryBuilder:
    def __init__(self, interpreter_code):
        self.interpreter_code = interpreter_code

    def build_simple_query(self, scheme_document):
        querySimple = self._make_query_string(
            defns=scheme_document.definition_text,
            body=",_",
            expectedOut="q",
            simple=True,
            name="-simple"
        )
        return QUERY_SIMPLE_T.substitute(
            load_mk_vicare=LOAD_MK_VICARE,
            load_mk=LOAD_MK,
            interp_string=self.interpreter_code,
            query_simple=querySimple
        )
    
    def build_all_tests_query(self, scheme_document):
        allTestInputs = " ".join(scheme_document.test_inputs)
        allTestOutputs = " ".join(scheme_document.test_expected)
        return ALL_TEST_WRITE_T.substitute(
            definitionText=scheme_document.definition_text,
            allTestInputs=allTestInputs,
            allTestOutputs=allTestOutputs
        )

    def _make_query_string(self, defns, body, expectedOut, simple, name):
        if simple:
            parse_ans_string = SIMPLE_PARSE_ANS_T.substitute(name=name, defns=defns, body=body)
        else:
            parse_ans_string = PARSE_ANS_T.substitute(name=name, defns=defns, body=body)
        eval_string = EVAL_T.substitute(defns=defns, body=body, expectedOut=expectedOut)
        eval_string_fast = EVAL_FAST_T.substitute(eval_string=eval_string)
        eval_string_complete = EVAL_COMPLETE_T.substitute(eval_string=eval_string)
        eval_string_both = EVAL_BOTH_T.substitute(eval_string_fast=eval_string_fast, eval_string_complete=eval_string_complete)
        define_ans_string = DEFINE_ANS_T.substitute(name=name, eval_string_both=eval_string_both)
        query_type = "simple" if simple else "individual"
        return FULL_T.substitute(query_type=query_type, parse_ans_string=parse_ans_string, define_ans_string=define_ans_string)