"""
Controlador para la página Gas – gestión de PCB y sensores.

Responsabilidades:
  • Poblar el dropdown de PCBs con los archivos CSV de resources/data/pcb/
  • Cargar la configuración de la PCB seleccionada en la tabla.
  • Poblar los combos de referencia con sensors.csv.
  • Agregar nuevos sensores a sensors.csv (sin duplicados).
  • Añadir / quitar filas de la tabla.
  • Guardar la configuración actual como un nuevo archivo CSV.
"""

import csv
import os

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import (
    QComboBox, QInputDialog, QLabel, QMessageBox, QPushButton, QTabWidget
)
from services.gas_service import GasService
import time


NUEVA_PCB_TEXT = "Nueva PCB"


class GasController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view
        self._gas_service = GasService()
        
        # Estado de visualización
        self._is_visualizing = False
        self._vis_timer = QTimer()
        self._vis_timer.setInterval(20)  # 50 Hz (20ms)
        self._vis_timer.timeout.connect(self._on_vis_tick)
        self._start_time = 0
        self._vis_data = {}        # { "SG_1": [val1, val2...], ... }
        self._vis_timestamps = []  # [t1, t2, ...]
        self._max_points = 150     # 3 segundos de datos a 50Hz

        # Rutas de datos
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self._pcb_dir = os.path.join(base, "resources", "data", "pcb")
        self._sensors_path = os.path.join(base, "resources", "data", "sensors.csv")

        # Asegurar que la carpeta pcb exista
        os.makedirs(self._pcb_dir, exist_ok=True)

        # ── Referencias a widgets del .ui ──────────────────────────
        ui = self.view.ui
        self._cmb_pcb: QComboBox = ui.findChild(QComboBox, "cmbPcb")
        self._btn_add_sensor: QPushButton = ui.findChild(QPushButton, "btnAddSensor")
        self._btn_save: QPushButton = ui.findChild(QPushButton, "btnSaveConfig")
        self._btn_edit: QPushButton = ui.findChild(QPushButton, "btnEditPcb")
        self._tab_widget: QTabWidget = ui.findChild(QTabWidget, "tabWidgetGas")
        self._lbl_table_title: QLabel = ui.findChild(QLabel, "lblTableTitle")

        # Estado de edición
        self._editing = False

        # ── Inicialización ─────────────────────────────────────────
        # Estilo negro sobre blanco para el dropdown de PCB
        if self._cmb_pcb:
            self._cmb_pcb.setStyleSheet("""
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
            """)
        self._load_sensors()
        self._load_pcb_list()
        self._update_save_button_state()

        # ── Conexiones ─────────────────────────────────────────────
        if self._cmb_pcb:
            self._cmb_pcb.currentIndexChanged.connect(self._on_pcb_changed)
        if self._btn_add_sensor:
            self._btn_add_sensor.clicked.connect(self._on_add_sensor)
        if self._btn_save:
            self._btn_save.clicked.connect(self._on_save_config)
        if self._btn_edit:
            self._btn_edit.clicked.connect(self._on_edit_toggle)

        # Conexión: eliminación de sensor desde la lista visual
        self.view.sensor_deleted.connect(self._on_sensor_deleted)

        # Conexiones nuevas para visualización
        if self._tab_widget:
            self._tab_widget.currentChanged.connect(self._on_tab_changed)
        
        if hasattr(self.view, "btn_start_stop") and self.view.btn_start_stop:
            self.view.btn_start_stop.clicked.connect(self._on_start_stop_vis)

    # ── Lógica de Visualización ────────────────────────────────────
    def _on_tab_changed(self, index: int):
        """Se activa al cambiar de pestaña."""
        # Si entramos a la pestaña de "Lectura de sensores"
        if index == 1:
            # Obtener configuración actual de la PCB
            config = self.view.get_row_data()
            self.view.update_sensor_visualization_list(config)

    def _on_start_stop_vis(self):
        """Inicia o detiene la comunicación con LabJack y el gráfico."""
        if not self._is_visualizing:
            # INICIAR
            selected_ids = self.view.get_selected_visualized_sensors()
            if not selected_ids:
                QMessageBox.warning(self.view, "Sin selección", "Seleccione al menos un sensor para visualizar.")
                return

            if not self._gas_service.connect():
                QMessageBox.critical(self.view, "Error de hardware", "No se pudo conectar con la LabJack.")
                return

            # Preparar datos
            self._vis_data = {sid: [] for sid in selected_ids}
            self._vis_timestamps = []
            self._start_time = time.time()
            self.view.setup_curves(selected_ids)

            self._is_visualizing = True
            self._vis_timer.start()
            self.view.btn_start_stop.setText("Detener Visualización")
            self.view.btn_start_stop.setStyleSheet("background-color: #F44336; color: white; font-weight: bold; border-radius: 8px;")
        else:
            # DETENER
            self._is_visualizing = False
            self._vis_timer.stop()
            self._gas_service.disconnect()
            self.view.btn_start_stop.setText("Iniciar Visualización")
            self.view.btn_start_stop.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; border-radius: 8px;")

    def _on_vis_tick(self):
        """Hilo de actualización del gráfico."""
        if not self._is_visualizing:
            return

        #IDs seleccionados (e.g., ["SG_1", "SG_3"])
        selected_ids = list(self._vis_data.keys())
        # Mapear SG_N a AIN(N-1)
        channels = []
        for sid in selected_ids:
            try:
                num = int(sid.split("_")[1])
                channels.append(f"AIN{num-1}")
            except:
                continue
        
        if not channels:
            return

        voltages = self._gas_service.read_channels(channels)
        if voltages is None:
            # Posible pérdida de conexión
            self._on_start_stop_vis() # Detener
            QMessageBox.warning(self.view, "Conexión perdida", "Se perdió la comunicación con la LabJack.")
            return

        # Actualizar datos
        curr_t = time.time() - self._start_time
        self._vis_timestamps.append(curr_t)
        
        for i, sid in enumerate(selected_ids):
            self._vis_data[sid].append(voltages[i])

        # Mantener solo 3 segundos de datos en memoria (independientemente de la frecuencia real)
        while self._vis_timestamps and (self._vis_timestamps[-1] - self._vis_timestamps[0] > 3.0):
            self._vis_timestamps.pop(0)
            for sid in self._vis_data:
                if self._vis_data[sid]:
                    self._vis_data[sid].pop(0)

        # Refrescar gráfico
        self.view.update_plot(self._vis_timestamps, self._vis_data)

    # ── Estado de botones ───────────────────────────────────────────
    def _update_button_states(self):
        """Actualiza el estado de btnSaveConfig y btnEditPcb según el dropdown."""
        if not self._cmb_pcb:
            return
        is_new = self._cmb_pcb.currentText() == NUEVA_PCB_TEXT

        # Editar: solo activo con una PCB existente
        if self._btn_edit:
            self._btn_edit.setEnabled(not is_new)
            if is_new:
                self._editing = False
            
            # El texto del botón cambia según si estamos editando o no
            self._btn_edit.setText("Desactivar edición" if self._editing else "Editar PCB")

        # Guardar: activo si es 'Nueva PCB' O si estamos editando una existente
        if self._btn_save:
            self._btn_save.setEnabled(is_new or self._editing)
        
        # Activar el segundo tab ("Lectura de sensores de gas") solo si hay una PCB seleccionada
        if self._tab_widget:
            is_pcb_selected = (not is_new) and (self._cmb_pcb.currentText().strip() != "")
            self._tab_widget.setTabEnabled(1, is_pcb_selected)

        # Actualizar título dinámico de la tabla
        if self._lbl_table_title:
            if is_new:
                self._lbl_table_title.setText("Ingrese referencias de los sensores de gas")
            else:
                pcb_name = self._cmb_pcb.currentText()
                self._lbl_table_title.setText(f"Referencias de sensores de gas para {pcb_name}")

        # Combos de la tabla: activos si es Nueva PCB o si estamos editando
        self.view.set_combos_enabled(is_new or self._editing)

    # Alias para compatibilidad
    _update_save_button_state = _update_button_states

    # ── Sensores ───────────────────────────────────────────────────
    def _read_sensors(self) -> list[str]:
        """Lee la lista de referencias de sensores desde sensors.csv."""
        sensors = []
        if os.path.exists(self._sensors_path):
            with open(self._sensors_path, "r", encoding="utf-8") as f:
                for line in f:
                    name = line.strip()
                    if name:
                        sensors.append(name)
        return sensors

    def _load_sensors(self):
        """Carga la lista de sensores en todos los combos de la tabla y en la lista visual."""
        self._sensors = self._read_sensors()
        self.view.populate_sensor_combos(self._sensors)
        self.view.populate_sensor_list(self._sensors)

    def _on_add_sensor(self):
        """Ventana emergente para agregar una nueva referencia de sensor."""
        name, ok = QInputDialog.getText(
            self.view, "Agregar nuevo sensor",
            "Nombre de la referencia del sensor:",
        )
        if not ok or not name.strip():
            return

        name = name.strip()

        # Verificar duplicado
        if name in self._sensors:
            QMessageBox.warning(
                self.view, "Duplicado",
                f"La referencia '{name}' ya existe en la lista.",
            )
            return

        # Agregar al archivo
        with open(self._sensors_path, "a", encoding="utf-8") as f:
            f.write(f"{name}\n")

        # Refrescar
        self._load_sensors()

        QMessageBox.information(
            self.view, "Sensor agregado",
            f"Se agregó '{name}' a la lista de sensores.",
        )

    # ── Listado de PCBs ────────────────────────────────────────────
    def _load_pcb_list(self):
        """Pobla el dropdown con los archivos CSV de la carpeta pcb/."""
        if not self._cmb_pcb:
            return

        self._cmb_pcb.blockSignals(True)
        self._cmb_pcb.clear()
        self._cmb_pcb.addItem(NUEVA_PCB_TEXT)

        if os.path.isdir(self._pcb_dir):
            for fname in sorted(os.listdir(self._pcb_dir)):
                if fname.lower().endswith(".csv"):
                    self._cmb_pcb.addItem(fname.replace(".csv", ""))

        self._cmb_pcb.blockSignals(False)

    def _on_pcb_changed(self, index: int):
        """Carga la configuración del PCB seleccionado en la tabla."""
        self._editing = False
        self._update_button_states()
        if not self._cmb_pcb:
            return
        name = self._cmb_pcb.currentText()
        if not name or name == NUEVA_PCB_TEXT:
            # Limpiar las selecciones de la tabla al volver a Nueva PCB
            self.view.clear_combos()
            return

        path = os.path.join(self._pcb_dir, f"{name}.csv")
        if not os.path.exists(path):
            return

        rows: list[tuple[str, str]] = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    rows.append((row[0].strip(), row[1].strip()))

        if rows:
            self.view.set_row_data(rows)
            # Refrescar combos con la lista actual de sensores
            self._load_sensors()
            # Volver a aplicar selecciones del CSV
            self.view.set_row_data(rows)



    # ── Guardar configuración ──────────────────────────────────────
    def _on_save_config(self):
        """Guarda la configuración actual. Maneja tanto nuevas PCBs como ediciones."""
        if not self._cmb_pcb: return

        # Validar que haya al menos 5 sensores con referencia (no N/A)
        valid_sensors = self.view.count_valid_references()
        if valid_sensors < 5:
            QMessageBox.warning(
                self.view, "Configuración insuficiente",
                f"No es posible guardar la configuración. Se han asignado {valid_sensors} sensores, "
                "pero se requiere un mínimo de 5 sensores con referencia (distintos a N/A)."
            )
            return

        is_new = self._cmb_pcb.currentText() == NUEVA_PCB_TEXT
        
        if is_new:
            # Flujo de Nueva PCB: pedir nombre
            name, ok = QInputDialog.getText(
                self.view, "Guardar nueva PCB",
                "Nombre de la nueva PCB:",
            )
            if not ok or not name.strip():
                return
            name = name.strip()
            path = os.path.join(self._pcb_dir, f"{name}.csv")
        else:
            # Flujo de Edición: usar nombre actual
            name = self._cmb_pcb.currentText()
            path = os.path.join(self._pcb_dir, f"{name}.csv")

        # Confirmar si ya existe (solo para nuevas)
        if is_new and os.path.exists(path):
            reply = QMessageBox.question(
                self.view, "Archivo existente",
                f"'{name}.csv' ya existe. ¿Desea reemplazarlo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Escribir CSV
        data = self.view.get_row_data()
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                for sensor, ref in data:
                    writer.writerow([sensor, ref])
        except Exception as e:
            QMessageBox.critical(self.view, "Error al guardar", f"No se pudo guardar el archivo: {e}")
            return

        # Si estábamos editando, salir del modo edición
        if self._editing:
            self._editing = False
            self.view.set_combos_enabled(False)

        # Refrescar dropdown
        self._load_pcb_list()
        
        # Volver a seleccionar la guardada
        idx = self._cmb_pcb.findText(name)
        if idx >= 0:
            self._cmb_pcb.setCurrentIndex(idx)
        
        self._update_button_states()

        QMessageBox.information(
            self.view, "Configuración guardada",
            f"La configuración '{name}' se guardó correctamente.",
        )

    # ── Editar PCB existente ──────────────────────────────────────
    def _on_edit_toggle(self):
        """Alterna entre habilitar/desactivar la edición de la PCB actual."""
        if not self._editing:
            # Entrar en modo edición: habilitar combos
            self._editing = True
            self.view.set_combos_enabled(True)
        else:
            # Salir del modo edición: revertir cambios (recargando el archivo)
            self._editing = False
            self.view.set_combos_enabled(False)
            self._on_pcb_changed(self._cmb_pcb.currentIndex())
        
        self._update_button_states()

    # ── Eliminación de sensor desde la lista visual ─────────────────
    def _on_sensor_deleted(self, name: str):
        """Elimina un sensor de sensors.csv y refresca combos y lista."""
        if name in self._sensors:
            self._sensors.remove(name)

        # Reescribir sensors.csv sin el sensor eliminado
        with open(self._sensors_path, "w", encoding="utf-8") as f:
            for s in self._sensors:
                f.write(f"{s}\n")

        # Refrescar combos de la tabla (conservando selecciones válidas)
        self.view.populate_sensor_combos(self._sensors)

    def get_gas_config(self) -> list[tuple[str, str]]:
        """Devuelve la configuración actual (Sensor #, Referencia)."""
        return self.view.get_row_data()

    @property
    def has_selected_pcb(self) -> bool:
        """Indica si hay una PCB válida seleccionada (no 'Nueva PCB' ni vacío)."""
        if not self._cmb_pcb:
            return False
        text = self._cmb_pcb.currentText()
        return (text != NUEVA_PCB_TEXT) and (text.strip() != "")

