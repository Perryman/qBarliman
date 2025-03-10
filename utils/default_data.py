from typing import List

from config.constants import (
    DEFAULT_DEFINITIONS,
    DEFAULT_TEST_EXPECTED_OUTPUTS,
    DEFAULT_TEST_INPUTS,
)


def make_default_editor_state() -> dict:
    """Pure factory to create default editor state."""
    return {
        "definition": {
            "text": "\n".join(DEFAULT_DEFINITIONS),
            "status": ("Idle", None),
        },
        "best_guess": {"text": "", "status": ("Idle", None)},
        "error_output": "",
        "tests": create_default_tests(),
    }


def create_default_tests(num_tests: int = 6) -> List[dict]:
    """Create a list of default test dictionaries."""
    tests = []
    for i in range(num_tests):
        input_text = DEFAULT_TEST_INPUTS[i] if i < len(DEFAULT_TEST_INPUTS) else ""
        expected_text = (
            DEFAULT_TEST_EXPECTED_OUTPUTS[i]
            if i < len(DEFAULT_TEST_EXPECTED_OUTPUTS)
            else ""
        )
        tests.append(
            {"input": input_text, "expected": expected_text, "status": ("Empty", None)}
        )
    return tests


def validate_editor_state(state: dict) -> dict:
    """Return a validated editor state with proper status set."""
    # Apply simple validation logic (pure function)
    is_valid = bool(state["definition"]["text"].strip())
    # Example: Update definition status based on validity
    if is_valid:
        state["definition"]["status"] = ("Valid", None)
    else:
        state["definition"]["status"] = ("Invalid", None)
    return state


def ensure_min_tests(state: dict, min_tests: int = 6) -> dict:
    """Ensure test input/output lists are at least min_tests long."""
    tests = state["tests"]
    while len(tests) < min_tests:
        tests.append({"input": "", "expected": "", "status": ("Empty", None)})
    state["tests"] = tests
    return state
