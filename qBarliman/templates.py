from string import Template

from qBarliman.constants import (
    ALLTESTS_STRING_1,
    ALLTESTS_STRING_2,
    EVAL_FLAGS_COMPLETE,
    EVAL_FLAGS_FAST,
    EVAL_STRING_1,
    EVAL_STRING_2,
    EVAL_STRING_COMPLETE,
    EVAL_STRING_FAST,
    INTERP_SCM,
    LOAD_MK_SCM,
    LOAD_MK_VICARE_SCM,
)
from qBarliman.utils import log as l
from qBarliman.utils.rainbowp import rainbowp

"""
Template definitions for query strings and other frequently used code.
ref: https://docs.python.org/3/library/string.html#template-strings
"""

##### func makeQueryString
##### ARGS: $defns $body $expected_out $simple_query $name
PARSE_ANS_STRING_T = Template(  # $name $defns $body
    """
(define (parse-ans$name) (run 1 (q)
  (let ((g1 (gensym \"g1\")) (g2 (gensym \"g2\")) (g3 (gensym \"g3\")) (g4 (gensym \"g4\")) (g5 (gensym \"g5\")) (g6 (gensym \"g6\")) (g7 (gensym \"g7\")) (g8 (gensym \"g8\")) (g9 (gensym \"g9\")) (g10 (gensym \"g10\")) (g11 (gensym \"g11\")) (g12 (gensym \"g12\")) (g13 (gensym \"g13\")) (g14 (gensym \"g14\")) (g15 (gensym \"g15\")) (g16 (gensym \"g16\")) (g17 (gensym \"g17\")) (g18 (gensym \"g18\")) (g19 (gensym \"g19\")) (g20 (gensym \"g20\")))
  (fresh (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z _) (parseo `(begin $defns $body))))))
"""
)

PARSE_WITH_FAKE_DEFNS_ANS_STRING_T = Template(  # $name $defns $body
    """
(define (parse-ans$name) (run 1 (q)
  (let ((g1 (gensym \"g1\")) (g2 (gensym \"g2\")) (g3 (gensym \"g3\")) (g4 (gensym \"g4\")) (g5 (gensym \"g5\")) (g6 (gensym \"g6\")) (g7 (gensym \"g7\")) (g8 (gensym \"g8\")) (g9 (gensym \"g9\")) (g10 (gensym \"g10\")) (g11 (gensym \"g11\")) (g12 (gensym \"g12\")) (g13 (gensym \"g13\")) (g14 (gensym \"g14\")) (g15 (gensym \"g15\")) (g16 (gensym \"g16\")) (g17 (gensym \"g17\")) (g18 (gensym \"g18\")) (g19 (gensym \"g19\")) (g20 (gensym \"g20\")))
  (fresh (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z _) (fresh (names dummy-expr) (extract-nameso `( $defns ) names) (parseo `((lambda ,names $body) ,dummy-expr)))))))
"""
)

EVAL_STRING_T = Template(
    f"""
{EVAL_STRING_1}
        (== `( $defns ) defn-list)
{EVAL_STRING_2}
  (evalo `(begin $defns $body) $expectedOut))))
"""
)

EVAL_STRING_FAST_T = Template(
    f"""
(begin {EVAL_FLAGS_FAST} {EVAL_STRING_T.safe_substitute()})
"""
)

EVAL_STRING_COMPLETE_T = Template(
    f"""
(begin {EVAL_FLAGS_COMPLETE} {EVAL_STRING_T.safe_substitute()})
"""
)

EVAL_STRING_BOTH_T = Template(
    f"""
(let ((results-fast $eval_string_fast))
  (if (null? results-fast)
    {EVAL_STRING_COMPLETE_T.safe_substitute()}
    results-fast))
"""
)

DEFINE_ANS_STRING_T = Template(
    f"""
(define (query-val$name)
  (if (null? (parse-ans$name))
      'parse-error
      {EVAL_STRING_BOTH_T.safe_substitute()}))
    """
)

# $defns $body $expected_out $query_type $name
MAKE_QUERY_STRING_T = Template(  # $defns $body $expected_out $name
    """
;; $query_type query


$parse_ans


$define_ans


"""
)  # full_string
##########

##### func makeAllTestsQueryString
##### ARGS: $defns $body $expected_out $simple_query $name

ALL_TEST_WRITE_T = Template(
    f"""
;; allTests
(define (ans-allTests)
  (define (results)
    {ALLTESTS_STRING_1}
    (== `( $definitionText ) defn-list)

    {ALLTESTS_STRING_2}
        (== `( $definitionText ) defns) (appendo defns `(((lambda x x) $all_test_inputs)) begin-body) (evalo `(begin . ,begin-body) (list $all_test_outputs))))))
(let ((results-fast {EVAL_STRING_FAST}))
  (if (null? results-fast)
    {EVAL_STRING_COMPLETE}
    results-fast)))
"""
)  # return fullString
##########


