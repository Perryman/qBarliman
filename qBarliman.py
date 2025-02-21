#!/usr/bin/env python3
# qBarliman.py
"""Main application entry point for qBarliman.

This module serves as the bootstrap for the qBarliman application, a Qt-based GUI
for running miniKanren/Scheme queries. It initializes the main application window
and sets up the core application infrastructure.

Key responsibilities:
    - Application initialization and configuration
    - Main window creation
    - Global exception handling setup
    - Resource management initialization
    - Logging configuration

Dependencies:
    - PyQt6
    - EditorWindowController
"""

import signal
import sys

from PySide6.QtWidgets import QApplication

from controllers.editor_window_controller import EditorWindowController


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
