#!/usr/bin/env python3

import sys
import traceback
from PySide6.QtWidgets import QApplication
from qBarliman.controllers.editor_window_controller import EditorWindowController
from qBarliman.constants import *
from qBarliman.models.scheme_document import SchemeDocument
from qBarliman.views.editor_window_ui import EditorWindowUI

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    
    # Create the model
    model = SchemeDocument(
        definition_text="",
        test_inputs=[""] * 6,
        test_expected=[""] * 6
    )
    
    # Create the view
    view = EditorWindowUI()
    
    # Create the controller
    controller = EditorWindowController()
    controller.set_model(model)
    controller.set_view(view)
    
    # Show the view
    view.show()
    
    # Start the application
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
