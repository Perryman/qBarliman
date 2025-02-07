"""
Template definitions for query strings and other frequently used code.
ref: https://docs.python.org/3/library/string.html#template-strings
"""

from string import Template

SIMPLE_QUERY_T = Template("""
$load_mk_vicare
$load_mk
$interp
$query_simple
""")  # Use a single multiline string

ALL_TESTS_QUERY_T = Template("""
;; allTests
$all_tests_query
""")

EVAL_QUERY_T = Template("""
$eval_part1
$defn_list_query
$eval_part2
(evalo `(begin $defns $body) $expected_out)
""")

QUERY_SIMPLE_T = Template("""
$load_mk_vicare
$load_mk
$interp_string
$query_simple
""")


def makeQuerySimpleForMondoSchemeFileString(self, interp_string: str) -> str:
    # Get the scheme definition text
    definitionText = self.schemeDefinitionView.toPlainText()
    # Create the simple query using makeQueryString (simple=True)
    querySimple = self.makeQueryString(
        definitionText, body=",_", expectedOut="q", simple=True, name="-simple"
    )
    full_string = MAKE_QUERY_SIMPLE_TEMPLATE.substitute(
        load_mk_vicare=LOAD_MK_VICARE,
        load_mk=LOAD_MK,
        interp_string=interp_string,
        query_simple=querySimple,
    )
    return full_string
