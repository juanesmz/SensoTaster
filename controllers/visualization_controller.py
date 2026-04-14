from PySide6.QtCore import QObject
from PySide6.QtWidgets import QPushButton, QTabWidget, QVBoxLayout, QFileDialog, QLineEdit
from navigation.router import router

# Import modular components
from views.visualization.gas_sensors_view import GasSensorsView
from controllers.visualization.gas_sensors_controller import GasSensorsController
from views.visualization.imaging_view import ImagingView
from controllers.visualization.imaging_controller import ImagingController
from views.visualization.audio_view import AudioView
from controllers.visualization.audio_controller import AudioController
from views.visualization.emg_view import EMGView
from controllers.visualization.emg_controller import EMGController

class VisualizationController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view
        self._setup_connections()
        self._init_tabs()

    def _setup_connections(self):
        # Navigation
        btn_return = self.view.ui.findChild(QPushButton, "btnReturn")
        if btn_return:
            btn_return.clicked.connect(lambda: router.go_to("main_menu"))
        
        # Directory Selection
        btn_browse = self.view.ui.findChild(QPushButton, "btnBrowse")
        self.line_directory = self.view.ui.findChild(QLineEdit, "lineDirectory")
        
        if btn_browse:
            btn_browse.clicked.connect(self._select_directory)

    def _select_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self.view,
            "Seleccionar Directorio de Experimentación",
            ""
        )
        if directory:
            self.line_directory.setText(directory)
            # Notify sub-controllers if needed (optional for now)
            print(f"Directorio seleccionado: {directory}")

    def _init_tabs(self):
        # 1. Gas Sensors
        self.gas_view = GasSensorsView()
        self.gas_controller = GasSensorsController(self.gas_view)
        self._add_view_to_layout("verticalLayoutGas", self.gas_view)

        # 2. Imaging
        self.imaging_view = ImagingView()
        self.imaging_controller = ImagingController(self.imaging_view)
        self._add_view_to_layout("verticalLayoutImaging", self.imaging_view)

        # 3. Audio
        self.audio_view = AudioView()
        self.audio_controller = AudioController(self.audio_view)
        self._add_view_to_layout("verticalLayoutAudio", self.audio_view)

        # 4. EMG
        self.emg_view = EMGView()
        self.emg_controller = EMGController(self.emg_view)
        self._add_view_to_layout("verticalLayoutEMG", self.emg_view)

    def _add_view_to_layout(self, layout_name, view):
        layout = self.view.ui.findChild(QVBoxLayout, layout_name)
        if layout:
            layout.addWidget(view)
        else:
            print(f"Warning: Layout {layout_name} not found in Visualization UI")
