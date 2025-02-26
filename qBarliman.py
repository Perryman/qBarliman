import signal
import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from controllers.editor_window_controller import EditorWindowController


def signal_handler(signum, frame):
    """Handle SIGINT (Ctrl+C) and SIGTERM gracefully."""
    print("Exiting...")
    QApplication.quit()


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    main_window.controller = EditorWindowController(main_window)
    main_window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
