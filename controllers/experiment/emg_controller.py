"""
EmgController
-------------
Controlador para la vista de sensores EMG.

Comportamiento:
  - Lee datos del puerto serial COM6 a 115200 baudios.
  - 6 sensores controlados por checkboxes (chkSensor1..chkSensor6).
  - El botón "Probar sensores seleccionados" arranca/detiene la lectura serial.
  - Los checkboxes controlan qué canales se muestran en el gráfico.
  - El botón "Agregar sensores seleccionados" agrega los sensores checked
    a la tabla de sensores de la derecha.
"""

import numpy as np
import serial
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QPushButton, QCheckBox, QMessageBox


# ── Parámetros de configuración ────────────────────────────────────────────────
SERIAL_PORT = "COM6"
BAUD_RATE   = 115200
NUM_CHANNELS = 6
WINDOW_SIZE  = 200      # Muestras visibles

# Textos del botón
BTN_START = "Probar sensores seleccionados"
BTN_STOP  = "⏹  Detener"
# ─────────────────────────────────────────────────────────────────────────────


class SerialWorker(QThread):
    """Hilo dedicado a leer del puerto serial."""
    data_received = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, port, baudrate, parent=None):
        super().__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self._running = False

    def run(self):
        self._running = True
        try:
            with serial.Serial(self.port, self.baudrate, timeout=1) as ser:
                print(f"[EmgController] Conectado a {self.port}")
                ser.reset_input_buffer()

                while self._running:
                    if ser.in_waiting > 0:
                        try:
                            line = ser.readline().decode('utf-8', errors='ignore').strip()
                            if not line:
                                continue

                            parts = line.split(', ')
                            values = []
                            for p in parts:
                                try:
                                    values.append(float(p))
                                except ValueError:
                                    pass

                            if len(values) >= NUM_CHANNELS:
                                self.data_received.emit(values[:NUM_CHANNELS])
                        except Exception as e:
                            print(f"[EmgController] Error parseando línea: {e}")
                    else:
                        self.msleep(5)

        except serial.SerialException as e:
            self.error_occurred.emit(str(e))
            print(f"[EmgController] Error Serial: {e}")
        finally:
            print("[EmgController] Conexión serial cerrada.")

    def stop(self):
        self._running = False
        self.wait(2000)


class EmgController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view

        # Buffers circulares (6 canales)
        self._buffers: list[np.ndarray] = [
            np.zeros(WINDOW_SIZE) for _ in range(NUM_CHANNELS)
        ]

        # Worker del puerto serial
        self._worker = None

        # Referencias a checkboxes
        self._checkboxes: list[QCheckBox] = []
        for i in range(1, NUM_CHANNELS + 1):
            cb = self._find_widget(QCheckBox, f"chkSensor{i}")
            self._checkboxes.append(cb)

        # Conectar controles de la UI
        self._connect_controls()

    # ── Conexiones ─────────────────────────────────────────────────
    def _connect_controls(self):
        btn_test = self._find_widget(QPushButton, "btnTestSensor")
        if btn_test:
            btn_test.clicked.connect(self._toggle)

        btn_add = self._find_widget(QPushButton, "btnAddSensor")
        if btn_add:
            btn_add.clicked.connect(self._on_add_sensors)

        # Conectar cada checkbox para controlar la visibilidad del canal
        for i, cb in enumerate(self._checkboxes):
            if cb:
                cb.toggled.connect(lambda checked, idx=i: self._on_checkbox_toggled(idx, checked))

    # ── Checkboxes → visibilidad del gráfico ──────────────────────
    @Slot(int, bool)
    def _on_checkbox_toggled(self, index: int, checked: bool):
        """Muestra u oculta el canal en el gráfico según el checkbox."""
        chart = getattr(self.view, "chart_widget", None)
        if chart is not None:
            chart.set_channel_visible(index, checked)

    # ── Agregar sensores seleccionados a la tabla ──────────────────
    @Slot()
    def _on_add_sensors(self):
        """Agrega los sensores seleccionados (checked) a la tabla derecha."""
        added_count = 0
        already_count = 0

        for i, cb in enumerate(self._checkboxes):
            if cb and cb.isChecked():
                sensor_name = f"Sensor_{i + 1}"
                result = self.view.add_sensor_row(sensor_name)
                if result:
                    added_count += 1
                else:
                    already_count += 1

        if added_count == 0 and already_count > 0:
            QMessageBox.information(
                self.view, "Sin cambios",
                "Todos los sensores seleccionados ya están en la lista.",
            )
        elif added_count == 0:
            QMessageBox.warning(
                self.view, "Sin selección",
                "No hay sensores seleccionados para agregar.",
            )

    # ── Control de lectura ─────────────────────────────────────────
    def start(self):
        """Inicia el hilo de lectura serial."""
        if self._worker is not None and self._worker.isRunning():
            return

        # Aplicar visibilidad según estado actual de los checkboxes
        chart = getattr(self.view, "chart_widget", None)
        if chart:
            for i, cb in enumerate(self._checkboxes):
                if cb:
                    chart.set_channel_visible(i, cb.isChecked())

        self._worker = SerialWorker(SERIAL_PORT, BAUD_RATE)
        self._worker.data_received.connect(self._on_data_received)
        self._worker.error_occurred.connect(self._on_serial_error)
        self._worker.start()

    def stop(self):
        """Detiene la lectura serial."""
        if self._worker:
            self._worker.stop()
            self._worker = None

    # ── Slots ──────────────────────────────────────────────────────
    @Slot(list)
    def _on_data_received(self, values: list):
        for i in range(NUM_CHANNELS):
            self._buffers[i] = np.roll(self._buffers[i], -1)
            self._buffers[i][-1] = values[i]

        chart = getattr(self.view, "chart_widget", None)
        if chart is not None:
            chart.update_data(self._buffers)

    @Slot(str)
    def _on_serial_error(self, error_msg):
        print(f"[EmgController] Error crítico serial: {error_msg}")
        self._toggle()

    @Slot()
    def _toggle(self):
        btn = self._find_widget(QPushButton, "btnTestSensor")
        is_running = (self._worker is not None and self._worker.isRunning())

        if is_running:
            self.stop()
            if btn:
                btn.setText(BTN_START)
        else:
            self.start()
            if btn:
                btn.setText(BTN_STOP)

    # ── Helpers ────────────────────────────────────────────────────
    def _find_widget(self, widget_type, name: str):
        if self.view and self.view.ui:
            return self.view.ui.findChild(widget_type, name)
        return None
