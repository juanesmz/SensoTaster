import os
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QWidget, QFrame,
    QScrollArea, QPushButton, QSizePolicy, QCheckBox,
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPixmap, QPainter
from views.base_view import BaseView
from ui.experiment.pages.emg_chart_widget import EMGChartWidget


class FitImageWidget(QWidget):
    """Muestra una imagen dentro del espacio disponible
    conservando su relación de aspecto (sin recortar, con letterbox)."""

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self._pixmap = pixmap
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, event):
        if self._pixmap.isNull():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w_w, w_h = self.width(), self.height()
        p_w, p_h = self._pixmap.width(), self._pixmap.height()

        scale = min(w_w / p_w, w_h / p_h)
        draw_w = int(p_w * scale)
        draw_h = int(p_h * scale)
        x = (w_w - draw_w) // 2
        y = (w_h - draw_h) // 2

        painter.drawPixmap(
            QRect(x, y, draw_w, draw_h),
            self._pixmap,
            self._pixmap.rect(),
        )
        painter.end()


# ── Estilos ────────────────────────────────────────────────────────
HEADER_STYLE = """
    font-size: 14px;
    font-weight: bold;
    color: white;
    background-color: #4CAF50;
    padding: 8px 12px;
"""

SENSOR_ROW_STYLE = """
    font-size: 14px;
    font-weight: bold;
    color: #333333;
    padding: 8px 12px;
"""

DELETE_BTN_STYLE = """
QPushButton {
    border: none;
    background: transparent;
    font-size: 16px;
    color: #999999;
    padding: 4px;
}
QPushButton:hover {
    color: #E53935;
}
"""


class EMGView(BaseView):
    def __init__(self):
        super().__init__(os.path.join("ui", "experiment", "pages", "emg.ui"))
        self._sensor_rows: list[dict] = []
        self._setup_image()
        self._setup_chart()
        self._setup_sensor_list()

    # ── Tab 1: Imagen de instrucciones ─────────────────────────────
    def _setup_image(self):
        """Reemplaza el QLabel con un FitImageWidget que conserva el aspecto."""
        if not self.ui:
            return

        frame: QFrame = self.ui.findChild(QFrame, "frameImage")
        if frame is None:
            return

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        img_path = os.path.join(base_dir, "resources", "images", "EMG_img.png")
        pixmap = QPixmap(img_path)
        if pixmap.isNull():
            return

        lbl: QLabel = frame.findChild(QLabel, "lblEmgImage")
        layout = frame.layout()
        if lbl and layout:
            layout.removeWidget(lbl)
            lbl.deleteLater()

        self._img_widget = FitImageWidget(pixmap)
        layout.addWidget(self._img_widget)

    # ── Tab 2: Gráfico EMG ─────────────────────────────────────────
    def _setup_chart(self):
        if not self.ui:
            return

        chart_container: QWidget = self.ui.findChild(QWidget, "chartContainer")
        if chart_container is None:
            return

        self.chart_widget = EMGChartWidget()
        layout = QVBoxLayout(chart_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.chart_widget)

    # ── Tab 2: Lista de sensores seleccionados ─────────────────────
    def _setup_sensor_list(self):
        """Construye el contenedor con header + filas dentro del scrollArea."""
        if not self.ui:
            return

        scroll: QScrollArea = self.ui.findChild(QScrollArea, "scrollSensors")
        if scroll is None:
            return

        frame_right: QFrame = self.ui.findChild(QFrame, "frameRight")

        container = QWidget()
        self._sensor_layout = QVBoxLayout(container)
        self._sensor_layout.setContentsMargins(0, 0, 0, 0)
        self._sensor_layout.setSpacing(0)

        # Header fijo
        header = QWidget()
        header.setStyleSheet("background-color: #4CAF50; border-radius: 6px;")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(0)

        lbl_h = QLabel("Sensor")
        lbl_h.setStyleSheet(HEADER_STYLE)
        lbl_h.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        h_lay.addWidget(lbl_h, 1)

        lbl_act = QLabel("")
        lbl_act.setStyleSheet(HEADER_STYLE)
        lbl_act.setFixedWidth(50)
        lbl_act.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_lay.addWidget(lbl_act)

        self._sensor_layout.addWidget(header)
        self._sensor_layout.addStretch(1)

        scroll.setWidget(container)
        scroll.setWidgetResizable(True)

    # ── API pública ────────────────────────────────────────────────
    def add_sensor_row(self, name: str) -> bool:
        """Agrega un sensor a la lista. Retorna False si ya existe."""
        for entry in self._sensor_rows:
            if entry["name"] == name:
                return False

        row = QWidget()
        bg = "#FFFFFF" if len(self._sensor_rows) % 2 == 0 else "#F0F0F0"
        row.setStyleSheet(f"background-color: {bg};")
        row.setFixedHeight(44)

        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lbl = QLabel(name)
        lbl.setStyleSheet(SENSOR_ROW_STYLE)
        lay.addWidget(lbl, 1)

        btn_del = QPushButton("🗑")
        btn_del.setFixedSize(44, 44)
        btn_del.setStyleSheet(DELETE_BTN_STYLE)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setToolTip(f"Quitar {name}")
        lay.addWidget(btn_del)

        insert_pos = self._sensor_layout.count() - 1
        self._sensor_layout.insertWidget(insert_pos, row)

        entry = {"name": name, "widget": row, "btn_del": btn_del}
        self._sensor_rows.append(entry)

        btn_del.clicked.connect(lambda checked, e=entry: self._remove_sensor_row(e))
        return True

    def _remove_sensor_row(self, entry: dict):
        """Elimina una fila de sensor."""
        if entry in self._sensor_rows:
            self._sensor_rows.remove(entry)
            self._sensor_layout.removeWidget(entry["widget"])
            entry["widget"].setParent(None)
            entry["widget"].deleteLater()

    def get_selected_sensors(self) -> list[int]:
        """Retorna los índices (0-based) de los sensores seleccionados via checkboxes."""
        selected = []
        for i in range(1, 7):
            cb = self.ui.findChild(QCheckBox, f"chkSensor{i}")
            if cb and cb.isChecked():
                selected.append(i - 1)
        return selected

    def get_sensor_list(self) -> list[str]:
        """Retorna la lista de nombres de sensores en la tabla derecha."""
        return [e["name"] for e in self._sensor_rows]
