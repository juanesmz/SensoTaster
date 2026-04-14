import cv2
import numpy as np
from PySide6.QtCore import QObject, Signal, Slot, QThread, Qt, QEvent
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QComboBox, QPushButton, QSpinBox, QMessageBox

class CameraWorker(QThread):
    frame_ready = Signal(object) # Emit np.ndarray image
    error_occurred = Signal(str)

    def __init__(self, camera_index=0, parent=None):
        super().__init__(parent)
        self.camera_index = camera_index
        self._running = False
        self._cap = None

        self.p1 = None
        self.p2 = None

    def set_roi(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

    def run(self):
        self._running = True
        self._cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            # Try without DSHOW fall back
            self._cap = cv2.VideoCapture(self.camera_index)
        
        if not self._cap.isOpened():
            self.error_occurred.emit(f"No se pudo abrir la cámara {self.camera_index}")
            self._running = False
            return

        while self._running:
            ret, frame = self._cap.read()
            if ret:
                # Dibujar ROI si existen P1 y P2
                if self.p1 is not None and self.p2 is not None:
                    # Garantizar tipos numéricos
                    try:
                        x1, y1 = int(self.p1[0]), int(self.p1[1])
                        x2, y2 = int(self.p2[0]), int(self.p2[1])
                        
                        # Ordenar para que sea un rectangulo correcto
                        rx1, ry1 = min(x1, x2), min(y1, y2)
                        rx2, ry2 = max(x1, x2), max(y1, y2)

                        # Dibujar Rectángulo con grosor
                        cv2.rectangle(frame, (rx1, ry1), (rx2, ry2), (0, 0, 255), 2)
                        
                        # Dibujar puntos y texto
                        cv2.circle(frame, (x1, y1), 4, (0, 0, 255), -1)
                        cv2.putText(frame, "P1", (x1 - 30, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        cv2.circle(frame, (x2, y2), 4, (0, 0, 255), -1)
                        cv2.putText(frame, "P2", (x2 + 10, y2 + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    except Exception as e:
                        print("Error dibujando ROI:", e)

                self.frame_ready.emit(frame)
            else:
                self.msleep(10)

        self._cap.release()

    def stop(self):
        self._running = False
        self.wait(2000)

class ImagingController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view
        self._worker = None

        self._lblImageCam: QLabel = self._find(QLabel, "lblImageCam")
        
        # Combo y botones
        self._cmbCameras: QComboBox = self._find(QComboBox, "cmbCameras")
        self._btnRefresh = self._find(QPushButton, "btnRefreshCameras")
        
        # Spinboxes
        self._spinP1_X = self._find(QSpinBox, "spinP1_X")
        self._spinP1_Y = self._find(QSpinBox, "spinP1_Y")
        self._spinP2_X = self._find(QSpinBox, "spinP2_X")
        self._spinP2_Y = self._find(QSpinBox, "spinP2_Y")
        
        # Buttons point selectors
        self._btnSelectP1: QPushButton = self._find(QPushButton, "btnSelectP1")
        self._btnSelectP2: QPushButton = self._find(QPushButton, "btnSelectP2")

        self._last_frame_size = None  # (width, height)

        self._connect_signals()
        self._setup_event_filter()

        # Iniciar escaneo
        self._populate_cameras()

    def _find(self, widget_type, name: str):
        if self.view and self.view.ui:
            return self.view.ui.findChild(widget_type, name)
        return None

    def get_selected_camera_index(self):
        """Devuelve el índice de la cámara seleccionada en el combo box."""
        if self._cmbCameras:
            data = self._cmbCameras.currentData()
            return data if data is not None else 0
        return 0

    def _connect_signals(self):
        if self._btnRefresh:
            self._btnRefresh.clicked.connect(self._toggle_or_refresh)
        
        # Listeners para spinboxes
        spins = [self._spinP1_X, self._spinP1_Y, self._spinP2_X, self._spinP2_Y]
        for sp in spins:
            if sp:
                sp.valueChanged.connect(self._update_worker_roi)

        # Hacer toggle mutuamente excluyente
        if self._btnSelectP1:
            self._btnSelectP1.toggled.connect(self._on_p1_toggled)
        if self._btnSelectP2:
            self._btnSelectP2.toggled.connect(self._on_p2_toggled)

    def _on_p1_toggled(self, checked):
        if checked and self._btnSelectP2:
            self._btnSelectP2.setChecked(False)
    
    def _on_p2_toggled(self, checked):
        if checked and self._btnSelectP1:
            self._btnSelectP1.setChecked(False)

    def _setup_event_filter(self):
        if self._lblImageCam:
            self._lblImageCam.installEventFilter(self)

    def eventFilter(self, source, event) -> bool:
        if source == self._lblImageCam and event.type() == QEvent.Type.MouseButtonPress:
            self._handle_image_click(event.pos())
            return True
        return super().eventFilter(source, event)

    def _handle_image_click(self, pos):
        # Mapeamos pos al original si la imagen está escalada
        if not self._lblImageCam or not self._lblImageCam.pixmap() or not self._last_frame_size:
            return

        w_label = self._lblImageCam.width()
        h_label = self._lblImageCam.height()
        
        pix_scaled = self._lblImageCam.pixmap()
        w_scaled = pix_scaled.width()
        h_scaled = pix_scaled.height()
        
        w_orig, h_orig = self._last_frame_size

        # El QLabel tiene alineacion al centro (AlignCenter)
        offset_x = (w_label - w_scaled) / 2.0
        offset_y = (h_label - h_scaled) / 2.0

        # Coordenada sobre el pixmap escalado
        px = pos.x() - offset_x
        py = pos.y() - offset_y

        # Ignorar si se dio clic en las barras negras
        if px < 0 or py < 0 or px > w_scaled or py > h_scaled:
            return

        x_ratio = w_orig / float(w_scaled)
        y_ratio = h_orig / float(h_scaled)

        real_x = int(px * x_ratio)
        real_y = int(py * y_ratio)

        if self._btnSelectP1 and self._btnSelectP1.isChecked():
            if self._spinP1_X: self._spinP1_X.setValue(real_x)
            if self._spinP1_Y: self._spinP1_Y.setValue(real_y)
            self._btnSelectP1.setChecked(False)
            
        elif self._btnSelectP2 and self._btnSelectP2.isChecked():
            if self._spinP2_X: self._spinP2_X.setValue(real_x)
            if self._spinP2_Y: self._spinP2_Y.setValue(real_y)
            self._btnSelectP2.setChecked(False)

    def _update_worker_roi(self):
        if not self._worker:
            return
        
        try:
            x1 = self._spinP1_X.value()
            y1 = self._spinP1_Y.value()
            x2 = self._spinP2_X.value()
            y2 = self._spinP2_Y.value()

            # Solo enviamos coordenadas validas (distintas de 0 salvo en esquina superior izquierda, pero consideremos un inicio simple)
            self._worker.set_roi((x1, y1), (x2, y2))
        except Exception:
            pass

    def _populate_cameras(self):
        if not self._cmbCameras:
            return

        self._cmbCameras.clear()
        self._cmbCameras.addItem("Buscando cámaras...", None)
        self._cmbCameras.setEnabled(False)

        # Intentar obtener nombres descriptivos via Qt (opcional, puede fallar)
        qt_names: dict[int, str] = {}
        try:
            from PySide6.QtMultimedia import QMediaDevices
            qt_cameras = QMediaDevices.videoInputs()
            for i, cam in enumerate(qt_cameras):
                desc = cam.description()
                if desc:
                    qt_names[i] = desc
        except Exception:
            pass

        # Detección real: probar índices con OpenCV (igual que CameraWorker)
        found = []
        for idx in range(10):
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if cap.isOpened():
                name = qt_names.get(len(found), qt_names.get(idx, f"Cámara {idx}"))
                found.append((idx, name))
                cap.release()

        self._cmbCameras.clear()
        if found:
            for idx, name in found:
                self._cmbCameras.addItem(name, idx)
        else:
            self._cmbCameras.addItem("Ninguna cámara detectada", None)

        self._cmbCameras.setEnabled(True)

    def _toggle_or_refresh(self):
        # Si esta corriendo el worker, detenemos
        if self._worker and self._worker.isRunning():
            self._stop_camera()
            if self._btnRefresh:
                self._btnRefresh.setText("Conectar / Iniciar")
        else:
            # Si no hay cámara seleccionada pero usuario intenta conectar, refrescamos la lista
            if self._cmbCameras.currentData() is None:
                self._populate_cameras()

            # Start
            idx = self._cmbCameras.currentData()
            if idx is not None:
                self._start_camera(idx)
                if self._btnRefresh:
                    self._btnRefresh.setText("Detener")

    def _start_camera(self, index=0):
        self._stop_camera()
        self._worker = CameraWorker(camera_index=index, parent=self)
        self._worker.frame_ready.connect(self._on_frame_ready)
        self._worker.error_occurred.connect(self._on_camera_error)
        self._update_worker_roi()
        self._worker.start()

    def _stop_camera(self):
        if self._worker:
            self._worker.stop()
            self._worker = None

    @Slot(object)
    def _on_frame_ready(self, frame):
        if not self._lblImageCam:
            return

        # Frame is BGR, we need RGB
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        self._last_frame_size = (w, h)
        bytes_per_line = ch * w
        
        q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pix = QPixmap.fromImage(q_img)
        
        # Fit inside the QLabel safely
        pix_scaled = pix.scaled(self._lblImageCam.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self._lblImageCam.setPixmap(pix_scaled)

    @Slot(str)
    def _on_camera_error(self, message):
        print("Camera Controller Error:", message)
        if getattr(self, "view", None):
            QMessageBox.warning(self.view, "Error en cámara", message)
