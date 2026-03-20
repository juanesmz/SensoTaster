from PySide6.QtCore import QObject
from navigation.router import router

class MainMenuController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view
        
        # Connect signals
        self.view.ui.btnExperiment.clicked.connect(lambda: router.go_to("experiment"))
        self.view.ui.btnVisualization.clicked.connect(lambda: router.go_to("visualization"))
        self.view.ui.btnAnalysis.clicked.connect(lambda: router.go_to("analysis"))
        self.view.ui.btnReturn.clicked.connect(lambda: router.go_to("login"))
