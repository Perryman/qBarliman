from string import Template

from qBarliman.constants import (
    ALLTESTS_STRING_PART_1,
    ALLTESTS_STRING_PART_2,
    EVAL_FLAGS_COMPLETE,
    EVAL_FLAGS_FAST,
    EVAL_STRING_COMPLETE,
    EVAL_STRING_FAST,
    EVAL_STRING_PART_1,
    EVAL_STRING_PART_2,
)

"""
Template definitions for query strings and other frequently used code.
ref: https://docs.python.org/3/library/string.html#template-strings
"""


SIMPLE_QUERY_T = Template(
    """
$load_mk_vicare
$load_mk
$interp
$query_simple
"""
)  # Use a single multiline string

ALL_TESTS_QUERY_T = Template(
    """
;; allTests
$all_tests_query
"""
)

ALL_TEST_WRITE_T = Template(
    f"""
;; allTests
(define (ans-allTests)
  (define (results)
{ALLTESTS_STRING_PART_1}
    (== `( $definitionText ) defn-list)

    
{ALLTESTS_STRING_PART_2}
        (== `( $definitionText ) defns) (appendo defns `(((lambda x x) $allTestInputs)) begin-body) (evalo `(begin . ,begin-body) (list $allTestOutputs) )))))
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
$interp_string
$query_simple
"""
)

SIMPLE_PARSE_ANS_T = Template(
    """
(define (parse-ans$name) (run 1 (q)
 (let ((g1 (gensym "g1")) (g2 (gensym "g2")) (g3 (gensym "g3")) 
(g4 (gensym "g4")) (g5 (gensym "g5")) (g6 (gensym "g6")) 
(g7 (gensym "g7")) (g8 (gensym "g8")) (g9 (gensym "g9")) 
(g10 (gensym "g10")) (g11 (gensym "g11")) (g12 (gensym "g12")) 
(g13 (gensym "g13")) (g14 (gensym "g14")) (g15 (gensym "g15")) 
(g16 (gensym "g16")) (g17 (gensym "g17")) (g18 (gensym "g18")) 
(g19 (gensym "g19")) (g20 (gensym "g20")))
 (fresh (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z  ) (parseo `(begin $defns $body))))))
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
 (fresh (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z  ) 
(fresh (names dummy-expr) (extract-nameso `( $defns ) names) (parseo `((lambda ,names $body) ,dummy-expr)))))))
"""
)

EVAL_T = Template(
    f"""
{EVAL_STRING_PART_1}

        (== `(  $defns  ) defn-list)

{EVAL_STRING_PART_2}
 (evalo `(begin $defns   $body )  $expectedOut ))))
"""
)

EVAL_FAST_T = Template(
    f"""
(begin {EVAL_FLAGS_FAST} $eval_string)
"""
)

EVAL_COMPLETE_T = Template(
    f"""
(begin {EVAL_FLAGS_COMPLETE} $eval_string)
"""
)

EVAL_BOTH_T = Template(
    """
(let ((results-fast $eval_string_fast))
  (if (null? results-fast)
    $eval_string_complete
     results-fast))
"""
)

DEFINE_ANS_T = Template(
    """
(define (query-val$name)
    (if (null? (parse-ans$name))
        'parse-error
        $eval_string_both))
    """
)

FULL_T = Template(
    """
;; $query_type query


$parse_ans_string


$define_ans_string


"""
)
