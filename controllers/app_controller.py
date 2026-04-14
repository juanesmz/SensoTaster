from PySide6.QtWidgets import QMainWindow, QStackedWidget
from views.login_view import LoginView
from views.main_menu_view import MainMenuView
from views.experiment.experiment_view import ExperimentView
from views.visualization_view import VisualizationView
from views.analysis_view import AnalysisView
from views.settings_view import SettingsView
from views.experiment.live_experiment_view import LiveExperimentView # Can be removed if not used elsewhere, but I'll replace it
from views.experiment.running_exp_view import RunningExpView
from controllers.login_controller import LoginController
from controllers.main_menu_controller import MainMenuController
from controllers.experiment.experiment_controller import ExperimentController
from controllers.visualization_controller import VisualizationController
from controllers.analysis_controller import AnalysisController
from controllers.settings_controller import SettingsController
from controllers.experiment.live_experiment_controller import LiveExperimentController # Can be removed
from controllers.experiment.running_exp_controller import RunningExpController
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
        self.settings_view = SettingsView()
        self.live_experiment_view = LiveExperimentView()
        self.running_exp_view = RunningExpView()

        # Initialize Controllers
        self.login_controller = LoginController(self.login_view)
        self.main_menu_controller = MainMenuController(self.main_menu_view)
        self.experiment_controller = ExperimentController(self.experiment_view)
        self.visualization_controller = VisualizationController(self.visualization_view)
        self.analysis_controller = AnalysisController(self.analysis_view)
        self.settings_controller = SettingsController(self.settings_view)
        self.live_experiment_controller = LiveExperimentController(self.live_experiment_view)
        self.running_exp_controller = RunningExpController(self.running_exp_view)
        
        # Inyectar el controlador de ejecución en el de experimentos para la transición
        self.experiment_controller.running_exp_controller = self.running_exp_controller
        
        # Add views to stack
        self.central_widget.addWidget(self.login_view)
        self.central_widget.addWidget(self.main_menu_view)
        self.central_widget.addWidget(self.experiment_view)
        self.central_widget.addWidget(self.visualization_view)
        self.central_widget.addWidget(self.analysis_view)
        self.central_widget.addWidget(self.settings_view)
        self.central_widget.addWidget(self.live_experiment_view)
        self.central_widget.addWidget(self.running_exp_view)
        
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
        elif route_name == "settings":
            self.central_widget.setCurrentWidget(self.settings_view)
        elif route_name == "live_experiment":
            self.central_widget.setCurrentWidget(self.live_experiment_view)
        elif route_name == "running_exp":
            self.central_widget.setCurrentWidget(self.running_exp_view)
        else:
            print(f"Unknown route: {route_name}")
