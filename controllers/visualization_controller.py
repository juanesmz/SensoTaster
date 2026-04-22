import os
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QPushButton, QTabWidget, QVBoxLayout, QFileDialog, QLineEdit, QMessageBox
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
        self._disable_tabs_initially()

    def _disable_tabs_initially(self):
        self.tab_widget = self.view.ui.findChild(QTabWidget, "tabWidget")
        if self.tab_widget:
            for i in range(self.tab_widget.count()):
                self.tab_widget.setTabEnabled(i, False)

    def _setup_connections(self):
        # Navigation
        btn_return = self.view.ui.findChild(QPushButton, "btnReturn")
        if btn_return:
            btn_return.clicked.connect(lambda: router.go_to("main_menu"))
        
        # Directory Selection
        btn_browse = self.view.ui.findChild(QPushButton, "btnBrowse")
        btn_visualize = self.view.ui.findChild(QPushButton, "btnVisualize")
        self.line_directory = self.view.ui.findChild(QLineEdit, "lineDirectory")
        
        if btn_browse:
            btn_browse.clicked.connect(self._select_directory)
        
        if btn_visualize:
            btn_visualize.clicked.connect(self._on_visualize_clicked)

    def _on_visualize_clicked(self):
        directory = self.line_directory.text().strip()
        if not directory:
            QMessageBox.warning(self.view, "Error", "Por favor seleccione un directorio primero.")
            return
        
        if not os.path.isdir(directory):
            QMessageBox.critical(self.view, "Error", "El directorio seleccionado no es válido.")
            return

        # Condition 1: Imagenes (exactly 10 files foto_1.jpg to foto_10.jpg)
        img_path = os.path.join(directory, "Imagenes")
        img_valid = False
        if os.path.isdir(img_path):
            files = [f.lower() for f in os.listdir(img_path) if f.lower().endswith(".jpg")]
            expected_files = {f"foto_{i}.jpg" for i in range(1, 11)}
            if set(files) == expected_files:
                img_valid = True

        # Condition 2: Sensores de Gases (single gases.csv)
        gas_path = os.path.join(directory, "Sensores de Gases")
        gas_valid = False
        if os.path.isdir(gas_path):
            files = [f.lower() for f in os.listdir(gas_path)]
            if len(files) == 1 and files[0] == "gases.csv":
                gas_valid = True

        # Condition 3: EMG (1-6 .csv files)
        emg_path = os.path.join(directory, "EMG")
        emg_valid = False
        if os.path.isdir(emg_path):
            files = [f for f in os.listdir(emg_path) if f.lower().endswith(".csv")]
            if 1 <= len(files) <= 6:
                emg_valid = True

        # Condition 4: Audio (1-6 .wav files)
        audio_path = os.path.join(directory, "Audio")
        audio_valid = False
        if os.path.isdir(audio_path):
            files = [f for f in os.listdir(audio_path) if f.lower().endswith(".wav")]
            if 1 <= len(files) <= 6:
                audio_valid = True

        # Update tabs state
        if self.tab_widget:
            self.tab_widget.setTabEnabled(0, gas_valid)   # Sensores Gases
            self.tab_widget.setTabEnabled(1, img_valid)   # Imagen
            self.tab_widget.setTabEnabled(2, audio_valid) # Audio
            self.tab_widget.setTabEnabled(3, emg_valid)   # Electromiografía
            
            # Load EMG data if valid
            if emg_valid:
                self.emg_controller.load_data(directory)
            
            # Load Audio data if valid
            if audio_valid:
                self.audio_controller.load_data(directory)
            
            # Optionally switch to the first enabled tab
            for i in range(self.tab_widget.count()):
                if self.tab_widget.isTabEnabled(i):
                    self.tab_widget.setCurrentIndex(i)
                    break
        
        if not (img_valid or gas_valid or emg_valid or audio_valid):
            QMessageBox.information(self.view, "Información", "No se encontró la estructura esperada en el directorio para activar los módulos.")

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
