import os
from PySide6.QtWidgets import QLabel, QWidget, QHBoxLayout, QFrame, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from views.base_view import BaseView


class LoginView(BaseView):
    def __init__(self):
        super().__init__(os.path.join("ui", "login", "login.ui"))
        self._setup_logos_row()

    def _setup_logos_row(self):
        """Reemplaza labelCapsab por una fila: CAPSAB | línea blanca | GAGPS,
        y centra los logos EUSab y el nuevo contenedor horizontalmente."""
        if not self.ui:
            return

        # ── Centrar EUSab ──────────────────────────────────────────
        lbl_eusab = self.ui.findChild(QLabel, "labelEUSab")
        if lbl_eusab:
            parent_layout = lbl_eusab.parentWidget().layout()
            if parent_layout:
                parent_layout.setAlignment(lbl_eusab, Qt.AlignmentFlag.AlignHCenter)

        # ── Reemplazar labelCapsab con la fila de logos ────────────
        lbl_capsab: QLabel = self.ui.findChild(QLabel, "labelCapsab")
        if lbl_capsab is None:
            return

        parent = lbl_capsab.parentWidget()
        parent_layout = parent.layout()
        if parent_layout is None:
            return

        # Encontrar la posición actual del labelCapsab en el layout
        idx = parent_layout.indexOf(lbl_capsab)
        if idx < 0:
            return

        # Crear contenedor horizontal
        logos_container = QWidget()
        logos_container.setStyleSheet("background: transparent;")
        h_lay = QHBoxLayout(logos_container)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(15)

        # Logo CAPSAB (reutilizar la imagen)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        lbl_capsab_new = QLabel()
        lbl_capsab_new.setStyleSheet("background: transparent;")
        pix_capsab = QPixmap(os.path.join(base_dir, "resources", "images", "logo_capsab2.png"))
        if not pix_capsab.isNull():
            pix_capsab = pix_capsab.scaledToHeight(180, Qt.TransformationMode.SmoothTransformation)
        lbl_capsab_new.setPixmap(pix_capsab)
        lbl_capsab_new.setFixedSize(pix_capsab.width(), pix_capsab.height())
        lbl_capsab_new.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Línea divisoria blanca vertical
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setStyleSheet("background: white; color: white; border: none; min-width: 2px; max-width: 2px;")
        divider.setFixedWidth(2)
        divider.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        # Logo GAGPS
        lbl_gagps = QLabel()
        lbl_gagps.setStyleSheet("background: transparent;")
        pix_gagps = QPixmap(os.path.join(base_dir, "resources", "images", "GAGPS_logo.png"))
        lbl_gagps.setPixmap(pix_gagps)
        lbl_gagps.setScaledContents(True)
        lbl_gagps.setMaximumSize(160, 180)
        lbl_gagps.setAlignment(Qt.AlignmentFlag.AlignCenter)

        h_lay.addStretch(1)
        h_lay.addWidget(lbl_capsab_new)
        h_lay.addWidget(divider)
        h_lay.addWidget(lbl_gagps)
        h_lay.addStretch(1)

        # Reemplazar: quitar labelCapsab original, insertar contenedor en su lugar
        parent_layout.removeWidget(lbl_capsab)
        lbl_capsab.deleteLater()
        parent_layout.insertWidget(idx, logos_container)

        # Centrar el contenedor horizontalmente
        parent_layout.setAlignment(logos_container, Qt.AlignmentFlag.AlignHCenter)
