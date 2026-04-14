import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QGroupBox, QGridLayout, QSizePolicy, QSpacerItem,
    QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

import serial.tools.list_ports
from navigation.router import router
import env_config
from env_config import ENV

ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

LABEL_MIN_W = 160

STYLE_GROUPBOX = """
QGroupBox {
    font-family: 'Segoe UI';
    font-size: 13px;
    font-weight: bold;
    border: 1px solid #CCCCCC;
    border-radius: 6px;
    margin-top: 14px;
    background-color: #FFFFFF;
    color: #1A365D;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
}
"""

STYLE_LABEL = """
QLabel {
    font-family: 'Segoe UI';
    font-size: 13px;
    color: #444444;
}
"""

STYLE_SUBLABEL = """
QLabel {
    font-family: 'Segoe UI';
    font-size: 11px;
    color: #888888;
}
"""

STYLE_INPUT = """
QLineEdit, QComboBox {
    font-family: 'Segoe UI';
    font-size: 13px;
    padding: 7px 10px;
    border: 1px solid #CBD5E0;
    border-radius: 4px;
    background-color: #FFFFFF;
    color: #333333;
}
QLineEdit:disabled {
    background-color: #EDF2F7;
    color: #718096;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #3182CE;
}
"""

STYLE_BTN_REFRESH = """
QPushButton {
    font-family: 'Segoe UI';
    font-size: 13px;
    padding: 7px 16px;
    border: 1px solid #CBD5E0;
    border-radius: 4px;
    background-color: #FFFFFF;
    color: #333333;
}
QPushButton:hover { background-color: #EDF2F7; }
QPushButton:pressed { background-color: #E2E8F0; }
"""

STYLE_BTN_EYE = """
QPushButton {
    font-size: 16px;
    border: 1px solid #CBD5E0;
    border-radius: 4px;
    background-color: #FFFFFF;
    color: #718096;
    padding: 4px 8px;
}
QPushButton:hover { background-color: #EDF2F7; color: #2D3748; }
"""



STYLE_BTN_SAVE = """
QPushButton {
    font-family: 'Segoe UI';
    font-size: 13px;
    font-weight: bold;
    padding: 9px 24px;
    border: none;
    border-radius: 4px;
    background-color: #3182CE;
    color: #FFFFFF;
    min-width: 150px;
}
QPushButton:hover { background-color: #2B6CB0; }
QPushButton:pressed { background-color: #2C5282; }
"""

STYLE_TOAST_SUCCESS = """
QLabel {
    background-color: #276749;
    color: #FFFFFF;
    font-family: 'Segoe UI';
    font-size: 13px;
    border-radius: 6px;
    padding: 10px 20px;
}
"""

STYLE_TOAST_ERROR = """
QLabel {
    background-color: #C53030;
    color: #FFFFFF;
    font-family: 'Segoe UI';
    font-size: 13px;
    border-radius: 6px;
    padding: 10px 20px;
}
"""


def _make_field_label(text: str, sublabel: str = "") -> QWidget:
    """Returns a vertical widget with a bold label and an optional sub-label."""
    container = QWidget()
    vl = QVBoxLayout(container)
    vl.setContentsMargins(0, 0, 0, 0)
    vl.setSpacing(2)

    lbl = QLabel(text)
    lbl.setStyleSheet(STYLE_LABEL)
    vl.addWidget(lbl)

    if sublabel:
        sub = QLabel(sublabel)
        sub.setStyleSheet(STYLE_SUBLABEL)
        vl.addWidget(sub)

    container.setMinimumWidth(LABEL_MIN_W)
    return container


