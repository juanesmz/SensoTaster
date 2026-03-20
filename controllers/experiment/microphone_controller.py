"""
MicrophoneController
--------------------
Controlador para la vista de micrófonos.

Responsabilidades:
  1. Enumerar SOLO micrófonos (dispositivos de entrada reales) con sounddevice.
  2. Poblar el QComboBox (cmbMicrophone) con esos dispositivos.
  3. Botón 🔄 (btnRefreshDevices) re-escanea los dispositivos del sistema.
  4. Gestionar la lista de micrófonos agregados (QTableWidget tableMicList).
     - btnAddMicrophone  → agrega el dispositivo seleccionado en cmbMicrophone.
     - Botón papelera    → elimina la fila correspondiente.
  5. btnViewMicrophone (checkable) → inicia/detiene la captura de audio
     del micrófono seleccionado en la tabla y actualiza el gráfico de onda.

Dependencias: sounddevice, numpy
"""

import numpy as np
import sounddevice as sd

from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt
from PySide6.QtWidgets import (
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy
)


# ── Parámetros de captura ─────────────────────────────────────────────────────
SAMPLE_RATE    = 44100   # Hz
BLOCK_SIZE     = 2048    # muestras por bloque → ~46 ms
CHANNELS       = 1       # mono
# ─────────────────────────────────────────────────────────────────────────────


class _AudioWorker(QThread):
    """
    Hilo de captura de audio con sounddevice usando lectura bloqueante.
    La señal chunk_ready se emite desde el propio QThread (no desde el
    callback de PortAudio), garantizando el correcto despacho por Qt.
    """

    chunk_ready = Signal(object)   # emite np.ndarray float32

    def __init__(self, device_index: int, parent=None):
        super().__init__(parent)
        self.device_index = device_index
        self._running = False

    def run(self):
        self._running = True
        try:
            stream = sd.InputStream(
                device=self.device_index,
                channels=CHANNELS,
                samplerate=SAMPLE_RATE,
                blocksize=BLOCK_SIZE,
                dtype="float32",
            )
            stream.start()
            while self._running:
                data, overflowed = stream.read(BLOCK_SIZE)
                if self._running and not overflowed:
                    # data shape: (BLOCK_SIZE, 1) → aplanar a (BLOCK_SIZE,)
                    self.chunk_ready.emit(data[:, 0].copy())
            stream.stop()
            stream.close()
        except Exception as e:
            print(f"[AudioWorker] Error: {e}")

    def stop(self):
        self._running = False
        self.wait(3000)


