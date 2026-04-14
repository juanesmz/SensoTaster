from PySide6.QtCore import QObject
from PySide6.QtWidgets import QPushButton, QLineEdit, QFileDialog, QTableWidget, QHeaderView, QWidget, QSpinBox, QHBoxLayout

class ConfigurationController(QObject):
    def __init__(self, view, emg_controller=None, mic_controller=None, experiment_controller=None):
        super().__init__()
        self.view = view
        self.emg_controller = emg_controller
        self.mic_controller = mic_controller
        self.experiment_controller = experiment_controller
        self._setup_connections()

    def refresh(self):
        """Refresca el estado de la tabla según los módulos activos."""
        if not self.experiment_controller:
            return

        # Indices: EMG=2, Mic=3
        emg_active = (self.experiment_controller._checked[2] and not self.experiment_controller._reds[2])
        mic_active = (self.experiment_controller._checked[3] and not self.experiment_controller._reds[3])

        can_edit = emg_active or mic_active
        
        # Habilitar/deshabilitar tabla
        if self.table:
            self.table.setEnabled(can_edit)
            # Opacidad visual para indicar bloqueo
            self.table.setWindowOpacity(1.0 if can_edit else 0.5)
            
            if can_edit:
                emg_count = self.emg_controller.num_selected_sensors if self.emg_controller else 0
                mic_count = self.mic_controller.num_selected_microphones if self.mic_controller else 0
                
                # Determinamos la cantidad de participantes (el máximo de ambos módulos)
                count = max(emg_count, mic_count)
                if count != self.table.rowCount():
                    self._setup_table(count)
            else:
                self.table.setRowCount(0)

    def get_base_path(self):
        return self.line_path.text() if self.line_path else ""

    def get_user_data(self):
        users = []
        if not self.table:
            return users
            
        for row in range(self.table.rowCount()):
            # Col 1: Edad (SpinBox dentro de container)
            # Col 2: Genero (Widget con 2 botones dentro de container)
            # Col 3: ID (LineEdit dentro de container)
            
            # Edad
            age = 0
            age_cont = self.table.cellWidget(row, 1)
            if age_cont:
                spin = age_cont.findChild(QSpinBox)
                if spin: age = spin.value()
                
            # Género
            gender = "M" 
            gen_cont = self.table.cellWidget(row, 2)
            if gen_cont:
                btns = gen_cont.findChildren(QPushButton)
                for b in btns:
                    if b.isChecked():
                        gender = "M" if b.text() == "Masculino" else "F"
                        break
            
            # ID
            user_id = ""
            id_cont = self.table.cellWidget(row, 3)
            if id_cont:
                line = id_cont.findChild(QLineEdit)
                if line: user_id = line.text()
                
            users.append({
                "id": user_id,
                "gender": gender,
                "age": age
            })
        return users

    def _setup_connections(self):
        btn_browse = self.view.ui.findChild(QPushButton, "btnBrowse")
        self.line_path = self.view.ui.findChild(QLineEdit, "linePath")
        self.table = self.view.ui.findChild(QTableWidget, "tableUsers")
        
        # Ajustar el layout para que la tabla tome el espacio
        # El layout principal está directamente en self.view.ui
        main_layout = self.view.ui.layout()
        # Encontramos el verticalLayoutGeneral que está dentro del frame
        main_frame = self.view.ui.findChild(QWidget, "frameMainContainer")
        if main_frame:
            v_lay = main_frame.layout()
            if v_lay:
                # Top row (0), Table (1)
                v_lay.setStretch(0, 0)
                v_lay.setStretch(1, 1)

        if btn_browse:
            btn_browse.clicked.connect(self._on_browse)
        
        if self.table:
            self._setup_table()

    def _setup_table(self, count=6):
        from PySide6.QtWidgets import QTableWidgetItem, QSpinBox, QLineEdit, QHBoxLayout, QWidget, QLabel
        from PySide6.QtCore import Qt
        
        self.table.setRowCount(0) # Limpiar
        self.table.setRowCount(count)
        
        # Ajustar para que la tabla use todo el espacio disponible
        header_h = self.table.horizontalHeader()
        header_h.setSectionResizeMode(QHeaderView.Stretch)
        header_h.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_v = self.table.verticalHeader()
        header_v.setSectionResizeMode(QHeaderView.Stretch) # Esto hace que las filas se expandan verticalmente
        header_v.setDefaultSectionSize(60) 
        header_v.setVisible(False)
        
        if count == 0:
            return

        for row in range(count):
            # Column 0: Usuario #
            item_num = QTableWidgetItem(str(row + 1))
            item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, item_num)
            
            # Column 1: Edad
            spin = QSpinBox()
            spin.setRange(0, 120)
            spin.setValue(25 if row % 2 == 0 else 20)
            spin.setMinimumHeight(45)
            spin.setStyleSheet("QSpinBox { background-color: white; border: 1px solid #CCCCCC; border-radius: 4px; padding-left: 5px; }")
            self.table.setCellWidget(row, 1, self._center_widget(spin))
            
            # Column 2: Género (Two buttons)
            btn_male = QPushButton("Masculino")
            btn_female = QPushButton("Femenino")
            
            # Estilo para los botones de género
            gender_style = """
                QPushButton {
                    background-color: #E0E0E0;
                    color: black;
                    font-weight: bold;
                    border-radius: 5px;
                    border: 1px solid #CCCCCC;
                }
                QPushButton:checked {
                    background-color: #4CAF50;
                    color: white;
                    border: 1px solid #388E3C;
                }
                QPushButton:hover:not(:checked) {
                    background-color: #D5D5D5;
                }
            """
            
            for b in [btn_male, btn_female]:
                b.setCheckable(True)
                b.setMinimumHeight(45)
                b.setFixedWidth(110)
                b.setStyleSheet(gender_style)
            
            btn_male.setChecked(True)
            
            # Contenedor para los dos botones
            gender_widget = QWidget()
            gender_lay = QHBoxLayout(gender_widget)
            gender_lay.addWidget(btn_male)
            gender_lay.addWidget(btn_female)
            gender_lay.setContentsMargins(0, 0, 0, 0)
            gender_lay.setSpacing(10)
            
            # Hacerlos exclusivos dentro de la fila
            from PySide6.QtWidgets import QButtonGroup
            group = QButtonGroup(gender_widget)
            group.addButton(btn_male)
            group.addButton(btn_female)
            group.setExclusive(True)
            
            self.table.setCellWidget(row, 2, self._center_widget(gender_widget))
            
            # Column 3: ID
            line = QLineEdit(f"USR_00{row+1}")
            line.setMinimumHeight(45)
            line.setStyleSheet("QLineEdit { background-color: #E0E0E0; border: 1px solid #CCCCCC; border-radius: 4px; padding-left: 5px; }")
            self.table.setCellWidget(row, 3, self._center_widget(line))

    def _center_widget(self, widget):
        from PySide6.QtWidgets import QWidget, QHBoxLayout
        from PySide6.QtCore import Qt
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(10, 5, 10, 5)
        return container

    def _on_browse(self):
        directory = QFileDialog.getExistingDirectory(
            self.view,
            "Seleccionar Carpeta para Guardar Archivos",
            self.line_path.text() if self.line_path else ""
        )
        if directory and self.line_path:
            self.line_path.setText(directory)
