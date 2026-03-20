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

from PySide6.QtCore import QObject
from PySide6.QtWidgets import (
    QComboBox, QInputDialog, QMessageBox, QPushButton,
)


NUEVA_PCB_TEXT = "Nueva PCB"


class GasController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view

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
        self._btn_add_row: QPushButton = ui.findChild(QPushButton, "btnAddRow")
        self._btn_remove_row: QPushButton = ui.findChild(QPushButton, "btnRemoveRow")
        self._btn_save: QPushButton = ui.findChild(QPushButton, "btnSaveConfig")
        self._btn_edit: QPushButton = ui.findChild(QPushButton, "btnEditPcb")

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
        if self._btn_add_row:
            self._btn_add_row.clicked.connect(self._on_add_row)
        if self._btn_remove_row:
            self._btn_remove_row.clicked.connect(self._on_remove_row)
        if self._btn_save:
            self._btn_save.clicked.connect(self._on_save_config)
        if self._btn_edit:
            self._btn_edit.clicked.connect(self._on_edit_toggle)

        # Conexión: eliminación de sensor desde la lista visual
        self.view.sensor_deleted.connect(self._on_sensor_deleted)

    # ── Estado de botones ───────────────────────────────────────────
    def _update_button_states(self):
        """Actualiza el estado de btnSaveConfig y btnEditPcb según el dropdown."""
        if not self._cmb_pcb:
            return
        is_new = self._cmb_pcb.currentText() == NUEVA_PCB_TEXT

        # Guardar: solo activo con 'Nueva PCB'
        if self._btn_save:
            self._btn_save.setEnabled(is_new)

        # Editar: solo activo con una PCB existente (y no en medio de edición)
        if self._btn_edit:
            self._btn_edit.setEnabled(not is_new)
            if is_new:
                self._editing = False
                self._btn_edit.setText("Editar PCB")

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
        if self._btn_edit:
            self._btn_edit.setText("Editar PCB")
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

    # ── Filas ──────────────────────────────────────────────────────
    def _on_add_row(self):
        """Agrega una fila a la tabla y pobla su combo."""
        self.view.add_row()
        self._load_sensors()

    def _on_remove_row(self):
        """Quita la última fila de la tabla."""
        self.view.remove_row()

    # ── Guardar configuración ──────────────────────────────────────
    def _on_save_config(self):
        """Pide nombre de PCB y guarda la configuración como CSV."""
        name, ok = QInputDialog.getText(
            self.view, "Guardar configuración",
            "Nombre de la PCB:",
        )
        if not ok or not name.strip():
            return

        name = name.strip()
        path = os.path.join(self._pcb_dir, f"{name}.csv")

        # Confirmar si ya existe
        if os.path.exists(path):
            reply = QMessageBox.question(
                self.view, "Archivo existente",
                f"'{name}.csv' ya existe. ¿Desea reemplazarlo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Escribir CSV
        data = self.view.get_row_data()
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            for sensor, ref in data:
                writer.writerow([sensor, ref])

        # Refrescar dropdown y volver a "Nueva PCB"
        self._load_pcb_list()
        self._cmb_pcb.setCurrentIndex(0)  # Nueva PCB

        QMessageBox.information(
            self.view, "Configuración guardada",
            f"La configuración '{name}' se guardó correctamente.",
        )

    # ── Editar PCB existente ──────────────────────────────────────
    def _on_edit_toggle(self):
        """Alterna entre 'Editar PCB' y 'Guardar cambios'."""
        if not self._editing:
            # Entrar en modo edición: habilitar combos
            self._editing = True
            if self._btn_edit:
                self._btn_edit.setText("Guardar cambios")
            self.view.set_combos_enabled(True)
        else:
            # Guardar cambios al CSV de la PCB seleccionada
            name = self._cmb_pcb.currentText() if self._cmb_pcb else ""
            if not name or name == NUEVA_PCB_TEXT:
                return

            path = os.path.join(self._pcb_dir, f"{name}.csv")
            data = self.view.get_row_data()

            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                for sensor, ref in data:
                    writer.writerow([sensor, ref])

            # Salir del modo edición
            self._editing = False
            if self._btn_edit:
                self._btn_edit.setText("Editar PCB")
            self.view.set_combos_enabled(False)

            QMessageBox.information(
                self.view, "Cambios guardados",
                f"La configuración de '{name}' se actualizó correctamente.",
            )

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

