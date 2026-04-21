import os
import pyqtgraph as pg
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QLabel, QComboBox,
    QFrame, QScrollArea, QSizePolicy, QPushButton, QCheckBox,
    QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QTimer
from views.base_view import BaseView


# ── Estilos reutilizables ──────────────────────────────────────────
COMBO_STYLE = """
QComboBox {
    font-size: 12px;
    padding: 4px 8px;
    border: 1px solid #CCCCCC;
    border-radius: 6px;
    background-color: #FFFFFF;
    color: #000000;
}
QComboBox:hover {
    border-color: #4CAF50;
}
QComboBox::drop-down {
    border: none;
    width: 22px;
}
QComboBox QAbstractItemView {
    font-size: 11px;
    background-color: #FFFFFF;
    color: #000000;
    selection-background-color: #E8F5E9;
    selection-color: #2E7D32;
}
"""

HEADER_STYLE = """
    font-size: 16px;
    font-weight: bold;
    color: white;
    background-color: #4CAF50;
    padding: 8px 12px;
"""

ROW_HEIGHT = 64

SENSOR_LABEL_STYLE = """
    font-size: 16px;
    font-weight: bold;
    color: #4CAF50;
    padding: 6px 12px;
"""

DEFAULT_ROW_COUNT = 13


class NoScrollComboBox(QComboBox):
    """QComboBox que ignora el evento de la rueda del ratón para evitar cambios accidentales al scrollear."""
    def wheelEvent(self, event):
        event.ignore()


