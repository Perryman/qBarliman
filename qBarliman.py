#!/usr/bin/env python3
import sys, signal
from PyQt6.QtWidgets import QApplication, QMainWindow
from qBarliman.controllers.editor_window_controller import EditorWindowController

def signal_handler(signum, frame):
    print("Received SIGINT. Shutting down gracefully...")
    window.cancel_all_operations()  # Kill all subprocesses.
    QApplication.quit()

def main():
    app = QApplication(sys.argv)
    global window
    window = EditorWindowController()
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        window.loadInterpreterCode("interp")  # Load the interpreter code
        primary_screen = app.primaryScreen()
        if primary_screen:
            screen_size = primary_screen.availableGeometry().size()
            window_width = min(1200, screen_size.width())
            window_height = min(1000, screen_size.height())
        else:
            window_width = 800
            window_height = 600

        window.setWindowTitle("qBarliman")
        window.resize(window_width, window_height)
        window.show()
    except Exception as e:
        print("Failed to load interpreter code. Exiting...")
        sys.exit(1)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