##### func makeQuerySimpleForMondoSchemeFileString
##### ARGS: $defns  (inherited from MAKE_QUERY_STRING_T)
MAKE_QUERY_SIMPLE_FOR_MONDO_SCHEME_T = Template(
    f"""
{LOAD_MK_VICARE_SCM}
{LOAD_MK_SCM}
{INTERP_SCM}
{MAKE_QUERY_STRING_T.safe_substitute( \
    name="-simple", \
    body=",_", expected_out="q", query_type="simple", \
    parse_ans=PARSE_ANS_STRING_T.safe_substitute(), \
    define_ans="")}
"""
)
##########


##### func makeNewTestNQueryString
##### ARGS: $loadFileString $actualQueryFilePath $n $new_test_query_template_string
##### $localSimpleQueryForMondoSchemeFilePath
LOAD_FILE_STRING_T = Template(
    """
(define simple-query-for-mondo-file-path \"$localSimpleQueryForMondoSchemeFilePath\")
"""
)

MAKE_NEW_TEST_N_QUERY_STRING_T = Template(
    f"""
{LOAD_FILE_STRING_T.safe_substitute()}

(define actual-query-file-path \"$actualQueryFilePath\")

(define (test-query-fn) (query-val-test$n))


$new_test_query_template_string
"""
)
##########


SIMPLE_QUERY_T = Template(
    """
$load_mk_vicare
$load_mk
$interp_scm
$query_simple
"""
)

ALL_TESTS_QUERY_T = Template(
    """
;; allTests
$all_tests_query
"""
)

# All tests query has all non-empty test i/o, and definition text
ALL_TEST_WRITE_T = Template(
    f"""
;; allTests
(define (ans-allTests)
  (define (results)
    {ALLTESTS_STRING_1}
    (== `( $definitionText ) defn-list)

    
        {ALLTESTS_STRING_2}
        (== `( $definitionText ) defns) (appendo defns `(((lambda x x) $all_test_inputs)) begin-body) (evalo `(begin . ,begin-body) (list $all_test_outputs) )))))
(let ((results-fast {EVAL_STRING_FAST}))
  (if (null? results-fast)
    {EVAL_STRING_COMPLETE}
    results-fast)))
"""
)

EVAL_QUERY_T = Template(
    """
$eval_part1
$defn_list_query
$eval_part2
(evalo `(begin $defns $body) $expected_out)
"""
)

QUERY_SIMPLE_T = Template(
    """
$load_mk_vicare
$load_mk
$interp_scm_string
$query_simple
"""
)

PARSE_ANS_T = Template(
    """
(define (parse-ans$name) (run 1 (q)
 (let ((g1 (gensym "g1")) (g2 (gensym "g2")) (g3 (gensym "g3")) 
(g4 (gensym "g4")) (g5 (gensym "g5")) (g6 (gensym "g6")) 
(g7 (gensym "g7")) (g8 (gensym "g8")) (g9 (gensym "g9")) 
(g10 (gensym "g10")) (g11 (gensym "g11")) (g12 (gensym "g12")) 
(g13 (gensym "g13")) (g14 (gensym "g14")) (g15 (gensym "g15")) 
(g16 (gensym "g16")) (g17 (gensym "g17")) (g18 (gensym "g18")) 
(g19 (gensym "g19")) (g20 (gensym "g20")))
 (fresh (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z _) (parseo `(begin $defns $body))))))
"""
)
PARSE_FAKE_DEFNS_ANS_T = Template(
    """
(define (parse-ans$name) (run 1 (q)
 (let ((g1 (gensym "g1")) (g2 (gensym "g2")) (g3 (gensym "g3")) 
(g4 (gensym "g4")) (g5 (gensym "g5")) (g6 (gensym "g6")) 
(g7 (gensym "g7")) (g8 (gensym "g8")) (g9 (gensym "g9")) 
(g10 (gensym "g10")) (g11 (gensym "g11")) (g12 (gensym "g12")) 
(g13 (gensym "g13")) (g14 (gensym "g14")) (g15 (gensym "g15")) 
(g16 (gensym "g16")) (g17 (gensym "g17")) (g18 (gensym "g18")) 
(g19 (gensym "g19")) (g20 (gensym "g20")))
 (fresh (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z _)
(fresh (names dummy-expr) (extract-nameso `( $defns ) names) (parseo `((lambda ,names $body) ,dummy-expr)))))))
"""
)


def unroll(tmpl: Template, subs: dict, iters: int = 5, res: str = "") -> str:
    if iters <= 0:
        raise ValueError("Max template unrolling iterations exceeded")
    curr = tmpl.safe_substitute(**subs)
    if curr == res and "$" in curr:
        l.warn(
            "Possibly incomplete template! Ensure these are all from the rel-interp and not templates.py or constants.py"
        )
        d = [s for s in curr.split() if "$" in s]
        for s in d:
            print(rainbowp(s), end=", ")
        print()

    return curr if curr == res else unroll(Template(curr), subs, iters - 1, curr)
