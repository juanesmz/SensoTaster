from PySide6.QtCore import QObject, QTimer, Qt, QSize
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QPushButton, QListWidget, QStackedWidget, QListWidgetItem,
    QWidget, QHBoxLayout, QLabel,
)
from navigation.router import router
from views.experiment.cleaning_view import CleaningView
from views.experiment.emg_view import EMGView
from views.experiment.gas_view import GasView
from views.experiment.microphone_view import MicrophoneView
from views.experiment.imaging_view import ImagingView
from views.experiment.configuration_view import ConfigurationView
from controllers.experiment.emg_controller import EmgController
from controllers.experiment.microphone_controller import MicrophoneController
from controllers.experiment.gas_controller import GasController
from controllers.experiment.cleaning_controller import CleaningController
from controllers.experiment.imaging_controller import ImagingController
from controllers.experiment.configuration_controller import ConfigurationController

# Colores
ACTIVE_BG     = "#D5D5D5"
TRANSPARENT   = "transparent"
CHECK_GRAY    = "#A0A0A0"
CHECK_GREEN   = "#4CAF50"
CHECK_RED     = "#F44336"

SIDEBAR_SECTIONS = [
    "Limpieza de cabina",
    "Sensores de Gas",
    "Sensores EMG",
    "Micrófonos",
    "Cámaras",
    "Configuración",
]

# Estilos para el indicador (checkbox visual)
INDICATOR_STYLE = """
    QLabel {{
        background-color: {color};
        border-radius: 5px;
        min-width: 24px;
        max-width: 24px;
        min-height: 24px;
        max-height: 24px;
    }}
"""

# Estilos del texto del item
TEXT_STYLE_ACTIVE = """
    QLabel {{
        font-family: 'Segoe UI';
        font-size: 14pt;
        font-weight: bold;
        color: #333333;
        background: transparent;
    }}
"""

TEXT_STYLE_NORMAL = """
    QLabel {{
        font-family: 'Segoe UI';
        font-size: 14pt;
        font-weight: normal;
        color: #333333;
        background: transparent;
    }}
"""

# Estilo del contenedor del item
ROW_STYLE = """
    QWidget#sidebarRow {{
        background-color: {bg};
        border-radius: 8px;
        padding: 4px;
    }}
"""

SKIP_STYLE_GREEN = """
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        padding: 15px;
        margin-left: 20px;
        margin-right: 20px;
        margin-top: 5px;
        margin-bottom: 5px;
        font-family: 'Segoe UI';
        font-size: 14pt;
        font-weight: bold;
        border: none;
    }
    QPushButton:hover { background-color: #2E7D32; }
    QPushButton:pressed { background-color: #1B5E20; }
"""

SKIP_STYLE_ORANGE = """
    QPushButton {
        background-color: #FF9800;
        color: white;
        border-radius: 10px;
        padding: 15px;
        margin-left: 20px;
        margin-right: 20px;
        margin-top: 5px;
        margin-bottom: 5px;
        font-family: 'Segoe UI';
        font-size: 14pt;
        font-weight: bold;
        border: none;
    }
    QPushButton:hover { background-color: #F57C00; }
    QPushButton:pressed { background-color: #E65100; }
"""

NEXT_STYLE_STANDARD = """
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        padding: 15px;
        margin-top: 5px;
        margin-bottom: 5px;
        margin-left: 5px;
        margin-right: 20px;
        font-family: 'Segoe UI';
        font-size: 14pt;
        font-weight: bold;
        border: none;
    }
    QPushButton:hover { background-color: #2E7D32; }
    QPushButton:pressed { background-color: #1B5E20; }
    QPushButton:disabled { background-color: #A5D6A7; color: #E0E0E0; }
"""

NEXT_STYLE_ALONE = """
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        padding: 15px;
        margin-top: 5px;
        margin-bottom: 5px;
        margin-left: 20px;
        margin-right: 20px;
        font-family: 'Segoe UI';
        font-size: 14pt;
        font-weight: bold;
        border: none;
    }
    QPushButton:hover { background-color: #2E7D32; }
    QPushButton:pressed { background-color: #1B5E20; }
    QPushButton:disabled { background-color: #A5D6A7; color: #E0E0E0; }
"""


