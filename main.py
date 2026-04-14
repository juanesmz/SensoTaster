import sys
import os

# Suprimir advertencia inofensiva de Qt sobre los márgenes de Windows y la barra de tareas (QWindowsWindow::setGeometry)
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"

from PySide6.QtWidgets import QApplication
from controllers.app_controller import AppController

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