from PySide6.QtCore import QObject
from PySide6.QtWidgets import QPushButton
from navigation.router import router

class LiveExperimentController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view
        
        btn_finish = self.view.ui.findChild(QPushButton, "btnFinish")
        if btn_finish:
            btn_finish.clicked.connect(lambda: router.go_to("main_menu"))
