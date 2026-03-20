import sys
from PySide6.QtWidgets import QApplication
from controllers.app_controller import AppController
from config import Config

def main():
    app = QApplication(sys.argv)
    
    # Apply theme if available
    try:
        with open("resources/styles/theme.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass

    app_controller = AppController()
    app_controller.showMaximized()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()