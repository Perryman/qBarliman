import os
import platform
import shutil  # added import
import sys
import tempfile
from typing import Optional

"""
Temporary flags
"""
VERBOSE = 3
WARN = "❌‼️‼️"  # 0
GOOD = "✅"  # 1
INFO = "✏️"  # 2
DEBUG = "🐞"  # 3
# Avoid unnecessary coloring when redirecting to file
USE_COLORS = sys.stdout.isatty()


def warn(*args) -> None:
    if VERBOSE >= 0:
        print(f"\033[33m{WARN}\033[0m" if USE_COLORS else WARN, *args)


def good(*args) -> None:
    if VERBOSE >= 1:
        print(f"\033[32m{GOOD}\033[0m" if USE_COLORS else GOOD, *args)


def info(*args) -> None:
    if VERBOSE >= 2:
        print(f"\033[37m{INFO}\033[0m" if USE_COLORS else INFO, *args)


def debug(*args) -> None:
    if VERBOSE >= 3:
        print(f"\033[36m{DEBUG}\033[0m" if USE_COLORS else DEBUG, *args)


"""
Query string (QS) file names
"""

ALLTESTS_QS_FILE_1 = "interp-alltests-query-string-part-1.scm"
ALLTESTS_QS_FILE_2 = "interp-alltests-query-string-part-2.scm"
EVAL_QS_FILE_1 = "interp-eval-query-string-part-1.scm"
EVAL_QS_FILE_2 = "interp-eval-query-string-part-2.scm"
BARLIMAN_QUERY_SIMPLE_FILE = "barliman-query-simple.scm"
BARLIMAN_QUERY_ALLTESTS_FILE = "barliman-query-alltests.scm"

"""
Minikanren file names
"""
MK_VICARE_FILE = "mk-vicare.scm"
MK_FILE = "mk.scm"
MK_TEST_CHECK_FILE = "test-check.scm"
INTERP_FILE = "interp.scm"

"""
File paths
"""

TMP_DIR = tempfile.gettempdir()
TMP_DIR = os.path.join(TMP_DIR, "qBarliman").replace("\\", "\\\\")
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = BASE_DIR.replace("\\", "\\\\")
MINIKANREN_ROOT = os.path.join(BASE_DIR, "minikanren", "core")
REL_INTERP_DIR = os.path.join(BASE_DIR, "minikanren", "rel-interp")
TEMPLATES_DIR = os.path.join(BASE_DIR, "minikanren", "templates")

MK_VICARE_FULLPATH = os.path.join(MINIKANREN_ROOT, MK_VICARE_FILE).replace("\\", "\\\\")
MK_FULLPATH = os.path.join(MINIKANREN_ROOT, MK_FILE).replace("\\", "\\\\")
MK_TEST_CHECK_FULLPATH = os.path.join(MINIKANREN_ROOT, MK_TEST_CHECK_FILE).replace(
    "\\", "\\\\"
)
INTERP_FULLPATH = os.path.join(REL_INTERP_DIR, INTERP_FILE).replace("\\", "\\\\")

CORE_FULLPATH = [
    MK_VICARE_FULLPATH,
    MK_FULLPATH,
    MK_TEST_CHECK_FULLPATH,
    INTERP_FULLPATH,
]


INTERP_ALLTESTS_P_1 = os.path.join(TEMPLATES_DIR, ALLTESTS_QS_FILE_1).replace(
    "\\", "\\\\"
)
INTERP_ALLTESTS_P_2 = os.path.join(TEMPLATES_DIR, ALLTESTS_QS_FILE_2).replace(
    "\\", "\\\\"
)
INTERP_EVAL_P_1 = os.path.join(TEMPLATES_DIR, EVAL_QS_FILE_1).replace("\\", "\\\\")
INTERP_EVAL_P_2 = os.path.join(TEMPLATES_DIR, EVAL_QS_FILE_2).replace("\\", "\\\\")

"""
System paths and configuration
"""
# Process timeouts in milliseconds - increase for debugging
TEST_TIMEOUT_MS = 5000  # 5 seconds for testing
PROCESS_TIMEOUT_MS = 600000  # 60 seconds for processes


# Scheme executable detection
def find_scheme_executable() -> Optional[str]:
    """
    Find the Scheme executable in the system PATH.

    Returns:
        Optional[str]: The name of the Scheme executable if found, otherwise None.
    """
    potential_executables = ["scheme", "chez", "chezscheme"]

    if platform.system() == "Windows":
        potential_executables = [exe + ".exe" for exe in potential_executables]

    for exe in potential_executables:
        # use shutil.which instead of os.system to locate the executable safely
        if shutil.which(exe) is not None:
            return exe

    return None


# Find Scheme executable
SCHEME_EXECUTABLE = find_scheme_executable()
if not SCHEME_EXECUTABLE:
    warn(
        f"Could not find Scheme executable in PATH. Looked for: {', '.join(['scheme', 'chez', 'chezscheme'])}"
    )
    sys.exit(1)
else:
    good(f"Found Scheme executable: {SCHEME_EXECUTABLE}")

# Load query strings from files

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

LOAD_MK_VICARE_SCM = f'(load "{MK_VICARE_FULLPATH}")'
LOAD_MK_SCM = f'(load "{MK_FULLPATH}")'

SIMPLE_Q = "simple"
INDIVIDUAL_Q = "individual test"

EVAL_FLAGS_FAST = "(allow-incomplete-search)"
EVAL_FLAGS_COMPLETE = "(disallow-incomplete-search)"

EVAL_STRING_FAST = f"(begin {EVAL_FLAGS_FAST} (results))"
EVAL_STRING_COMPLETE = f"(begin {EVAL_FLAGS_COMPLETE} (results))"
