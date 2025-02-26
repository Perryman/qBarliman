from PySide6.QtCore import QObject, Signal

from config.constants import (
    DEFAULT_DEFINITIONS,
    DEFAULT_TEST_EXPECTED_OUTPUTS,
    DEFAULT_TEST_INPUTS,
)


class EditorModel(QObject):
    """Model for editor state with smart updates and path-based state management."""

    state_changed = Signal(object)

    def __init__(self, emit_defaults=True):
        super().__init__()
        self._state = {
            "definition": {"text": "", "status": ("Idle", None)},
            "best_guess": {"text": "", "status": ("Idle", None)},
            "error_output": "",
            "tests": [],
        }
        self._apply_defaults()

        # Only emit state if emit_defaults is True
        if emit_defaults:
            self.state_changed.emit(self._state)

    def emit_state(self):
        """Explicitly emit the current state."""
        self.state_changed.emit(self._state)

    def _apply_defaults(self):
        """Apply default values to state."""
        self.update("definition.text", "\n".join(DEFAULT_DEFINITIONS))

        for i in range(
            max(len(DEFAULT_TEST_INPUTS), len(DEFAULT_TEST_EXPECTED_OUTPUTS))
        ):
            input_text = DEFAULT_TEST_INPUTS[i] if i < len(DEFAULT_TEST_INPUTS) else ""
            expected_text = (
                DEFAULT_TEST_EXPECTED_OUTPUTS[i]
                if i < len(DEFAULT_TEST_EXPECTED_OUTPUTS)
                else ""
            )
            self.update(f"tests.{i}.input", input_text)
            self.update(f"tests.{i}.expected", expected_text)

    def _update_state(self, path, value):
        """Update state at path and emit signal if changed.  Handles test validity."""
        keys = path.split(".")
        target = self._state
        for key in keys[:-1]:
            if key.isdigit():
                key = int(key)
                self._ensure_test_exists(key)  # Ensure the test exists!
            target = target[key]

        if target[keys[-1]] != value:
            target[keys[-1]] = value

            # Special handling for test status updates.
            if "tests" in keys and ("input" in keys or "expected" in keys):
                test_index = int(keys[keys.index("tests") + 1])
                self._update_test_validity(test_index)

            self.state_changed.emit(self._state)

    def update(self, path, value):
        """
        General purpose update method.

        Args:
            path (str): Dot-separated path to the value within the state (e.g., "definition.text", "tests.0.input").
            value: The new value.
        """
        self._update_state(path, value)

    def _update_test_validity(self, index):
        """Update the status of a test case based on input/expected."""
        test = self._state["tests"][index]
        has_input = bool(test["input"].strip())
        has_expected = bool(test["expected"].strip())

        if has_input and has_expected:
            status = ("Ready", None)
        elif has_input or has_expected:
            status = ("Invalid", None)
        else:
            status = ("Empty", None)
        self._update_state(f"tests.{index}.status", status)

    def _ensure_test_exists(self, index):
        """Ensure a test case exists at the given index."""
        while len(self._state["tests"]) <= index:
            self._state["tests"].append(
                {"input": "", "expected": "", "status": ("Empty", None)}
            )

    @property
    def state(self):
        return self._state

    def update_text(self, text):
        """Update definition text."""
        self.update("definition.text", text)

    def update_test_input(self, index, text):
        """Update test input."""
        self.update(f"tests.{index}.input", text.strip())

    def update_test_expected(self, index, text):
        """Update test expected output."""
        self.update(f"tests.{index}.expected", text.strip())

    def update_definition_status(self, status):
        """Update definition status."""
        self.update("definition.status", status)

    def update_best_guess(self, text, status="Ready"):
        """Update best guess with new text and status."""
        self.update("best_guess.text", text)
        self.update("best_guess.status", status)

    def update_error_output(self, text):
        """Update error output."""
        self.update("error_output", text)

    def update_test_status(self, index, status):
        """Update test status."""
        self.update(f"tests.{index}.status", status)

    def get_active_tests(self):
        """Return only the valid, complete tests."""
        return [
            test
            for test in self._state["tests"]
            if test["input"].strip() and test["expected"].strip()
        ]

    def get_query_data(self):
        """Generate a clean query object with only valid tests."""
        return {
            "definition": self._state["definition"]["text"],
            "tests": self.get_active_tests(),
        }