class SettingsController:
    def __init__(self, view):
        self.view = view
        self._pw_visible = False
        self._toast: QLabel | None = None
        self._timer: QTimer | None = None

        # We build the form programmatically so it matches the reference
        self._build_ui()

        router.navigate.connect(self._on_navigate)

    def _on_navigate(self, route_name):
        if route_name == "settings":
            self._refresh_ports()
            self._load_env()

    # ─── Build UI ────────────────────────────────────────────────────────────

    def _build_ui(self):
        """Build the settings form directly in code for pixel-perfect control."""
        body = self.view.findChild(QWidget, "bodyWidget")
        if body is None:
            return

        # Clear existing layout and all nested layouts/widgets from the .ui file
        def clear_layout(layout):
            if layout is None:
                return
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    clear_layout(item.layout())
        
        old_layout = body.layout()
        if old_layout:
            clear_layout(old_layout)
            QWidget().setLayout(old_layout)

        main_vl = QVBoxLayout(body)
        main_vl.setContentsMargins(80, 30, 80, 30)
        main_vl.setSpacing(24)

        # ── Page title ──────────────────────────────────────────────────────
        title = QLabel("Configuración - Dispositivos & Sesión")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("QLabel { color: #1A202C; }")
        main_vl.addWidget(title)

        # ── Hardware section ────────────────────────────────────────────────
        hw_group = QGroupBox("Dispositivos & Hardware")
        hw_group.setStyleSheet(STYLE_GROUPBOX)
        hw_grid = QGridLayout(hw_group)
        hw_grid.setContentsMargins(20, 24, 20, 20)
        hw_grid.setHorizontalSpacing(20)
        hw_grid.setVerticalSpacing(18)
        hw_grid.setColumnStretch(1, 1)

        # Row 0: LabJack
        hw_grid.addWidget(
            _make_field_label("Serial LabJack:", "Ej. LJ-123456"),
            0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
        )
        self.txt_labjack = QLineEdit()
        self.txt_labjack.setPlaceholderText("LJ-123456")
        self.txt_labjack.setStyleSheet(STYLE_INPUT)
        self.txt_labjack.setMinimumHeight(38)
        hw_grid.addWidget(self.txt_labjack, 0, 1)

        # Row 1: Arduino COM port + refresh
        hw_grid.addWidget(
            _make_field_label("Puerto Arduino:", "Seleccione el puerto COM"),
            1, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
        )
        arduino_hl = QHBoxLayout()
        arduino_hl.setSpacing(10)
        self.cmb_arduino = QComboBox()
        self.cmb_arduino.setStyleSheet(STYLE_INPUT)
        self.cmb_arduino.setMinimumHeight(38)
        self.cmb_arduino.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        arduino_hl.addWidget(self.cmb_arduino)
        self.btn_refresh = QPushButton("Actualizar puertos")
        self.btn_refresh.setStyleSheet(STYLE_BTN_REFRESH)
        self.btn_refresh.setMinimumHeight(38)
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self._refresh_ports)
        arduino_hl.addWidget(self.btn_refresh)
        hw_grid.addLayout(arduino_hl, 1, 1)

        main_vl.addWidget(hw_group)

        # ── Session section ─────────────────────────────────────────────────
        sess_group = QGroupBox("Sesión & Cuenta")
        sess_group.setStyleSheet(STYLE_GROUPBOX)
        sess_grid = QGridLayout(sess_group)
        sess_grid.setContentsMargins(20, 24, 20, 20)
        sess_grid.setHorizontalSpacing(20)
        sess_grid.setVerticalSpacing(18)
        sess_grid.setColumnStretch(1, 1)

        # Row 0: Username (read-only)
        sess_grid.addWidget(
            _make_field_label("Usuario de Sesión:", "No editable (sesión activa)"),
            0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
        )
        self.txt_user = QLineEdit()
        self.txt_user.setEnabled(False)
        self.txt_user.setStyleSheet(STYLE_INPUT)
        self.txt_user.setMinimumHeight(38)
        sess_grid.addWidget(self.txt_user, 0, 1)

        # Row 1: Password
        sess_grid.addWidget(
            _make_field_label("Clave de Sesión:", "Contraseña enmascarada, toggle visibilidad."),
            1, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
        )
        pw_hl = QHBoxLayout()
        pw_hl.setSpacing(8)
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setPlaceholderText("••••••••")
        self.txt_password.setStyleSheet(STYLE_INPUT)
        self.txt_password.setMinimumHeight(38)
        pw_hl.addWidget(self.txt_password)
        self.btn_eye = QPushButton("👁")
        self.btn_eye.setStyleSheet(STYLE_BTN_EYE)
        self.btn_eye.setFixedSize(38, 38)
        self.btn_eye.setToolTip("Mostrar / ocultar contraseña")
        self.btn_eye.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_eye.clicked.connect(self._toggle_password)
        pw_hl.addWidget(self.btn_eye)
        sess_grid.addLayout(pw_hl, 1, 1)

        main_vl.addWidget(sess_group)

        # ── Spacer ──────────────────────────────────────────────────────────
        main_vl.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # ── Toast ───────────────────────────────────────────────────────────
        self._toast = QLabel("", body)
        self._toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._toast.hide()

        # ── Bottom buttons ───────────────────────────────────────────────────
        btn_hl = QHBoxLayout()
        btn_hl.setSpacing(12)
        btn_hl.addStretch()
        self.btn_save = QPushButton("Guardar Cambios")
        self.btn_save.setStyleSheet(STYLE_BTN_SAVE)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self._save_env)
        btn_hl.addWidget(self.btn_save)
        btn_hl.addStretch()
        main_vl.addLayout(btn_hl)

        # ── Bottom Spacer ────────────────────────────────────────────────────
        main_vl.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Also wire the header return button
        if self.view.ui:
            btn_return = self.view.ui.findChild(QPushButton, "btnReturn")
            if btn_return:
                btn_return.clicked.connect(lambda: router.go_to("main_menu"))

        # Load initial data
        self._refresh_ports()
        self._load_env()

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _toggle_password(self):
        if self._pw_visible:
            self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_eye.setText("👁")
            self._pw_visible = False
        else:
            self.txt_password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_eye.setText("🔒")
            self._pw_visible = True

    def _refresh_ports(self):
        current = self.cmb_arduino.currentData()
        self.cmb_arduino.clear()
        ports = serial.tools.list_ports.comports()
        for p in ports:
            label = f"{p.device}  ({p.description})" if p.description != p.device else p.device
            self.cmb_arduino.addItem(label, userData=p.device)
        if self.cmb_arduino.count() == 0:
            self.cmb_arduino.addItem("Sin puertos disponibles", userData="")
        # Restore previous selection
        if current:
            for i in range(self.cmb_arduino.count()):
                if self.cmb_arduino.itemData(i) == current:
                    self.cmb_arduino.setCurrentIndex(i)
                    break

    def _parse_env_file(self):
        env_vars = {}
        if os.path.exists(ENV_FILE):
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip()
        return env_vars

    def _load_env(self):
        env_vars = self._parse_env_file()
        self.txt_labjack.setText(env_vars.get("LABJACK_SERIAL", ""))
        self.txt_user.setText(env_vars.get("SESSION_USER", "admin"))
        self.txt_password.setText(env_vars.get("SESSION_PASSWORD", ""))
        target_port = env_vars.get("ARDUINO_COM_PORT", "")
        for i in range(self.cmb_arduino.count()):
            if self.cmb_arduino.itemData(i) == target_port:
                self.cmb_arduino.setCurrentIndex(i)
                break

    def _save_env(self):
        labjack = self.txt_labjack.text().strip()
        arduino_port = self.cmb_arduino.currentData() or ""
        password = self.txt_password.text().strip()
        user = self.txt_user.text().strip()

        if not labjack or not password:
            self._show_toast("Complete todos los campos requeridos.", error=True)
            return

        env_vars = self._parse_env_file()
        env_vars["LABJACK_SERIAL"] = labjack
        env_vars["ARDUINO_COM_PORT"] = arduino_port
        env_vars["SESSION_USER"] = user
        env_vars["SESSION_PASSWORD"] = password

        try:
            with open(ENV_FILE, "w", encoding="utf-8") as f:
                for k, v in env_vars.items():
                    f.write(f"{k}={v}\n")
            # Reload in-memory config so all controllers pick up new values
            env_config.reload()
            self._show_toast("✓  Configuración guardada correctamente.")
            QTimer.singleShot(1800, lambda: router.go_to("main_menu"))
        except Exception as e:
            self._show_toast(f"Error al guardar: {e}", error=True)

    def _show_toast(self, message: str, error: bool = False):
        """Shows a non-intrusive toast notification at the bottom of the body."""
        if self._toast is None:
            return
        self._toast.setText(message)
        self._toast.setStyleSheet(STYLE_TOAST_ERROR if error else STYLE_TOAST_SUCCESS)
        
        body = self.view.findChild(QWidget, "bodyWidget")
        if body:
            margin = 24
            w = min(body.width() - margin * 2, 500)
            h = 42
            x = (body.width() - w) // 2
            y = body.height() - h - margin
            self._toast.setGeometry(x, y, w, h)
        
        self._toast.raise_()
        self._toast.show()

        if self._timer:
            self._timer.stop()
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._toast.hide)
        self._timer.start(3000)

    # keep go_back for backwards compat
    def go_back(self):
        router.go_to("main_menu")