class MicrophoneController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view

        # Lista interna: [{name, device_index}, ...]
        self._mic_list: list[dict] = []
        self._worker: _AudioWorker | None = None

        # Índice del dispositivo que se está monitoreando (-1 = ninguno)
        self._monitoring_device: int = -1

        self._populate_devices()
        self._setup_table()
        self._connect_buttons()

    # ------------------------------------------------------------------ #
    #  Dispositivos disponibles                                            #
    # ------------------------------------------------------------------ #

    def _populate_devices(self):
        """
        Llena el cmbMicrophone SOLO con micrófonos reales del sistema.
        Filtra dispositivos virtuales (Stereo Mix, loopback, etc.) y
        usa únicamente la hostapi por defecto para evitar duplicados.
        """
        cmb = self._find(QComboBox, "cmbMicrophone")
        if cmb is None:
            return

        # Forzar re-escaneo del hardware (PortAudio cachea la lista)
        try:
            sd._terminate()
            sd._initialize()
        except Exception:
            pass

        cmb.clear()
        self._input_devices: list[dict] = []


        # Obtener la hostapi por defecto del sistema
        try:
            default_hostapi = sd.query_hostapis(sd.default.hostapi)
            default_hostapi_idx = sd.default.hostapi
        except Exception:
            default_hostapi_idx = 0

        # Palabras clave de dispositivos virtuales que NO son micrófonos
        virtual_keywords = [
            "stereo mix", "loopback", "what u hear", "wave out",
            "virtual", "voicemeter", "cable output", "asignador"
        ]

        for idx, dev in enumerate(sd.query_devices()):
            # Solo dispositivos de entrada
            if dev["max_input_channels"] <= 0:
                continue

            # Solo de la hostapi por defecto (evita duplicados MME/WASAPI/DS)
            if dev.get("hostapi", -1) != default_hostapi_idx:
                continue

            # Filtrar dispositivos virtuales/loopback
            name_lower = dev["name"].lower()
            if any(kw in name_lower for kw in virtual_keywords):
                continue

            label = dev["name"]
            cmb.addItem(label)
            self._input_devices.append({"name": label, "index": idx})

    # ------------------------------------------------------------------ #
    #  Tabla de micrófonos                                                 #
    # ------------------------------------------------------------------ #

    def _setup_table(self):
        table: QTableWidget = self._find(QTableWidget, "tableMicList")
        if table is None:
            return

        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Nombre de dispositivo", "Eliminar"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        table.setColumnWidth(1, 80)
        table.verticalHeader().setVisible(False)
        table.setRowCount(0)

    def _add_row(self, name: str, device_index: int):
        """Añade una fila a la tabla con el nombre del micrófono y botón de borrado."""
        table: QTableWidget = self._find(QTableWidget, "tableMicList")
        if table is None:
            return

        row = table.rowCount()
        table.insertRow(row)

        # Columna 0: nombre
        name_item = QTableWidgetItem(name)
        name_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        table.setItem(row, 0, name_item)

        # Columna 1: botón de eliminar (🗑)
        btn_delete = QPushButton("🗑")
        btn_delete.setToolTip("Eliminar micrófono")
        btn_delete.setCursor(Qt.PointingHandCursor)
        btn_delete.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                border: none;
                background: transparent;
                color: #757575;
            }
            QPushButton:hover { color: #E53935; }
            QPushButton:pressed { color: #B71C1C; }
        """)
        btn_delete.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        btn_delete.clicked.connect(lambda checked, r=row: self._delete_row(r))
        table.setCellWidget(row, 1, btn_delete)

        # Guardar en la lista interna
        self._mic_list.append({"name": name, "device_index": device_index})

    def _delete_row(self, row: int):
        """Elimina la fila indicada y ajusta los índices de los botones restantes."""
        table: QTableWidget = self._find(QTableWidget, "tableMicList")
        if table is None or row >= table.rowCount():
            return

        # Si se estaba monitoreando ese micrófono, detener
        if row < len(self._mic_list):
            if self._mic_list[row]["device_index"] == self._monitoring_device:
                self._stop_monitoring()
                # Resetear el botón
                btn_view = self._find(QPushButton, "btnViewMicrophone")
                if btn_view:
                    btn_view.setChecked(False)

        table.removeRow(row)
        if row < len(self._mic_list):
            self._mic_list.pop(row)

        # Reconectar botones de papelera con índices actualizados
        self._reconnect_delete_buttons()

    def _reconnect_delete_buttons(self):
        """Recalcula los índices de fila para todos los botones de eliminar."""
        table: QTableWidget = self._find(QTableWidget, "tableMicList")
        if table is None:
            return
        for r in range(table.rowCount()):
            btn = table.cellWidget(r, 1)
            if btn:
                try:
                    btn.clicked.disconnect()
                except RuntimeError:
                    pass
                btn.clicked.connect(lambda checked, row=r: self._delete_row(row))

    # ------------------------------------------------------------------ #
    #  Conexión de botones                                                 #
    # ------------------------------------------------------------------ #

    def _connect_buttons(self):
        btn_add     = self._find(QPushButton, "btnAddMicrophone")
        btn_view    = self._find(QPushButton, "btnViewMicrophone")
        btn_refresh = self._find(QPushButton, "btnRefreshDevices")

        if btn_add:
            btn_add.clicked.connect(self._on_add_microphone)
        if btn_view:
            btn_view.toggled.connect(self._on_view_toggled)
        if btn_refresh:
            btn_refresh.clicked.connect(self._on_refresh_devices)

    @Slot()
    def _on_refresh_devices(self):
        """Re-escanea los dispositivos de audio y actualiza el dropdown."""
        self._populate_devices()

    @Slot()
    def _on_add_microphone(self):
        """Agrega el dispositivo seleccionado en el dropdown a la tabla."""
        cmb = self._find(QComboBox, "cmbMicrophone")
        if cmb is None or not self._input_devices:
            return

        idx_combo = cmb.currentIndex()
        if idx_combo < 0 or idx_combo >= len(self._input_devices):
            return

        dev = self._input_devices[idx_combo]

        # Evitar duplicados
        for mic in self._mic_list:
            if mic["device_index"] == dev["index"]:
                return

        self._add_row(dev["name"], dev["index"])

    @Slot(bool)
    def _on_view_toggled(self, checked: bool):
        """Inicia o detiene la captura del micrófono seleccionado en el dropdown."""
        btn_view = self._find(QPushButton, "btnViewMicrophone")
        cmb = self._find(QComboBox, "cmbMicrophone")
        if checked:
            # Tomar el dispositivo directamente del dropdown (cmbMicrophone)
            device_index = -1
            if cmb and self._input_devices:
                idx_combo = cmb.currentIndex()
                if 0 <= idx_combo < len(self._input_devices):
                    device_index = self._input_devices[idx_combo]["index"]

            if device_index == -1:
                # No hay dispositivo seleccionado → desmarcar el botón
                if btn_view:
                    btn_view.setChecked(False)
                return

            self._start_monitoring(device_index)
            if btn_view:
                btn_view.setText("⏹  Detener")
            if cmb:
                cmb.setEnabled(False)
        else:
            self._stop_monitoring()
            if btn_view:
                btn_view.setText("Ver micrófono")
            if cmb:
                cmb.setEnabled(True)


    # ------------------------------------------------------------------ #
    #  Captura de audio                                                    #
    # ------------------------------------------------------------------ #

    def _start_monitoring(self, device_index: int):
        self._stop_monitoring()
        self._monitoring_device = device_index
        self._worker = _AudioWorker(device_index)
        self._worker.chunk_ready.connect(self._on_audio_chunk, Qt.QueuedConnection)
        self._worker.start()

    def _stop_monitoring(self):
        if self._worker is not None:
            self._worker.stop()
            self._worker = None
        self._monitoring_device = -1
        # Limpiar gráfico
        chart = getattr(self.view, "chart_widget", None)
        if chart:
            chart.clear()

    @Slot(object)
    def _on_audio_chunk(self, samples: np.ndarray):
        """Recibe un chunk de audio del hilo y actualiza el gráfico."""
        chart = getattr(self.view, "chart_widget", None)
        if chart:
            chart.update_waveform(samples)

    # ------------------------------------------------------------------ #
    #  Helper                                                              #
    # ------------------------------------------------------------------ #

    def _find(self, widget_type, name: str):
        if self.view and self.view.ui:
            return self.view.ui.findChild(widget_type, name)
        return None
