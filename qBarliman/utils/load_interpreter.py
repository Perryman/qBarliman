import os
from typing import List

from qBarliman.constants import CORE_FULLPATH
from qBarliman.utils import log as l


def load_interpreter_code(CORE_FULLPATH: List[str] = CORE_FULLPATH) -> str:
    """Load the miniKanren interpreter code from files"""
    code = ""
    try:
        # Load core miniKanren files
        for path in CORE_FULLPATH:
            if not os.path.exists(path):
                l.warn(f"Error: Could not find {path}")
                return ""
            with open(path, "r") as f:
                code += f.read() + "\n"
                l.good(f"Loaded {path}")

        return code

    except Exception as e:
        l.warn(f"Error loading interpreter code: {e}")
        return ""