class GasView(BaseView):
    sensor_deleted = Signal(str)  # emite el nombre del sensor eliminado

    def __init__(self):
        super().__init__(os.path.join("ui", "experiment", "pages", "gas.ui"))
        self._row_widgets: list[dict] = []
        self._sensor_list_entries: list[dict] = []
        self._setup_table()
        self._setup_sensor_list()
        self._setup_visualization_tab()

    def _setup_visualization_tab(self):
        """Inicializa los componentes de la pestaña de visualización."""
        if not self.ui:
            return

        self.btn_start_stop = self.ui.findChild(QPushButton, "btnStartStopVis")
        self.layout_checkboxes = self.ui.findChild(QGridLayout, "layoutSensorCheckboxes")
        self.plot_container = self.ui.findChild(QWidget, "plotContainer")
        self.layout_plot = self.ui.findChild(QVBoxLayout, "layoutPlot")

        # Configurar pyqtgraph
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        pg.setConfigOptions(antialias=True)

        self.plot_widget = pg.PlotWidget(title="Comportamiento de Sensores de Gas")
        self.plot_widget.setLabel('left', 'Voltaje', units='V')
        self.plot_widget.setLabel('bottom', 'Tiempo', units='s')
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True)
        
        if self.layout_plot:
            self.layout_plot.addWidget(self.plot_widget)

        self._curves = {}
        self._sensor_checkboxes = {}

    def update_sensor_visualization_list(self, active_sensors: list[tuple[str, str]]):
        """
        Crea checkboxes para los sensores que tienen una referencia asignada en una grilla de 5 columnas.
        active_sensors: lista de (SG_N, Referencia)
        """
        if not self.layout_checkboxes:
            return

        # Limpiar checkboxes anteriores
        while self.layout_checkboxes.count():
            item = self.layout_checkboxes.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self._sensor_checkboxes.clear()
        
        # Paleta de colores para las curvas
        colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', 
                  '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', 
                  '#008080', '#e6beff', '#9a6324']

        col_count = 2
        active_idx = 0

        for i, (sensor_id, ref) in enumerate(active_sensors):
            if ref and ref != "N/A":
                cb = QCheckBox(ref)
                cb.setChecked(True)
                cb.setStyleSheet("font-size: 11px; font-weight: bold; color: #333333;")
                
                row = active_idx // col_count
                col = active_idx % col_count
                self.layout_checkboxes.addWidget(cb, row, col)

                self._sensor_checkboxes[sensor_id] = {
                    "checkbox": cb,
                    "color": colors[active_idx % len(colors)],
                    "ref": ref
                }
                active_idx += 1

    def get_selected_visualized_sensors(self) -> list[str]:
        """Retorna los IDs de sensores (SG_N) seleccionados para visualizar."""
        return [sid for sid, data in self._sensor_checkboxes.items() if data["checkbox"].isChecked()]

    def setup_curves(self, sensor_ids: list[str]):
        """Prepara las curvas en el gráfico para los sensores indicados."""
        self.plot_widget.clear()
        self._curves.clear()
        
        for sid in sensor_ids:
            if sid in self._sensor_checkboxes:
                data = self._sensor_checkboxes[sid]
                curve = self.plot_widget.plot(
                    pen=pg.mkPen(color=data["color"], width=2),
                    name=f"{sid}: {data['ref']}"
                )
                self._curves[sid] = curve

    def update_plot(self, x_data, y_map: dict[str, list[float]]):
        """Actualiza los datos del gráfico con una ventana fija de 3 segundos."""
        for sid, curve in self._curves.items():
            if sid in y_map:
                curve.setData(x_data, y_map[sid])
        
        if x_data:
            # Forzar que el eje X siempre muestre los últimos 3 segundos
            last_t = x_data[-1]
            self.plot_widget.setXRange(last_t - 3, last_t, padding=0)

    # ── Tabla deslizable ───────────────────────────────────────────
    def _setup_table(self):
        """Construye la tabla con header fijo + filas deslizables dentro del scrollArea."""
        if not self.ui:
            return

        frame_right: QFrame = self.ui.findChild(QFrame, "frameRight")
        scroll: QScrollArea = self.ui.findChild(QScrollArea, "scrollAreaTable")
        if frame_right is None or scroll is None:
            return

        # ── Bordes redondeados para la tabla ───────────────────────
        frame_right.setStyleSheet("""
            QFrame#frameRight {
                border: 1px solid #CCCCCC;
                border-radius: 10px;
            }
        """)
        scroll.setStyleSheet(scroll.styleSheet() + """
            QScrollArea { border: none; border-radius: 10px; }
        """)

        # ── Header fijo (fuera del scroll) ─────────────────────────
        header = QWidget()
        header.setStyleSheet("background-color: #4CAF50; border-top-left-radius: 9px; border-top-right-radius: 9px;")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(0)

        lbl_sensor = QLabel("Sensor")
        lbl_sensor.setStyleSheet(HEADER_STYLE)
        lbl_sensor.setFixedWidth(120)
        lbl_sensor.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_ref = QLabel("Referencia")
        lbl_ref.setStyleSheet(HEADER_STYLE)
        lbl_ref.setAlignment(Qt.AlignmentFlag.AlignCenter)

        h_lay.addWidget(lbl_sensor)
        h_lay.addWidget(lbl_ref, 1)

        # Insertar el header antes del scroll en el layout del frame derecho
        right_layout = frame_right.layout()
        
        # Buscar el índice del título dinámico si existe
        insert_pos = 0
        for i in range(right_layout.count()):
            item = right_layout.itemAt(i)
            if item.widget() and item.widget().objectName() == "lblTableTitle":
                insert_pos = i + 1
                break
                
        right_layout.insertWidget(insert_pos, header)

        # ── Contenedor de filas dentro del scroll ──────────────────
        container = QWidget()
        self._table_layout = QVBoxLayout(container)
        self._table_layout.setContentsMargins(0, 0, 0, 0)
        self._table_layout.setSpacing(0)

        # ── Filas por defecto (agregar secuencialmente) ────────────
        for i in range(DEFAULT_ROW_COUNT):
            self._append_row_widget(i + 1)

        # Espaciador final para empujar filas hacia arriba
        self._table_layout.addStretch(1)

        scroll.setWidget(container)
        scroll.setWidgetResizable(True)

    def _create_row_widget(self, number: int) -> tuple[QWidget, dict]:
        """Crea un widget de fila (SG_N + QComboBox) y devuelve (widget, entry)."""
        row = QWidget()
        row.setFixedHeight(ROW_HEIGHT)
        bg = "#FFFFFF" if number % 2 != 0 else "#F5F5F5"
        row.setStyleSheet(f"background-color: {bg};")

        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lbl = QLabel(f"SG_{number}")
        lbl.setStyleSheet(SENSOR_LABEL_STYLE)
        lbl.setFixedWidth(120)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Contenedor para el combo con márgenes horizontales (~7.5% a cada lado → 85%)
        cmb_container = QWidget()
        cmb_container.setStyleSheet("background: transparent;")
        cmb_lay = QHBoxLayout(cmb_container)
        cmb_lay.setContentsMargins(0, 0, 0, 0)
        cmb_lay.setSpacing(0)
        cmb_lay.addStretch(3)

        cmb = NoScrollComboBox()
        cmb.setStyleSheet(COMBO_STYLE)
        cmb.setFixedHeight(32)
        cmb.setCursor(Qt.CursorShape.PointingHandCursor)
        cmb_lay.addWidget(cmb, 40)

        cmb_lay.addStretch(3)

        lay.addWidget(lbl)
        lay.addWidget(cmb_container, 1)

        entry = {"widget": row, "combo": cmb, "label": lbl}
        return row, entry

    def _append_row_widget(self, number: int):
        """Agrega una fila al final del layout (usado durante la construcción inicial)."""
        row, entry = self._create_row_widget(number)
        self._table_layout.addWidget(row)
        self._row_widgets.append(entry)

    # ── API pública para el controller ─────────────────────────────
    def count_valid_references(self) -> int:
        """Cuenta cuántos sensores tienen una referencia válida (distinta a N/A o vacío)."""
        count = 0
        for entry in self._row_widgets:
            text = entry["combo"].currentText().strip()
            if text and text != "N/A":
                count += 1
        return count

    def get_row_data(self) -> list[tuple[str, str]]:
        """Devuelve [(SG_N, referencia), …] para todas las filas."""
        data = []
        for entry in self._row_widgets:
            sensor = entry["label"].text()
            ref = entry["combo"].currentText()
            data.append((sensor, ref))
        return data

    def set_row_data(self, rows: list[tuple[str, str]]):
        """Carga datos en la tabla (hasta el límite de filas existentes)."""
        for i, (sensor, ref) in enumerate(rows):
            if i >= len(self._row_widgets):
                break
            entry = self._row_widgets[i]
            entry["label"].setText(sensor)
            idx = entry["combo"].findText(ref)
            if idx >= 0:
                entry["combo"].setCurrentIndex(idx)

    def populate_sensor_combos(self, references: list[str]):
        """Llena todos los combos de referencia con la lista de sensores."""
        for entry in self._row_widgets:
            cmb: QComboBox = entry["combo"]
            current = cmb.currentText()
            cmb.blockSignals(True)
            cmb.clear()
            cmb.addItem("N/A")  # opción por defecto
            cmb.addItems(references)
            # Restaurar selección previa si existe
            idx = cmb.findText(current)
            if idx >= 0:
                cmb.setCurrentIndex(idx)
            cmb.blockSignals(False)

    def set_combos_enabled(self, enabled: bool):
        """Activa o desactiva todos los dropdowns de la tabla."""
        for entry in self._row_widgets:
            entry["combo"].setEnabled(enabled)

    def clear_combos(self):
        """Resetea todos los dropdowns de la tabla a la opción vacía."""
        for entry in self._row_widgets:
            entry["combo"].setCurrentIndex(0)

    # ── Lista de sensores de gas ───────────────────────────────
    def _setup_sensor_list(self):
        """Configura el scroll area para la lista de sensores."""
        if not self.ui:
            return
        scroll: QScrollArea = self.ui.findChild(QScrollArea, "scrollSensorList")
        if scroll is None:
            return

        container = QWidget()
        self._sensor_list_layout = QVBoxLayout(container)
        self._sensor_list_layout.setContentsMargins(4, 4, 4, 4)
        self._sensor_list_layout.setSpacing(2)
        self._sensor_list_layout.addStretch(1)

        scroll.setWidget(container)
        scroll.setWidgetResizable(True)

    def populate_sensor_list(self, sensors: list[str]):
        """Llena la lista de sensores con los nombres dados."""
        # Limpiar lista actual
        for entry in self._sensor_list_entries:
            self._sensor_list_layout.removeWidget(entry["widget"])
            entry["widget"].deleteLater()
        self._sensor_list_entries.clear()

        for name in sensors:
            self._add_sensor_list_row(name)

    def _add_sensor_list_row(self, name: str):
        """Agrega una fila a la lista de sensores."""
        row = QWidget()
        row.setFixedHeight(36)
        bg = "#FFFFFF" if len(self._sensor_list_entries) % 2 == 0 else "#F5F5F5"
        row.setStyleSheet(f"background-color: {bg}; border-radius: 4px;")

        lay = QHBoxLayout(row)
        lay.setContentsMargins(8, 0, 4, 0)
        lay.setSpacing(4)

        lbl = QLabel(name)
        lbl.setStyleSheet("font-size: 12px; color: #333333; font-weight: bold;")
        lay.addWidget(lbl, 1)

        btn_del = QPushButton("🗑")
        btn_del.setFixedSize(30, 30)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                font-size: 14px;
                color: #999999;
            }
            QPushButton:hover { color: #E53935; }
        """)
        btn_del.setToolTip(f"Eliminar {name}")
        lay.addWidget(btn_del)

        insert_pos = self._sensor_list_layout.count() - 1
        self._sensor_list_layout.insertWidget(insert_pos, row)

        entry = {"name": name, "widget": row, "btn_del": btn_del}
        self._sensor_list_entries.append(entry)

        btn_del.clicked.connect(lambda checked, e=entry: self._on_delete_sensor(e))

    def _on_delete_sensor(self, entry: dict):
        """Elimina un sensor de la lista y emite la señal."""
        if entry in self._sensor_list_entries:
            self._sensor_list_entries.remove(entry)
            self._sensor_list_layout.removeWidget(entry["widget"])
            entry["widget"].deleteLater()
            self.sensor_deleted.emit(entry["name"])

