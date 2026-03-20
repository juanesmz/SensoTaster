import os
from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QWidget, QSizePolicy, QFrame,
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPixmap, QPainter
from views.base_view import BaseView


class ScaledImageWidget(QWidget):
    """Widget que muestra una imagen llenando todo el espacio disponible
    sin perder la relación de aspecto (recorta el exceso centrado)."""

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

        scale = max(w_w / p_w, w_h / p_h)
        scaled_w = int(p_w * scale)
        scaled_h = int(p_h * scale)

        x = (scaled_w - w_w) / 2
        y = (scaled_h - w_h) / 2

        src_x = x / scale
        src_y = y / scale
        src_w = w_w / scale
        src_h = w_h / scale

        painter.drawPixmap(
            QRect(0, 0, w_w, w_h),
            self._pixmap,
            QRect(int(src_x), int(src_y), int(src_w), int(src_h)),
        )
        painter.end()


class CleaningView(BaseView):
    def __init__(self):
        super().__init__(os.path.join("ui", "experiment", "pages", "cleaning.ui"))
        self._setup_image()

    def _setup_image(self):
        """Reemplaza el QLabel de la imagen con un widget escalado."""
        if not self.ui:
            return

        frame: QFrame = self.ui.findChild(QFrame, "frameImage")
        if frame is None:
            return

        # Cargar la imagen original
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        img_path = os.path.join(base_dir, "resources", "images", "cleanCabin.png")
        pixmap = QPixmap(img_path)

        if pixmap.isNull():
            return

        # Eliminar el QLabel original
        lbl: QLabel = frame.findChild(QLabel, "lblCleanImage")
        layout = frame.layout()
        if lbl and layout:
            layout.removeWidget(lbl)
            lbl.deleteLater()

        # Insertar el widget de imagen escalada
        self._img_widget = ScaledImageWidget(pixmap)
        layout.addWidget(self._img_widget)