class ExperimentController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view

        # Connect btnReturn
        btn_return = self.view.ui.findChild(QPushButton, "btnReturn")
        if btn_return:
            btn_return.clicked.connect(lambda: router.go_to("main_menu"))

        # Initialize Sub-Views
        self.cleaning_view = CleaningView()
        self.emg_view = EMGView()
        self.gas_view = GasView()
        self.microphone_view = MicrophoneView()
        self.imaging_view = ImagingView()
        self.configuration_view = ConfigurationView()

        # Sub-controladores
        self.emg_controller = EmgController(self.emg_view)
        self.microphone_controller = MicrophoneController(self.microphone_view)
        self.gas_controller = GasController(self.gas_view)
        self.cleaning_controller = CleaningController(self.cleaning_view)
        self.imaging_controller = ImagingController(self.imaging_view)
        self.configuration_controller = ConfigurationController(
            self.configuration_view,
            self.emg_controller,
            self.microphone_controller,
            self # Para acceder a self._checked y self._reds
        )

        # ── Widgets ────────────────────────────────────────────────
        self._sidebar: QListWidget = self.view.ui.findChild(QListWidget, "sidebarMenu")
        self._stack: QStackedWidget = self.view.ui.findChild(QStackedWidget, "contentStack")
        self._btn_next: QPushButton = self.view.ui.findChild(QPushButton, "btnStartExperiment")
        self._btn_prev: QPushButton = self.view.ui.findChild(QPushButton, "btnPrevSection")
        self._btn_skip: QPushButton = self.view.ui.findChild(QPushButton, "btnSkipSection")

        if self._stack:
            self._stack.addWidget(self.cleaning_view)
            self._stack.addWidget(self.gas_view)
            self._stack.addWidget(self.emg_view)
            self._stack.addWidget(self.microphone_view)
            self._stack.addWidget(self.imaging_view)
            self._stack.addWidget(self.configuration_view)

        # ── Sidebar personalizado ──────────────────────────────────
        self._section_widgets: list[dict] = []  # {row, indicator, label}
        self._checked: list[bool] = [False] * len(SIDEBAR_SECTIONS)
        self._reds: list[bool] = [False] * len(SIDEBAR_SECTIONS)
        self._current_index = 0

        if self._sidebar:
            self._sidebar.setSelectionMode(QListWidget.SelectionMode.NoSelection)
            self._sidebar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            # Limpiar items predefinidos del .ui
            self._sidebar.clear()
            self._sidebar.setStyleSheet("""
                QListWidget {
                    background-color: transparent;
                    border: none;
                    outline: none;
                }
                QListWidget::item {
                    padding: 2px 4px;
                }
            """)

            for text in SIDEBAR_SECTIONS:
                self._add_sidebar_item(text)

            self._refresh_sidebar()

        # ── Botones de navegación ──────────────────────────────────
        if self._btn_next:
            self._btn_next.clicked.connect(self._on_next_section)
        if self._btn_prev:
            self._btn_prev.clicked.connect(self._on_prev_section)
        if self._btn_skip:
            self._btn_skip.clicked.connect(self._on_skip_section)

        self._update_button_states()

        if self._stack:
            self._stack.setCurrentIndex(0)

    # ── Crear items del sidebar ────────────────────────────────────
    def _add_sidebar_item(self, text: str):
        """Crea un item del sidebar con indicador (checkbox visual) + label."""
        item = QListWidgetItem()
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)

        # Widget contenedor
        row = QWidget()
        row.setObjectName("sidebarRow")
        h_lay = QHBoxLayout(row)
        h_lay.setContentsMargins(10, 10, 10, 10)
        h_lay.setSpacing(12)

        # Indicador (reemplaza el checkbox nativo)
        indicator = QLabel()
        indicator.setFixedSize(24, 24)
        indicator.setStyleSheet(INDICATOR_STYLE.format(color=CHECK_GRAY))

        # Texto
        label = QLabel(text)
        label.setStyleSheet(TEXT_STYLE_NORMAL.format())

        h_lay.addWidget(indicator)
        h_lay.addWidget(label, 1)

        item.setSizeHint(QSize(0, 54))
        self._sidebar.addItem(item)
        self._sidebar.setItemWidget(item, row)

        self._section_widgets.append({
            "item": item,
            "row": row,
            "indicator": indicator,
            "label": label,
        })

    # ── Refrescar apariencia del sidebar ───────────────────────────
    def _refresh_sidebar(self):
        """Actualiza fondos, negritas e indicadores de todos los items."""
        for i, entry in enumerate(self._section_widgets):
            is_active = (i == self._current_index)
            is_done = self._checked[i]
            is_red = self._reds[i]

            # Fondo del item
            bg = ACTIVE_BG if is_active else TRANSPARENT
            entry["row"].setStyleSheet(ROW_STYLE.format(bg=bg))

            # Texto en negrita si activo
            style = TEXT_STYLE_ACTIVE if is_active else TEXT_STYLE_NORMAL
            entry["label"].setStyleSheet(style.format())

            # Indicador: verde si completado, gris si no
            if is_red:
                color = CHECK_RED
            else:
                color = CHECK_GREEN if is_done else CHECK_GRAY
            entry["indicator"].setStyleSheet(INDICATOR_STYLE.format(color=color))

            # Bloquear visualmente "Configuración" si nada está activo
            if i == 5:
                any_active = any(self._checked[j] and not self._reds[j] for j in range(5))
                entry["row"].setEnabled(any_active)
                entry["label"].setEnabled(any_active)
                entry["indicator"].setEnabled(any_active)

        if self._current_index == 5:
            self.configuration_controller.refresh()

    # ── Estado de botones ──────────────────────────────────────────
    def _update_button_states(self):
        if not self._sidebar:
            return
        total = len(self._section_widgets)

        # ── Botón Anterior ──
        if self._btn_prev:
            # Ocultamos el botón si estamos en la primera sección (Limpieza)
            self._btn_prev.setVisible(self._current_index > 0)

        # ── Botón Siguiente ──
        if self._btn_next:
            if self._current_index == total - 1:
                # Ocultar en la sección de configuración
                self._btn_next.setVisible(False)
            else:
                self._btn_next.setVisible(True)
                self._btn_next.setText("Siguiente")
                
                # Si es la primera sección (Anterior oculto), expandimos el margen para que 
                # tenga el mismo ancho que "Omitir sección"
                if self._current_index == 0:
                    self._btn_next.setStyleSheet(NEXT_STYLE_ALONE)
                else:
                    self._btn_next.setStyleSheet(NEXT_STYLE_STANDARD)

        # ── Botón Omitir / Iniciar ──
        if self._btn_skip:
            if self._current_index == 5: # Configuración
                self._btn_skip.setText("Iniciar Experimentación")
                self._btn_skip.setStyleSheet(SKIP_STYLE_GREEN)
                self._btn_skip.setEnabled(True)
            else:
                self._btn_skip.setText("Omitir sección")
                self._btn_skip.setStyleSheet(SKIP_STYLE_ORANGE)
                # La sección de configuración es la única que requiere que haya algo activo para entrar
                # Pero aquí estamos en los botones inferiores.

    # ── Navegación ─────────────────────────────────────────────────
    def _handle_cleaning_skip(self) -> bool:
        """
        Maneja la lógica de saltar si el usuario está en Limpieza y no la ha completado.
        Retorna True si la navegación fue manejada aquí y no se debe avanzar de forma estándar.
        """
        from PySide6.QtWidgets import QMessageBox
        if self._current_index == 0:
            if not getattr(self.cleaning_controller, "cleaning_completed", False):
                reply = QMessageBox.warning(
                    self.view,
                    "Limpieza no realizada",
                    "Avanzar sin realizar limpieza hará que el uso de sensores de gases no sea permitido.\n¿Desea continuar de todos modos (saltando Sensores de Gas)?",
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
                )
                if reply == QMessageBox.StandardButton.Ok:
                    self._reds[0] = True
                    self._reds[1] = True
                    self._checked[0] = True
                    self._checked[1] = True
                    
                    self._current_index = 2  # Saltar a Sensores EMG
                    self._stack.setCurrentIndex(self._current_index)
                    self._refresh_sidebar()
                    self._update_button_states()
                return True
        return False

    def _handle_gas_skip(self) -> bool:
        """
        Maneja la lógica al intentar salir de la sección de Gas.
        Si no hay una PCB seleccionada, advierte que el módulo de gases no se activará 
        y salta a la sección de EMG.
        """
        from PySide6.QtWidgets import QMessageBox
        if self._current_index == 1:
            if not getattr(self.gas_controller, "has_selected_pcb", False):
                QMessageBox.information(
                    self.view,
                    "Módulo de Gas inactivo",
                    "No se ha seleccionado una configuración de PCB. El módulo de gases no se activará para este experimento.",
                    QMessageBox.StandardButton.Ok
                )
                self._reds[1] = True
                self._checked[1] = True
                self._current_index = 2 # Ir a Sensores EMG
                self._stack.setCurrentIndex(self._current_index)
                self._refresh_sidebar()
                self._update_button_states()
                return True
        return False

    def _handle_emg_skip(self) -> bool:
        """
        Maneja la lógica al intentar salir de la sección de EMG.
        Si no hay sensores seleccionados, advierte que el módulo de EMG no se activará 
        pero permite continuar a Micrófonos.
        """
        from PySide6.QtWidgets import QMessageBox
        if self._current_index == 2:
            if not getattr(self.emg_controller, "has_selected_sensors", False):
                reply = QMessageBox.warning(
                    self.view,
                    "Sin sensores EMG",
                    "No ha seleccionado sensores de EMG. El módulo de electromiografía no se activará para este experimento.\n¿Desea continuar a la configuración de micrófonos?",
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
                )
                if reply == QMessageBox.StandardButton.Ok:
                    self._reds[2] = True
                    self._checked[2] = True
                    self._current_index = 3 # Ir a Micrófonos
                    self._stack.setCurrentIndex(self._current_index)
                    self._refresh_sidebar()
                    self._update_button_states()
                return True
        return False

    def _handle_microphone_skip(self) -> bool:
        """
        Maneja la lógica de validación de micrófonos al intentar salir de la sección.
        1. Si hay EMG pero no hay Mic, solo se activa EMG.
        2. Si hay ambos, deben coincidir en cantidad.
        """
        from PySide6.QtWidgets import QMessageBox
        if self._current_index == 3:
            num_emg = getattr(self.emg_controller, "num_selected_sensors", 0)
            num_mic = getattr(self.microphone_controller, "num_selected_microphones", 0)
            
            # Caso 1: Hay EMG pero NO hay Micrófonos
            if num_emg > 0 and num_mic == 0:
                reply = QMessageBox.information(
                    self.view,
                    "Sin micrófonos",
                    "No ha seleccionado micrófonos. Solo se activará el módulo de EMG.\n¿Desea continuar?",
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
                )
                if reply == QMessageBox.StandardButton.Ok:
                    self._reds[3] = True
                    self._checked[3] = True
                    self._current_index = 4 # Ir a Cámaras
                    self._stack.setCurrentIndex(self._current_index)
                    self._refresh_sidebar()
                    self._update_button_states()
                return True
            
            # Caso 2: Hay ambos, pero no coinciden
            elif num_emg > 0 and num_mic > 0 and num_emg != num_mic:
                QMessageBox.critical(
                    self.view,
                    "Error de coincidencia",
                    f"La cantidad de micrófonos ({num_mic}) debe ser igual a la cantidad de sensores EMG ({num_emg}).\nPor favor, ajuste la selección."
                )
                return True # Bloquea el avance
                
            # Caso 3: No hay EMG y no hay Micrófonos (ambas secciones omitidas)
            elif num_emg == 0 and num_mic == 0:
                self._reds[3] = True
                self._checked[3] = True
                self._current_index = 4
                self._stack.setCurrentIndex(self._current_index)
                self._refresh_sidebar()
                self._update_button_states()
                return True

        return False

    def _on_next_section(self):
        total = len(self._section_widgets)
        if self._current_index >= total - 1:
            return

        if self._handle_cleaning_skip():
            return
        if self._handle_gas_skip():
            return
        if self._handle_emg_skip():
            return
        if self._handle_microphone_skip():
            return

        # Marcar sección actual como completada
        self._checked[self._current_index] = True

        # Validar si se puede entrar a Configuración (índice 5)
        if self._current_index == 4: # Estamos en Cámaras, queremos ir a Configuración
             if not any(self._checked[i] and not self._reds[i] for i in range(5)):
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self.view, "Acceso denegado", "Debe activar al menos una sección para ingresar a Configuración.")
                return

        self._current_index += 1
        self._stack.setCurrentIndex(self._current_index)
        self._refresh_sidebar()
        self._update_button_states()

    def _on_skip_section(self):
        # Si estamos en la sección de Configuración, el botón inicia el experimento
        if self._current_index == 5:
            self._start_live_experiment()
            return

        total = len(self._section_widgets)
        if self._current_index >= total - 1:
            return

        if self._handle_cleaning_skip():
            return
        if self._handle_gas_skip():
            return
        if self._handle_emg_skip():
            return
        if self._handle_microphone_skip():
            return

        # Marcar sección actual como omitida (rojo)
        self._reds[self._current_index] = True
        self._checked[self._current_index] = True

        # Validar si se puede entrar a Configuración (si el siguiente es el último)
        if self._current_index == 4: # Viniendo de Cámaras
            if not any(self._checked[i] and not self._reds[i] for i in range(5)):
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self.view, "Acceso denegado", "Debe activar al menos una sección para ingresar a Configuración.")
                return

        self._current_index += 1
        self._stack.setCurrentIndex(self._current_index)
        self._refresh_sidebar()
        self._update_button_states()

    def _start_live_experiment(self):
        """Inicia el experimento en una nueva ventana sin sidebar."""
        # Preparamos los datos
        if hasattr(self, "running_exp_controller"):
            self.running_exp_controller.prepare_session(
                base_path=self.configuration_controller.get_base_path(),
                modules_status=self._checked,
                omitted_modules=self._reds,
                user_data=self.configuration_controller.get_user_data(),
                camera_index=self.imaging_controller.get_selected_camera_index(),
                roi=self.imaging_controller.get_roi_coordinates(),
                mic_list=self.microphone_controller.get_microphone_list(),
                emg_indices=self.emg_controller.get_active_sensor_indices(),
                gas_config=self.gas_controller.get_gas_config()
            )

        # Navegamos a la nueva página primero
        router.go_to("running_exp")
        
        # Iniciamos la captura y carpetas después de un breve delay para que cargue la UI
        QTimer.singleShot(500, self.running_exp_controller.start_session)

    def _on_prev_section(self):
        if self._current_index <= 0:
            return

        # Si regresamos de EMG (2)
        if self._current_index == 2:
            # Si tanto Limpieza como Gas se omitieron (porque faltó limpieza), volver al inicio
            if self._reds[0] and self._reds[1]:
                self._checked[1] = False
                self._reds[1] = False
                self._checked[0] = False
                self._reds[0] = False
                self._current_index = 0
            else:
                # Si limpieza sí se hizo, volver normalmente a Gas (aunque se haya omitido por falta de PCB)
                self._checked[1] = False
                self._reds[1] = False
                self._current_index = 1
        # Si regresamos de Cámaras (4) y Micrófonos (3) estaba omitido..
        elif self._current_index == 4 and (self._reds[3] or self._checked[3]):
            self._checked[3] = False
            self._reds[3] = False
            self._current_index = 3
        # Si regresamos de Micrófonos (3) y EMG (2) estaba omitido..
        elif self._current_index == 3 and (self._reds[2] or self._checked[2]):
            self._checked[2] = False
            self._reds[2] = False
            self._current_index = 2
        else:
            # Des-marcar la sección a la que volvemos
            self._checked[self._current_index - 1] = False
            self._reds[self._current_index - 1] = False
            self._current_index -= 1

        self._stack.setCurrentIndex(self._current_index)
        self._refresh_sidebar()
        self._update_button_states()
