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

LABJACK_SERIAL = 470026166


class CleaningController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view
        self._handle = None  # handle de conexión LabJack
        self._remaining_seconds = 0

        # ── Referencias a widgets ──────────────────────────────────
        ui = self.view.ui
        self._input_time: QLineEdit = ui.findChild(QLineEdit, "inputTime")
        self._btn_start: QPushButton = ui.findChild(QPushButton, "btnStartCleaning")

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
            self._btn_start.clicked.connect(self._on_start)

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
        self._btn_start.setEnabled(False)
        self._btn_start.setText("Limpiando...")

        # Actualizar display y arrancar timer
        self._input_time.setText(self._format_time(self._remaining_seconds))
        self._timer.start()

    # ── Tick del timer ─────────────────────────────────────────────
    def _on_tick(self):
        """Se ejecuta cada segundo durante la cuenta regresiva."""
        self._remaining_seconds -= 1
        self._input_time.setText(self._format_time(self._remaining_seconds))

        if self._remaining_seconds <= 0:
            self._timer.stop()
            self._on_cleaning_done()

    # ── Limpieza terminada ─────────────────────────────────────────
    def _on_cleaning_done(self):
        """Pone FIO0/FIO1 en bajo, cierra conexión, restaura UI."""
        self._set_fio_low()
        self._disconnect_labjack()

        # Restaurar UI
        self._input_time.setReadOnly(False)
        self._btn_start.setEnabled(True)
        self._btn_start.setText("Iniciar limpieza")

        QMessageBox.information(
            self.view, "Limpieza completada",
            "El ciclo de limpieza ha terminado.\n"
            "FIO0 y FIO1 están ahora en BAJO.",
        )

    # ── LabJack T7 ─────────────────────────────────────────────────
    def _connect_labjack(self) -> bool:
        """Abre conexión USB con el LabJack T7 por número de serie."""
        try:
            import labjack.ljm as ljm
            self._handle = ljm.openS("T7", "USB", str(LABJACK_SERIAL))
            info = ljm.getHandleInfo(self._handle)
            print(f"LabJack T7 conectado – Serial: {info[2]}")
            return True
        except Exception as e:
            QMessageBox.critical(
                self.view, "Error de conexión",
                f"No se pudo conectar al LabJack T7 (serial {LABJACK_SERIAL}).\n\n"
                f"Error: {e}",
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
