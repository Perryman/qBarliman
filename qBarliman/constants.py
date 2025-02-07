import os

"""
Temporary flags
"""
VERBOSE = 2  # Temporary good functions because I don't want accidental import bloat
WARN = "❌‼️‼️"  # 0
GOOD = "✅"  # 1
INFO = "✏️"  # 2


def warn(*args):
    if VERBOSE >= 0:
        print(WARN, *args)


def good(*args):
    if VERBOSE >= 1:
        print(GOOD, *args)


def info(*args):
    if VERBOSE >= 2:
        print(INFO, *args)


"""
Query string (QS) file names
"""

ALLTESTS_QS_F_1 = "interp-alltests-query-string-part-1.scm"
ALLTESTS_QS_F_2 = "interp-alltests-query-string-part-2.scm"
EVAL_QS_F_1 = "interp-eval-query-string-part-1.scm"
EVAL_QS_F_2 = "interp-eval-query-string-part-2.scm"
BARLIMAN_QUERY_SIMPLE_SCM = "barliman-query-simple.scm"
BARLIMAN_QUERY_ALLTESTS_SCM = "barliman-query-alltests.scm"

"""
Minikanren file names
"""
MK_VICARE_F = "mk-vicare.scm"
MK_F = "mk.scm"

"""
File paths
"""

TMP_DIR = os.path.join(os.environ.get("TMP", "/tmp"), "barliman_tmp")
os.makedirs(TMP_DIR, exist_ok=True)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MINIKANREN_CORE_DIR = os.path.join(BASE_DIR, "minikanren", "core")
REL_INTERP_DIR = os.path.join(BASE_DIR, "minikanren", "rel-interp")
TEMPLATES_DIR = os.path.join(BASE_DIR, "minikanren", "templates")

MK_VICARE = os.path.join(MINIKANREN_CORE_DIR, MK_VICARE_F)
MK = os.path.join(MINIKANREN_CORE_DIR, MK_F)

INTERP_ALLTESTS_P_1 = os.path.join(TEMPLATES_DIR, ALLTESTS_QS_F_1)
INTERP_ALLTESTS_P_2 = os.path.join(TEMPLATES_DIR, ALLTESTS_QS_F_2)
INTERP_EVAL_P_1 = os.path.join(TEMPLATES_DIR, EVAL_QS_F_1)
INTERP_EVAL_P_2 = os.path.join(TEMPLATES_DIR, EVAL_QS_F_2)

"""
Load query strings from files
"""

ALLTESTS_STRING_PART_1 = ""
ALLTESTS_STRING_PART_2 = ""
EVAL_STRING_PART_1 = ""
EVAL_STRING_PART_2 = ""

try:
    with open(INTERP_ALLTESTS_P_1, "r", encoding="utf-8") as f:
        ALLTESTS_STRING_PART_1 = f.read()
        good(f"loaded {INTERP_ALLTESTS_P_1}")
except Exception as e:
    warn(f"LOAD_ERROR -- reading {INTERP_ALLTESTS_P_1}: {e}")

try:
    with open(INTERP_ALLTESTS_P_2, "r", encoding="utf-8") as f:
        ALLTESTS_STRING_PART_2 = f.read()
        good(f"loaded {INTERP_ALLTESTS_P_2}")
except Exception as e:
    warn(f"LOAD_ERROR -- reading {INTERP_ALLTESTS_P_2}: {e}")

try:
    with open(INTERP_EVAL_P_1, "r", encoding="utf-8") as f:
        EVAL_STRING_PART_1 = f.read()
        good(f"loaded {INTERP_EVAL_P_1}")
except Exception as e:
    warn(f"LOAD_ERROR -- reading {INTERP_EVAL_P_1}: {e}")

try:
    with open(INTERP_EVAL_P_2, "r", encoding="utf-8") as f:
        EVAL_STRING_PART_2 = f.read()
        good(f"loaded {INTERP_EVAL_P_2}")
except Exception as e:
    warn(f"LOAD_ERROR -- reading {INTERP_EVAL_P_2}: {e}")

"""
Default value fields
"""

DEFAULT_DEFINITIONS = [
    "(define ,A",
    "    (lambda ,B",
    "        ,C))",
]

DEFAULT_TEST_INPUTS = [
    "(append '() '5)",
    "(append '(a) '6)",
    "(append '(e f) '(g h))",
    "",
    "",
    "",
]

DEFAULT_TEST_EXPECTED_OUTPUTS = [
    "5",
    "'(a . 6)",
    "'(e f g h)",
    "",
    "",
    "",
]


"""
Scheme code constants
"""

LOAD_MK_VICARE = f'(load "{MK_VICARE}")'
LOAD_MK = f'(load "{MK}")'
