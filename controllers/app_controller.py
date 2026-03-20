from PySide6.QtWidgets import QMainWindow, QStackedWidget
from views.login_view import LoginView
from views.main_menu_view import MainMenuView
from views.experiment.experiment_view import ExperimentView
from views.visualization_view import VisualizationView
from views.analysis_view import AnalysisView
from controllers.login_controller import LoginController
from controllers.main_menu_controller import MainMenuController
from controllers.experiment.experiment_controller import ExperimentController
from controllers.visualization_controller import VisualizationController
from controllers.analysis_controller import AnalysisController
from navigation.router import router
from config import Config

class AppController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Config.APP_NAME)
        self.resize(Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
        
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        
        # Initialize Views
        self.login_view = LoginView()
        self.main_menu_view = MainMenuView()
        self.experiment_view = ExperimentView()
        self.visualization_view = VisualizationView()
        self.analysis_view = AnalysisView()

        # Initialize Controllers
        self.login_controller = LoginController(self.login_view)
        self.main_menu_controller = MainMenuController(self.main_menu_view)
        self.experiment_controller = ExperimentController(self.experiment_view)
        self.visualization_controller = VisualizationController(self.visualization_view)
        self.analysis_controller = AnalysisController(self.analysis_view)
        
        # Add views to stack
        self.central_widget.addWidget(self.login_view)
        self.central_widget.addWidget(self.main_menu_view)
        self.central_widget.addWidget(self.experiment_view)
        self.central_widget.addWidget(self.visualization_view)
        self.central_widget.addWidget(self.analysis_view)
        
        # Subscribe to router
        router.navigate.connect(self.on_navigate)
        
        # Start at Login
        self.on_navigate("login")

    def on_navigate(self, route_name):
        if route_name == "login":
            self.central_widget.setCurrentWidget(self.login_view)
        elif route_name == "main_menu":
            self.central_widget.setCurrentWidget(self.main_menu_view)
        elif route_name == "experiment":
            self.central_widget.setCurrentWidget(self.experiment_view)
        elif route_name == "visualization":
            self.central_widget.setCurrentWidget(self.visualization_view)
        elif route_name == "analysis":
            self.central_widget.setCurrentWidget(self.analysis_view)
        else:
            print(f"Unknown route: {route_name}")
