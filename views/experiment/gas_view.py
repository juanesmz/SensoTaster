import os
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QLabel, QComboBox,
    QFrame, QScrollArea, QSizePolicy, QPushButton,
)
from PySide6.QtCore import Qt, Signal
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


class GasView(BaseView):
    sensor_deleted = Signal(str)  # emite el nombre del sensor eliminado

    def __init__(self):
        super().__init__(os.path.join("ui", "experiment", "pages", "gas.ui"))
        self._row_widgets: list[dict] = []
        self._sensor_list_entries: list[dict] = []
        self._setup_table()
        self._setup_sensor_list()

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
        right_layout.insertWidget(0, header)

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

        cmb = QComboBox()
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
    def add_row(self):
        """Añade una fila nueva al final de la tabla."""
        number = len(self._row_widgets) + 1
        row, entry = self._create_row_widget(number)
        # Insertar antes del stretch (último elemento del layout)
        insert_pos = self._table_layout.count() - 1
        self._table_layout.insertWidget(insert_pos, row)
        self._row_widgets.append(entry)

    def remove_row(self):
        """Elimina la última fila de la tabla (mínimo 1)."""
        if len(self._row_widgets) <= 1:
            return
        entry = self._row_widgets.pop()
        self._table_layout.removeWidget(entry["widget"])
        entry["widget"].setParent(None)
        entry["widget"].deleteLater()

    def get_row_count(self) -> int:
        return len(self._row_widgets)

    def get_row_data(self) -> list[tuple[str, str]]:
        """Devuelve [(SG_N, referencia), …] para todas las filas."""
        data = []
        for entry in self._row_widgets:
            sensor = entry["label"].text()
            ref = entry["combo"].currentText() or "NA"
            data.append((sensor, ref))
        return data

    def set_row_data(self, rows: list[tuple[str, str]]):
        """Carga datos en la tabla, ajustando la cantidad de filas."""
        # Ajustar cantidad
        while len(self._row_widgets) < len(rows):
            self.add_row()
        while len(self._row_widgets) > len(rows) and len(self._row_widgets) > 1:
            self.remove_row()

        for i, (sensor, ref) in enumerate(rows):
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
            cmb.addItem("")  # opción vacía
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

