#!/usr/bin/env python3
import sys
import signal
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt
from qBarliman.controllers.editor_window_controller import EditorWindowController
from qBarliman.constants import warn, good, info, debug
from typing import cast


def signal_handler(signum, frame):
    warn("Received SIGINT. Shutting down gracefully...")
    app = QApplication.instance()
    if app:
        controller = cast(
            EditorWindowController,
            app.findChild(
                EditorWindowController,
                "",
                options=Qt.FindChildOption.FindChildrenRecursively,
            ),
        )
        if controller:
            controller.cancel_all_operations()  # Kill all subprocesses.
        QTimer.singleShot(0, app.quit)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    app = QApplication(sys.argv)

    window = EditorWindowController()

    try:
        primary_screen = app.primaryScreen()
        if primary_screen:
            screen_size = primary_screen.availableGeometry().size()
            window_width = min(1200, screen_size.width())
            window_height = min(1000, screen_size.height())
        else:
            window_width = 800
            window_height = 600

        # Configure main window
        window.mainWindow.setWindowTitle("qBarliman")
        window.mainWindow.resize(window_width, window_height)
        window.mainWindow.show()

    except Exception as e:
        warn(f"An error occurred: {e}")
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
