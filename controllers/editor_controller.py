from PySide6.QtCore import QObject
from PySide6.QtWidgets import QLabel

from models.editor_model import EditorModel
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

        self.model = EditorModel(debug_prints=True)

        self.bind_ui_signals()

    def bind_ui_signals(self):
        """Connect UI component signals to model slots for reactive updates."""
        pass
