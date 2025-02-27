from PySide6.QtCore import QObject, Slot

from models.editor_model import EditorModel
from views.editor_window_ui import EditorWindowUI


class EditorWindowController(QObject):
    def __init__(self, main_window):
        super().__init__()

        self.ui = EditorWindowUI(main_window)
        main_window.setCentralWidget(self.ui)

        self.ui_components = self.ui.get_component_registry()
        self.model = EditorModel(debug_prints=True)

        self._connect_signals()
        self.model.state_changed.emit(self.model.state)

    def _connect_signals(self):
        ui = self.ui_components
        model = self.model

        if definition_view := ui.get("definition_view"):
            definition_view.textChanged.connect(
                lambda text: model.update("definition.text", text)
            )

        for i in range(6):
            if test_input := ui.get(f"test_input_{i}"):
                test_input.textChanged.connect(
                    lambda index, text, i=i: model.update(f"tests.{i}.input", text)
                )

            if test_expected := ui.get(f"test_expected_{i}"):
                test_expected.textChanged.connect(
                    lambda index, text, i=i: model.update(f"tests.{i}.expected", text)
                )

        model.state_changed.connect(self._handle_state_change)

    @Slot(object)
    def _handle_state_change(self, state):
        ui = self.ui_components

        ui["create_slot"]("definition.view")(state["definition"]["text"])
        ui["create_slot"]("definition.status")(state["definition"]["status"])

        ui["create_slot"]("best_guess.view")(state["best_guess"]["text"])
        ui["create_slot"]("best_guess.status")(state["best_guess"]["status"])

        ui["create_slot"]("error_output")(state["error_output"])
        ui["create_visibility_slot"]("error_output")(bool(state["error_output"]))

        for i, test_data in enumerate(state["tests"]):
            if i < 6:
                ui["create_test_updater"](i, "input")(test_data["input"])
                ui["create_test_updater"](i, "expected")(test_data["expected"])
                ui["create_test_updater"](i, "status")(test_data["status"])
