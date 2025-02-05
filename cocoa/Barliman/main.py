import sys
from PyQt6.QtWidgets import QApplication
from editor_window_controller import EditorWindowController

def main():
    app = QApplication(sys.argv)
    window = EditorWindowController()
    window.resize(800, 600)
    window.show()
    # Simulate AppDelegate functionality by ensuring cleanup is called on exit
    app.aboutToQuit.connect(window.cleanup)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
