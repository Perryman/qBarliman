from qBarliman.constants import warn, good, CORE_FULLPATH
import os
from typing import List


def load_interpreter_code(CORE_FULLPATH: List[str] = CORE_FULLPATH) -> str:
    """Load the miniKanren interpreter code from files"""
    code = ""
    try:
        # Load core miniKanren files
        for path in CORE_FULLPATH:
            if not os.path.exists(path):
                warn(f"Error: Could not find {path}")
                return ""
            with open(path, "r") as f:
                code += f.read() + "\n"
                good(f"Loaded {path}")

        return code

    except Exception as e:
        warn(f"Error loading interpreter code: {e}")
        return ""
