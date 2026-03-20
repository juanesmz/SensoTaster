from PySide6.QtCore import QObject
from PySide6.QtWidgets import QPushButton
from navigation.router import router

class AnalysisController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view
        btn_return = self.view.ui.findChild(QPushButton, "btnReturn")
        if btn_return:
            btn_return.clicked.connect(lambda: router.go_to("main_menu"))
        else:
            print("Warning: btnReturn not found in AnalysisView")
