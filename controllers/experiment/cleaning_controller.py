"""
Controlador para la página Cleaning – limpieza de cabina de gas.

Responsabilidades:
  • Leer el tiempo de duración ingresado (formato MM:SS).
  • Al pulsar "Iniciar limpieza":
      1. Conectar a la tarjeta LabJack T7 (serial 470026166) por USB.
      2. Configurar FIO0 y FIO1 como salida digital en ALTO.
      3. Iniciar una cuenta regresiva visible en el campo de tiempo.
  • Cuando la cuenta llega a 00:00:
      1. Poner FIO0 y FIO1 en BAJO.
      2. Cerrar la conexión con la tarjeta.
      3. Re-habilitar el botón y el campo de texto.
"""

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QLineEdit, QPushButton, QMessageBox
from env_config import ENV


def _labjack_serial() -> int:
    """Reads LABJACK_SERIAL from the .env at call time (respects live changes)."""
    return int(ENV.get("LABJACK_SERIAL", "470026166"))


class CleaningController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view
        self._handle = None  # handle de conexión LabJack
        self._remaining_seconds = 0
        self.cleaning_completed = False

        # ── Referencias a widgets ──────────────────────────────────
        ui = self.view.ui
        self._input_time: QLineEdit = ui.findChild(QLineEdit, "inputTime")
        self._btn_start: QPushButton = ui.findChild(QPushButton, "btnStartCleaning")
        self._original_btn_style = ""
        if self._btn_start:
            self._original_btn_style = self._btn_start.styleSheet()

        # ── Validar formato de entrada ─────────────────────────────
        if self._input_time:
            from PySide6.QtCore import QRegularExpression
            from PySide6.QtGui import QRegularExpressionValidator
            regex = QRegularExpression(r"^\d{1,2}:\d{2}$")
            self._input_time.setValidator(QRegularExpressionValidator(regex))

        # ── Timer para la cuenta regresiva ─────────────────────────
        self._timer = QTimer(self)
        self._timer.setInterval(1000)  # cada segundo
        self._timer.timeout.connect(self._on_tick)

        # ── Conexión del botón ─────────────────────────────────────
        if self._btn_start:
            self._btn_start.clicked.connect(self._on_btn_click)

    # ── Parsear tiempo ─────────────────────────────────────────────
    def _parse_time(self) -> int | None:
        """Convierte MM:SS del campo de texto a segundos totales."""
        if not self._input_time:
            return None
        text = self._input_time.text().strip()
        try:
            parts = text.split(":")
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes * 60 + seconds
            elif len(parts) == 1:
                return int(parts[0]) * 60
        except ValueError:
            pass
        return None

    def _format_time(self, total_seconds: int) -> str:
        """Convierte segundos totales a formato MM:SS."""
        m = total_seconds // 60
        s = total_seconds % 60
        return f"{m:02d}:{s:02d}"

    # ── Iniciar limpieza ───────────────────────────────────────────
    def _on_start(self):
        """Inicia la limpieza: conecta LabJack, sube FIO0/FIO1, inicia cuenta."""
        total = self._parse_time()
        if total is None or total <= 0:
            QMessageBox.warning(
                self.view, "Tiempo inválido",
                "Ingrese un tiempo válido en formato MM:SS (ej. 20:00).",
            )
            return

        # Intentar conectar a la tarjeta LabJack T7
        if not self._connect_labjack():
            return

        # Configurar FIO0 y FIO1 como salida digital en ALTO
        self._set_fio_high()

        # Configurar UI para cuenta regresiva
        self._remaining_seconds = total
        self._input_time.setReadOnly(True)
        self._btn_start.setText("Detener limpieza")
        # Estilo rojo manteniendo el resto de propiedades (fuente, bordes, etc.)
        self._btn_start.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
                padding: 8px 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #c62828;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)

        # Actualizar display y arrancar timer
        self._input_time.setText(self._format_time(self._remaining_seconds))
        self._timer.start()

    def _on_btn_click(self):
        """Maneja el clic del botón: Inicia o Detiene según el estado."""
        if self._timer.isActive():
            self._on_stop()
        else:
            self._on_start()

    def _on_stop(self):
        """Detiene manualmente el proceso de limpieza."""
        self._timer.stop()
        self._on_cleaning_done(stopped_manually=True)

    # ── Tick del timer ─────────────────────────────────────────────
    def _on_tick(self):
        """Se ejecuta cada segundo durante la cuenta regresiva."""
        self._remaining_seconds -= 1
        self._input_time.setText(self._format_time(self._remaining_seconds))

        if self._remaining_seconds <= 0:
            self._timer.stop()
            self._on_cleaning_done()

    # ── Limpieza terminada ─────────────────────────────────────────
    def _on_cleaning_done(self, stopped_manually=False):
        """Pone FIO0/FIO1 en bajo, cierra conexión, restaura UI."""
        self._set_fio_low()
        self._disconnect_labjack()
        self.cleaning_completed = True

        # Restaurar UI
        self._input_time.setReadOnly(False)
        self._btn_start.setEnabled(True)
        self._btn_start.setText("Iniciar limpieza")
        self._btn_start.setStyleSheet(self._original_btn_style) 

        if not stopped_manually:
            QMessageBox.information(
                self.view, "Limpieza completada",
                "El ciclo de limpieza ha terminado.\n"
                "FIO0 y FIO1 están ahora en BAJO.",
            )
        else:
            QMessageBox.warning(
                self.view, "Limpieza interrumpida",
                "El proceso de limpieza fue detenido manualmente.\n"
                "FIO0 y FIO1 han vuelto a BAJO.",
            )

    # ── LabJack T7 ─────────────────────────────────────────────────
    def _connect_labjack(self) -> bool:
        """Abre conexión USB con el LabJack T7 por número de serie."""
        try:
            import labjack.ljm as ljm
            serial_num = _labjack_serial()
            self._handle = ljm.openS("T7", "USB", str(serial_num))
            info = ljm.getHandleInfo(self._handle)
            print(f"LabJack T7 conectado – Serial: {info[2]}")
            return True
        except Exception as e:
            QMessageBox.critical(
                self.view, "Error de conexión",
                "No se pudo establecer conexión con la LabJack.\n\n"
                "Se debe verificar la conexión y el número de serial en la sección de configuración."
            )
            self._handle = None
            return False

    def _disconnect_labjack(self):
        """Cierra la conexión con el LabJack."""
        if self._handle is not None:
            try:
                import labjack.ljm as ljm
                ljm.close(self._handle)
                print("LabJack T7 desconectado.")
            except Exception as e:
                print(f"Error al desconectar LabJack: {e}")
            finally:
                self._handle = None

    def _set_fio_high(self):
        """Configura FIO0 y FIO1 como salida digital en ALTO."""
        if self._handle is None:
            return
        try:
            import labjack.ljm as ljm
            ljm.eWriteName(self._handle, "FIO0", 1)
            ljm.eWriteName(self._handle, "FIO1", 1)
            print("FIO0 y FIO1 → ALTO")
        except Exception as e:
            print(f"Error al escribir FIO: {e}")

    def _set_fio_low(self):
        """Pone FIO0 y FIO1 en BAJO."""
        if self._handle is None:
            return
        try:
            import labjack.ljm as ljm
            ljm.eWriteName(self._handle, "FIO0", 0)
            ljm.eWriteName(self._handle, "FIO1", 0)
            print("FIO0 y FIO1 → BAJO")
        except Exception as e:
            print(f"Error al escribir FIO: {e}")
