from PySide6.QtCore import QObject, Slot

from models.editor_model import EditorModel
from views.editor_window_ui import EditorWindowUI  # Import the class, not a function


class EditorWindowController(QObject):
    """
    Controller that wires up signals and slots in a reactive architecture.
    Requires a QMainWindow instance for UI initialization.
    """

    def __init__(self, main_window):
        super().__init__()

        # Create view using the class-based approach
        self.ui = EditorWindowUI(main_window)
        main_window.setCentralWidget(self.ui)

        # Get component registry from the UI
        self.ui_components = self.ui.get_component_registry()

        # Create model but don't emit defaults yet
        self.model = EditorModel(emit_defaults=True)

        # Connect signals before emitting initial state
        self._connect_signals()

        # Now emit default values to flow through the same signal channels
        self.model.emit_state()

    def _connect_signals(self):
        """Connect UI signals to model and vice versa using the component registry."""
        ui = self.ui_components
        model = self.model

        # Connect definition view to model
        if definition_view := ui.get("definition_view"):
            definition_view.textChanged.connect(lambda text: model.update_text(text))

        # Connect test inputs and expected outputs to model
        for i in range(6):
            # Connect test inputs
            if test_input := ui.get(f"test_input_{i}"):
                test_input.textEdited.connect(
                    lambda text, idx=i: model.update_test_input(idx, text)
                )

            # Connect test expected outputs
            if test_expected := ui.get(f"test_expected_{i}"):
                test_expected.textEdited.connect(
                    lambda text, idx=i: model.update_test_expected(idx, text)
                )

        # Connect model state changes to UI updates
        model.state_changed.connect(self._handle_state_change)

    @Slot(object)
    def _handle_state_change(self, state):
        """React to state changes by updating UI components using factory methods."""
        ui = self.ui_components

        # Update definition text and status
        definition_text = state["definition"]["text"]
        definition_status = state["definition"]["status"]
        ui["create_slot"]("definition.view")(definition_text)
        ui["create_slot"]("definition.status")(definition_status)

        # Update best guess text and status
        best_guess_text = state["best_guess"]["text"]
        best_guess_status = state["best_guess"]["status"]
        ui["create_slot"]("best_guess.view")(best_guess_text)
        ui["create_slot"]("best_guess.status")(best_guess_status)

        # Update error output
        ui["create_slot"]("error_output")(state["error_output"])

        # Update test cases - use the registry helpers
        for i, test_data in enumerate(state["tests"]):
            if i < 6:  # Ensure we don't go out of bounds
                ui["create_test_updater"](i, "input")(test_data["input"])
                ui["create_test_updater"](i, "expected")(test_data["expected"])
                ui["create_test_updater"](i, "status")(test_data["status"])
