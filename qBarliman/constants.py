import os
import platform
import shutil  # added import
import sys
import tempfile
from typing import Optional

from qBarliman.utils import log as l

# Query string (QS) file names

ALLTESTS_QS_FILE_1 = "interp-alltests-query-string-part-1.scm"
ALLTESTS_QS_FILE_2 = "interp-alltests-query-string-part-2.scm"
INTERP_EVAL_QS_FILE_1 = "interp-eval-query-string-part-1.scm"
INTERP_EVAL_QS_FILE_2 = "interp-eval-query-string-part-2.scm"
BARLIMAN_QUERY_SIMPLE_FILE = "barliman-query-simple.scm"
BARLIMAN_QUERY_ALLTESTS_FILE = "barliman-query-alltests.scm"

# Minikanren file names

MK_VICARE_FILE = "mk-vicare.scm"
MK_FILE = "mk.scm"
MK_TEST_CHECK_FILE = "test-check.scm"
INTERP_FILE = "interp.scm"

# File paths

TMP_DIR = tempfile.gettempdir()
TMP_DIR = os.path.join(TMP_DIR, "qBarliman")
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MINIKANREN_ROOT = os.path.join(BASE_DIR, "minikanren", "core")
REL_INTERP_DIR = os.path.join(BASE_DIR, "minikanren", "rel-interp")
TEMPLATES_DIR = os.path.join(BASE_DIR, "minikanren", "templates")

MK_VICARE_FULLPATH = os.path.join(MINIKANREN_ROOT, MK_VICARE_FILE)
MK_FULLPATH = os.path.join(MINIKANREN_ROOT, MK_FILE)
MK_TEST_CHECK_FULLPATH = os.path.join(MINIKANREN_ROOT, MK_TEST_CHECK_FILE)
INTERP_FULLPATH = os.path.join(REL_INTERP_DIR, INTERP_FILE)

CORE_FULLPATH = [
    MK_VICARE_FULLPATH,
    MK_FULLPATH,
    MK_TEST_CHECK_FULLPATH,
    INTERP_FULLPATH,
]


INTERP_ALLTESTS_P_1 = os.path.join(TEMPLATES_DIR, ALLTESTS_QS_FILE_1)
INTERP_ALLTESTS_P_2 = os.path.join(TEMPLATES_DIR, ALLTESTS_QS_FILE_2)
INTERP_EVAL_P_1 = os.path.join(TEMPLATES_DIR, INTERP_EVAL_QS_FILE_1)
INTERP_EVAL_P_2 = os.path.join(TEMPLATES_DIR, INTERP_EVAL_QS_FILE_2)

# System paths and configuration

TEST_TIMEOUT_MS = 5000  # 5 seconds for testing
PROCESS_TIMEOUT_MS = 600000  # 60 seconds for processes


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
        if shutil.which(exe) is not None:
            return exe

    return None


SCHEME_EXECUTABLE = find_scheme_executable()
if not SCHEME_EXECUTABLE:
    l.warn(
        f"Could not find Scheme executable in PATH. Looked for: {', '.join(['scheme', 'chez', 'chezscheme'])}"
    )
    sys.exit(1)
else:
    l.good(f"Found Scheme executable: {SCHEME_EXECUTABLE}")

# Load query strings from files


def load_safe(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            l.good(f"loaded {file_path}")
            return content
    except Exception as e:
        l.warn(f"LOAD_ERROR -- reading {file_path}: {e}")
        return ""


ALLTESTS_STRING_1 = load_safe(INTERP_ALLTESTS_P_1)
ALLTESTS_STRING_2 = load_safe(INTERP_ALLTESTS_P_2)
EVAL_STRING_1 = load_safe(INTERP_EVAL_P_1)
EVAL_STRING_2 = load_safe(INTERP_EVAL_P_2)
INTERP_SCM = load_safe(INTERP_FULLPATH)

# Default value fields

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

# Scheme code constants

LOAD_MK_VICARE_SCM = f'(load "{MK_VICARE_FULLPATH}")'.replace("\\", "\\\\")
LOAD_MK_SCM = f'(load "{MK_FULLPATH}")'.replace("\\", "\\\\")

SIMPLE_Q = "simple"
INDIVIDUAL_Q = "individual test"

EVAL_FLAGS_FAST = "(allow-incomplete-search)"
EVAL_FLAGS_COMPLETE = "(disallow-incomplete-search)"

EVAL_STRING_FAST = f"(begin {EVAL_FLAGS_FAST} (results))"
EVAL_STRING_COMPLETE = f"(begin {EVAL_FLAGS_COMPLETE} (results))"
