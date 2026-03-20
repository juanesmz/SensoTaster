from PySide6.QtCore import QObject, Qt, QSize
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
from controllers.experiment.emg_controller import EmgController
from controllers.experiment.microphone_controller import MicrophoneController
from controllers.experiment.gas_controller import GasController
from controllers.experiment.cleaning_controller import CleaningController

# Colores
ACTIVE_BG     = "#D5D5D5"
TRANSPARENT   = "transparent"
CHECK_GRAY    = "#A0A0A0"
CHECK_GREEN   = "#4CAF50"

SIDEBAR_SECTIONS = [
    "Limpieza de cabina",
    "Sensores EMG",
    "Sensores de Gas",
    "Micrófonos",
    "Cámaras",
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

        # Sub-controladores
        self.emg_controller = EmgController(self.emg_view)
        self.microphone_controller = MicrophoneController(self.microphone_view)
        self.gas_controller = GasController(self.gas_view)
        self.cleaning_controller = CleaningController(self.cleaning_view)

        # ── Widgets ────────────────────────────────────────────────
        self._sidebar: QListWidget = self.view.ui.findChild(QListWidget, "sidebarMenu")
        self._stack: QStackedWidget = self.view.ui.findChild(QStackedWidget, "contentStack")
        self._btn_next: QPushButton = self.view.ui.findChild(QPushButton, "btnStartExperiment")
        self._btn_prev: QPushButton = self.view.ui.findChild(QPushButton, "btnPrevSection")

        if self._stack:
            self._stack.addWidget(self.cleaning_view)
            self._stack.addWidget(self.emg_view)
            self._stack.addWidget(self.gas_view)
            self._stack.addWidget(self.microphone_view)
            self._stack.addWidget(self.imaging_view)

        # ── Sidebar personalizado ──────────────────────────────────
        self._section_widgets: list[dict] = []  # {row, indicator, label}
        self._checked: list[bool] = [False] * len(SIDEBAR_SECTIONS)
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

            # Fondo del item
            bg = ACTIVE_BG if is_active else TRANSPARENT
            entry["row"].setStyleSheet(ROW_STYLE.format(bg=bg))

            # Texto en negrita si activo
            style = TEXT_STYLE_ACTIVE if is_active else TEXT_STYLE_NORMAL
            entry["label"].setStyleSheet(style.format())

            # Indicador: verde si completado, gris si no
            color = CHECK_GREEN if is_done else CHECK_GRAY
            entry["indicator"].setStyleSheet(INDICATOR_STYLE.format(color=color))

    # ── Estado de botones ──────────────────────────────────────────
    def _update_button_states(self):
        if not self._sidebar:
            return
        total = len(self._section_widgets)

        if self._btn_prev:
            self._btn_prev.setEnabled(self._current_index > 0)

        if self._btn_next:
            if self._current_index >= total - 1:
                self._btn_next.setText("Finalizar")
            else:
                self._btn_next.setText("Siguiente sección")

    # ── Navegación ─────────────────────────────────────────────────
    def _on_next_section(self):
        total = len(self._section_widgets)
        if self._current_index >= total - 1:
            return

        # Marcar sección actual como completada
        self._checked[self._current_index] = True

        self._current_index += 1
        self._stack.setCurrentIndex(self._current_index)
        self._refresh_sidebar()
        self._update_button_states()

    def _on_prev_section(self):
        if self._current_index <= 0:
            return

        # Des-marcar la sección a la que volvemos
        self._checked[self._current_index - 1] = False

        self._current_index -= 1
        self._stack.setCurrentIndex(self._current_index)
        self._refresh_sidebar()
        self._update_button_states()
