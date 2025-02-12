#!/usr/bin/env python3
import signal
import sys

from PySide6.QtWidgets import QApplication

from qBarliman.controllers.editor_window_controller import EditorWindowController


def signal_handler(signum, frame):
    """Handle SIGINT (Ctrl+C) and SIGTERM gracefully."""
    print("Exiting...")
    QApplication.quit()


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    app = QApplication(sys.argv)
    EditorWindowController()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
