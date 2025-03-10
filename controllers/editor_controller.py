from PySide6.QtCore import QObject
from PySide6.QtWidgets import QLabel

from models.editor_model import EditorModel
from utils.default_data import (
    ensure_min_tests,
    make_default_editor_state,
    validate_editor_state,
)
from views.editor_ui import EditorUI
from widgets.scheme_editor_line_edit import SchemeEditorLineEdit as scmLineEdit
from widgets.scheme_editor_text_edit import SchemeEditorTextEdit as scmTextEdit


class EditorController(QObject):
    def __init__(self, main_window):
        super().__init__()

        self.component_registry = {
            "definition": {
                "type": "vertical",
                "rows": [
                    {"type": "horizontal", "order": ["label", "status"]},
                    {"type": "single", "order": ["widget"]},
                ],
                "components": {
                    "label": {
                        "widget": QLabel("Definition:", main_window),
                        "role": "section_label",
                    },
                    "widget": {
                        "widget": scmTextEdit(main_window),
                        "role": "editor",
                    },
                    "status": {
                        "widget": QLabel("Idle", main_window),
                        "role": "status_indicator",
                    },
                },
            },
            "best_guess": {
                "type": "vertical",
                "rows": [
                    {"type": "horizontal", "order": ["label", "status"]},
                    {"type": "single", "order": ["widget"]},
                ],
                "components": {
                    "label": {
                        "widget": QLabel("Best Guess:", main_window),
                        "role": "section_label",
                    },
                    "widget": {
                        "widget": scmTextEdit(main_window),
                        "role": "editor",
                    },
                    "status": {
                        "widget": QLabel("Idle", main_window),
                        "role": "status_indicator",
                    },
                },
            },
            "tests": {
                "type": "grid",
                "components": {
                    "rows": {
                        i: {
                            "test_input": {
                                "widget": scmLineEdit(main_window, test_num=i),
                                "role": "test_input",
                            },
                            "test_expected": {
                                "widget": scmLineEdit(main_window, test_num=i),
                                "role": "test_expected",
                            },
                            "status": {
                                "widget": QLabel("Idle", main_window),
                                "role": "status_indicator",
                            },
                        }
                        for i in range(6)
                    }
                },
            },
        }

        self.ui = EditorUI(main_window, self.component_registry)
        main_window.setCentralWidget(self.ui)

        # Create default data
        default_state = make_default_editor_state()
        default_state = validate_editor_state(default_state)
        default_state = ensure_min_tests(default_state)

        # Instantiate EditorModel with the processed default data
        self.model = EditorModel(initial_state=default_state, debug_prints=True)

        self.bind_ui_signals()
        self.update_ui_from_state(self.model._state)

    def bind_ui_signals(self):
        """Connect UI component signals to model slots for reactive updates."""
        # Connect definition text changes to the model
        definition_editor = self.component_registry["definition"]["components"][
            "widget"
        ]["widget"]
        definition_editor.textChanged.connect(
            lambda text: self.model.update("definition.text", text)
        )

        # Connect test input and expected changes to the model
        for i in range(6):
            test_input_editor = self.component_registry["tests"]["components"]["rows"][
                i
            ]["test_input"]["widget"]
            test_expected_editor = self.component_registry["tests"]["components"][
                "rows"
            ][i]["test_expected"]["widget"]
            test_input_editor.textChanged.connect(
                lambda test_num, text: self.model.update(
                    f"tests.{test_num}.input", text
                )
            )
            test_expected_editor.textChanged.connect(
                lambda test_num, text: self.model.update(
                    f"tests.{test_num}.expected", text
                )
            )

        # Connect model's state_changed signal to the update_ui_from_state slot
        self.model.state_changed.connect(self.update_ui_from_state)

    def update_ui_from_state(self, state):
        """Update UI components based on the current state."""
        # Update definition text
        definition_text = state["definition"]["text"]
        definition_editor = self.component_registry["definition"]["components"][
            "widget"
        ]["widget"]
        definition_editor.setText(definition_text)

        # Update test inputs and expected outputs
        for i in range(6):
            test_input_text = state["tests"][i]["input"]
            test_expected_text = state["tests"][i]["expected"]
            test_input_editor = self.component_registry["tests"]["components"]["rows"][
                i
            ]["test_input"]["widget"]
            test_expected_editor = self.component_registry["tests"]["components"][
                "rows"
            ][i]["test_expected"]["widget"]
            test_input_editor.setText(test_input_text)
            test_expected_editor.setText(test_expected_text)
