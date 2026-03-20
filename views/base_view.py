from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QDir, Qt
from PySide6.QtGui import QPixmap
import os

# Altura de referencia para los logos del header (misma que logo_capsab)
HEADER_LOGO_HEIGHT = 80

class BaseView(QWidget):
    def __init__(self, ui_file_path):
        super().__init__()
        self.ui = self.load_ui(ui_file_path)
        
        # If the UI file is successfully loaded, we can layout it
        if self.ui:
            # We can use a layout to contain the loaded widget
            from PySide6.QtWidgets import QVBoxLayout
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.ui)
            self.setLayout(layout)

    def load_ui(self, path):
        loader = QUiLoader()
        # Ensure path is absolute or correct relative
        if not os.path.exists(path):
            print(f"Warning: UI file not found at {path}")
            return None
            
        # Set working directory to the directory of the ui file so relative paths (images) resolve correctly
        ui_dir = os.path.dirname(os.path.abspath(path))
        loader.setWorkingDirectory(QDir(ui_dir))
            
        file = QFile(path)
        if not file.open(QFile.ReadOnly):
            print(f"Cannot open {path}: {file.errorString()}")
            return None
        ui = loader.load(file, self)
        file.close()
        return ui

    def _setup_header_logos(self):
        """Inyecta EUSab2 (después del botón de retorno) y GAGPS_logo
        (antes de logo_capsab) en el header de cualquier página."""
        if not self.ui:
            return

        from PySide6.QtWidgets import QPushButton

        header = self.ui.findChild(QWidget, "headerWidget")
        if header is None:
            return

        h_layout: QHBoxLayout = header.findChild(QHBoxLayout, "horizontalLayoutHeader")
        if h_layout is None:
            return

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_dir = os.path.join(base_dir, "resources", "images")

        # ── Helpers ────────────────────────────────────────────────
        def _make_logo(filename: str) -> QLabel | None:
            """Crea un QLabel con la imagen escalada a HEADER_LOGO_HEIGHT
            conservando la relación de aspecto original."""
            path = os.path.join(img_dir, filename)
            pixmap = QPixmap(path)
            if pixmap.isNull():
                print(f"Warning: could not load {path}")
                return None

            scaled = pixmap.scaledToHeight(
                HEADER_LOGO_HEIGHT, Qt.TransformationMode.SmoothTransformation
            )
            lbl = QLabel()
            lbl.setPixmap(scaled)
            lbl.setFixedSize(scaled.width(), scaled.height())
            lbl.setStyleSheet("background: transparent;")
            return lbl

        # ── EUSab2: justo después del botón de retorno ─────────────
        btn_return = self.ui.findChild(QPushButton, "btnReturn")
        if btn_return is not None:
            idx_btn = h_layout.indexOf(btn_return)
            lbl_eusab = _make_logo("EUSab2.png")
            if lbl_eusab is not None:
                h_layout.insertWidget(idx_btn + 1, lbl_eusab)

        # ── GAGPS: justo después de logo_capsab ─────────────────────
        lbl_capsab = self.ui.findChild(QLabel, "lblLogoHeader")
        if lbl_capsab is not None:
            idx_capsab = h_layout.indexOf(lbl_capsab)
            lbl_gagps = _make_logo("GAGPS_logo2.png")
            if lbl_gagps is not None:
                h_layout.insertWidget(idx_capsab + 1, lbl_gagps)

