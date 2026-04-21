import os
import cv2
import time
import wave
import csv
import serial
import numpy as np
import sounddevice as sd
from datetime import datetime
from PySide6.QtCore import QObject, QThread, Signal, Slot, QTimer
from PySide6.QtWidgets import QPushButton, QMessageBox, QLabel
from navigation.router import router
from env_config import ENV

class AudioRecorderWorker(QThread):
    def __init__(self, device_index, filename, channel=0, num_channels=1, samplerate=44100):
        super().__init__()
        self.device_index = device_index
        self.filename = filename
        self.channel = channel
        self.num_channels = num_channels
        self.samplerate = samplerate
        self._running = False

    def run(self):
        self._running = True
        try:
            os.makedirs(os.path.dirname(self.filename), exist_ok=True)
            with wave.open(self.filename, 'wb') as wf:
                wf.setnchannels(1) 
                wf.setsampwidth(2) 
                wf.setframerate(self.samplerate)
                with sd.InputStream(device=self.device_index, channels=self.num_channels, 
                                    samplerate=self.samplerate, dtype='int16') as stream:
                    while self._running:
                        data, overflowed = stream.read(2048)
                        if self._running and not overflowed:
                            if self.num_channels > 1:
                                mono_data = data[:, self.channel].copy()
                            else:
                                mono_data = data.copy()
                            wf.writeframes(mono_data.tobytes())
        except Exception as e:
            print(f"[AudioRecorderWorker] Error: {e}")

    def stop(self):
        self._running = False
        self.wait(2000)

class SerialRecorderWorker(QThread):
    data_received = Signal(list)
    error_occurred = Signal(str)
    def __init__(self, port, baudrate=115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self._running = False

    def run(self):
        self._running = True
        try:
            with serial.Serial(self.port, self.baudrate, timeout=1) as ser:
                ser.reset_input_buffer()
                while self._running:
                    if ser.in_waiting > 0:
                        try:
                            line = ser.readline().decode('utf-8', errors='ignore').strip()
                            if not line: continue
                            
                            # Validación: 6 números enteros separados por comas
                            parts = [p.strip() for p in line.split(',') if p.strip()]
                            if len(parts) != 6:
                                self.error_occurred.emit(f"Datos EMG inválidos: se recibieron {len(parts)} valores en lugar de 6.")
                                break
                            
                            try:
                                values = [int(p) for p in parts]
                                self.data_received.emit(values)
                            except ValueError:
                                self.error_occurred.emit("Datos EMG inválidos: los valores deben ser números enteros.")
                                break
                        except Exception as e:
                            self.error_occurred.emit(f"Error de lectura serial: {str(e)}")
                            break
                    else:
                        self.msleep(5)
        except Exception as e:
            self.error_occurred.emit(f"No se pudo conectar al puerto {self.port}: {str(e)}")
            print(f"[SerialRecorderWorker] Error: {e}")

    def stop(self):
        self._running = False
        self.wait(2000)

class GasRecorderWorker(QThread):
    """Hilo para leer datos de LabJack y guardar en CSV por 1 minuto."""
    def __init__(self, filename, sensors_config, duration=60):
        super().__init__()
        self.filename = filename
        self.config = sensors_config # list of (sensor_name, reference)
        self.duration = duration
        self._running = False

    def run(self):
        self._running = True
        
        # Filtrar solo sensores con referencia válida (distinta a N/A)
        active_config = [c for c in self.config if c[1] != "N/A"]
        if not active_config:
            print("[GasRecorderWorker] Sin sensores configurados.")
            self._running = False
            return

        # Mapear SG_X a AIN(X-1) y guardar referencias para el CSV
        names = []
        refs = []
        for sid, ref in active_config:
            try:
                num = int(sid.split("_")[1])
                names.append(f"AIN{num-1}")
                refs.append(ref)
            except Exception:
                continue

        num_sensors = len(names)
        
        try:
            from labjack import ljm
            handle = None
            try:
                # ANY, ANY, ANY intenta abrir cualquier LabJack por USB o RED
                handle = ljm.openS("ANY", "ANY", "ANY")
            except Exception:
                print("[GasRecorderWorker] LabJack no encontrado. Iniciando Simulación.")
                handle = None

            os.makedirs(os.path.dirname(self.filename), exist_ok=True)
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                # Encabezado con los nombres de referencia de los sensores
                writer.writerow(["Timestamp"] + refs)
                
                start_time = time.time()
                while self._running and (time.time() - start_time < self.duration):
                    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    if handle:
                        # Lectura múltiple de canales LabJack
                        results = ljm.eReadNames(handle, num_sensors, names)
                    else:
                        # Simulación de lecturas aleatorias si no hay hardware
                        import random
                        results = [round(random.uniform(0.5, 2.5), 3) for _ in range(num_sensors)]
                    
                    writer.writerow([ts] + results)
                    time.sleep(0.5) # Lectura cada 500ms
                    
            if handle:
                ljm.close(handle)
        except Exception as e:
            print(f"[GasRecorderWorker] Error en GasRecorderWorker: {e}")
        finally:
            print(f"[GasRecorderWorker] Captura de gases finalizada ({self.filename})")

    def stop(self):
        self._running = False
        self.wait(2000)

class PhotoCaptureWorker(QThread):
    """Hilo para capturar ráfaga de fotos sin bloquear la UI."""
    def __init__(self, directory, camera_index, roi=None):
        super().__init__()
        self.directory = directory
        self.camera_index = camera_index
        self.roi = roi

    def run(self):
        try:
            import cv2
            cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(self.camera_index)
            if not cap.isOpened():
                return

            # Calentamiento / Auto-exposición
            for _ in range(5):
                cap.read()
                time.sleep(0.1)

            for i in range(1, 11):
                ret, frame = cap.read()
                if ret:
                    if self.roi:
                        try:
                            p1, p2 = self.roi
                            x1, y1 = int(p1[0]), int(p1[1])
                            x2, y2 = int(p2[0]), int(p2[1])
                            rx1, ry1 = min(x1, x2), min(y1, y2)
                            rx2, ry2 = max(x1, x2), max(y1, y2)
                            h, w = frame.shape[:2]
                            rx1, ry1 = max(0, rx1), max(0, ry1)
                            rx2, ry2 = min(w, rx2), min(h, ry2)
                            if rx2 > rx1 and ry2 > ry1:
                                frame = frame[ry1:ry2, rx1:rx2]
                        except: pass
                    
                    cv2.imwrite(os.path.join(self.directory, f"foto_{i}.jpg"), frame)
                    time.sleep(0.2)
            cap.release()
        except Exception as e:
            print(f"[PhotoCaptureWorker] Error: {e}")

class RunningExpController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view
        self._audio_recorders = {} 
        self._emg_files = {} 
        self._emg_handles = {} 
        self._emg_worker = None
        self._gas_worker = None
        
        # Temporizador de gases
        self._gas_timer = QTimer()
        self._gas_timer.setInterval(1000) # 1 segundo
        self._gas_timer.timeout.connect(self._update_gas_timer_ui)
        self._gas_remaining_seconds = 60

        self._setup_connections()

    def _setup_connections(self):
        ui = self.view.ui
        for i in range(1, 7):
            btn = ui.findChild(QPushButton, f"btnStopUser{i}")
            if btn:
                btn.clicked.connect(self._make_stop_handler(i))
        
        btn_finish = ui.findChild(QPushButton, "btnFinishExp")
        if btn_finish:
            btn_finish.clicked.connect(self._on_finish_experiment)

    def _make_stop_handler(self, idx):
        return lambda: self._on_stop_user(idx)

    def prepare_session(self, base_path, modules_status, omitted_modules, user_data, 
                        camera_index=0, roi=None, mic_list=None, emg_indices=None, gas_config=None):
        self.session_params = {
            "base_path": base_path,
            "modules_status": modules_status,
            "omitted_modules": omitted_modules,
            "user_data": user_data,
            "camera_index": camera_index,
            "roi": roi,
            "mic_list": mic_list or [],
            "emg_indices": emg_indices or [],
            "gas_config": gas_config or []
        }

    def start_session(self):
        if not hasattr(self, "session_params"): return
        params = self.session_params
        
        # ── Habilitar/Deshabilitar botones según usuarios configurados ──
        num_users = len(params.get("user_data", []))
        for i in range(1, 7):
            btn = self.view.ui.findChild(QPushButton, f"btnStopUser{i}")
            if btn:
                if i <= num_users:
                    btn.setEnabled(True)
                    btn.setText(f"Detener captura de usuario {i}")
                    # Color rojo original (desde el .ui o similar)
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #F44336;
                            color: white;
                            border-radius: 15px;
                            border: 2px solid #D32F2F;
                        }
                        QPushButton:hover { background-color: #EF5350; }
                    """)
                else:
                    btn.setEnabled(False)
                    btn.setText(f"Usuario {i} no configurado")
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #E0E0E0;
                            color: #9E9E9E;
                            border-radius: 15px;
                            border: 1px solid #BDBDBD;
                        }
                    """)

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = os.path.join(params["base_path"], timestamp)
            os.makedirs(session_dir, exist_ok=True)
            
            # Gases
            if params["modules_status"][1] and not params["omitted_modules"][1]:
                gas_dir = os.path.join(session_dir, "Sensores de Gases")
                os.makedirs(gas_dir, exist_ok=True)
                csv_path = os.path.join(gas_dir, "gases.csv")
                self._gas_worker = GasRecorderWorker(csv_path, params["gas_config"])
                self._gas_worker.start()
                
                # Iniciar temporizador visual
                self._gas_remaining_seconds = self._gas_worker.duration
                self._update_gas_timer_ui()
                self._gas_timer.start()
            else:
                # Ocultar panel de gases si no se usa
                lbl_title = self.view.ui.findChild(QLabel, "lblGasTitle")
                lbl_timer = self.view.ui.findChild(QLabel, "lblGasTimer")
                if lbl_title: lbl_title.setVisible(False)
                if lbl_timer: lbl_timer.setVisible(False)
            
            # Imagenes (Asíncrono para no bloquear)
            if params["modules_status"][4] and not params["omitted_modules"][4]:
                img_dir = os.path.join(session_dir, "Imagenes")
                os.makedirs(img_dir, exist_ok=True)
                self._photo_worker = PhotoCaptureWorker(img_dir, params["camera_index"], params.get("roi"))
                self._photo_worker.start()
            
            # Usuarios (EMG / Mic)
            emg_active = params["modules_status"][2] and not params["omitted_modules"][2]
            mic_active = params["modules_status"][3] and not params["omitted_modules"][3]
            
            if emg_active or mic_active:
                for i, user in enumerate(params["user_data"]):
                    user_num = i + 1
                    user_folder_name = f"{user['id']}_{user['gender']}_{user['age']}"
                    user_path = os.path.join(session_dir, user_folder_name)
                    os.makedirs(user_path, exist_ok=True)
                    
                    if mic_active and i < len(params["mic_list"]):
                        mic_info = params["mic_list"][i]
                        audio_file = os.path.join(user_path, f"audio_user_{user_num}.wav")
                        recorder = AudioRecorderWorker(mic_info["device_index"], audio_file, 
                                                       mic_info.get("channel", 0), mic_info.get("num_channels", 1))
                        self._audio_recorders[user_num] = recorder
                        recorder.start()

                    if emg_active and i < len(params["emg_indices"]):
                        sensor_idx = params["emg_indices"][i]
                        csv_path = os.path.join(user_path, f"emg_user_{user_num}.csv")
                        f = open(csv_path, 'w', newline='')
                        writer = csv.writer(f)
                        writer.writerow(["Timestamp", "EMG_Value", "Physical_Channel"])
                        self._emg_handles[user_num] = f
                        self._emg_files[user_num] = (writer, sensor_idx)

                if self._emg_files:
                    port = ENV.get("ARDUINO_COM_PORT", "COM6")
                    self._emg_worker = SerialRecorderWorker(port)
                    self._emg_worker.data_received.connect(self._on_emg_data)
                    self._emg_worker.error_occurred.connect(self._on_emg_error)
                    self._emg_worker.start()
            
            print(f"[RunningExpController] Sesión iniciada en: {session_dir}")
        except Exception as e:
            QMessageBox.critical(self.view, "Error", f"No se pudo iniciar la sesión:\n{str(e)}")

    @Slot(list)
    def _on_emg_data(self, values):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        for user_num, (writer, sensor_idx) in self._emg_files.items():
            if sensor_idx < len(values):
                writer.writerow([ts, values[sensor_idx], sensor_idx])

    @Slot(str)
    def _on_emg_error(self, error_msg):
        print(f"[RunningExpController] Error EMG: {error_msg}")
        QMessageBox.critical(self.view, "Error de Sensores EMG", 
                             f"Se produjo un error crítico en la lectura de los sensores EMG durante la experimentación:\n\n{error_msg}")
        if self._emg_worker:
            self._emg_worker.stop()
            self._emg_worker = None

    def _on_stop_user(self, user_idx):
        if user_idx in self._audio_recorders:
            self._audio_recorders[user_idx].stop()
            del self._audio_recorders[user_idx]
        if user_idx in self._emg_files:
            f = self._emg_handles.get(user_idx)
            if f:
                f.close()
                del self._emg_handles[user_idx]
            del self._emg_files[user_idx]

        btn = self.view.ui.findChild(QPushButton, f"btnStopUser{user_idx}")
        if btn:
            btn.setEnabled(False)
            btn.setText(f"Captura {user_idx} Finalizada")
            btn.setStyleSheet("background-color: #9E9E9E; color: white; border-radius: 15px;")
        
        if not self._audio_recorders and not self._emg_files:
            if self._emg_worker:
                self._emg_worker.stop()
                self._emg_worker = None
            print("[RunningExpController] Todos los usuarios han finalizado su captura local.")

    def _on_finish_experiment(self):
        """Finaliza toda la sesión de experimentación tras confirmación."""
        reply = QMessageBox.question(
            self.view, 
            "Finalizar Experimentación", 
            "¿Está seguro de que desea finalizar la experimentación y volver al menú principal?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Detener todos los hilos activos
            if self._emg_worker:
                self._emg_worker.stop()
                self._emg_worker = None
            
            if self._gas_worker:
                self._gas_worker.stop()
                self._gas_worker = None

            if hasattr(self, "_gas_timer") and self._gas_timer:
                self._gas_timer.stop()

            # Detener cualquier grabador de audio que siga activo
            for user_idx in list(self._audio_recorders.keys()):
                self._audio_recorders[user_idx].stop()
                del self._audio_recorders[user_idx]

            router.go_to("main_menu")

    def _update_gas_timer_ui(self):
        """Actualiza el label del temporizador de gases cada segundo."""
        if self._gas_remaining_seconds <= 0:
            self._gas_timer.stop()
            lbl_timer = self.view.ui.findChild(QLabel, "lblGasTimer")
            if lbl_timer:
                lbl_timer.setText("00:00")
                lbl_timer.setStyleSheet("color: #4CAF50; border: none;") # Cambiar a verde al terminar
            return

        minutes = self._gas_remaining_seconds // 60
        seconds = self._gas_remaining_seconds % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        lbl_timer = self.view.ui.findChild(QLabel, "lblGasTimer")
        if lbl_timer:
            lbl_timer.setText(time_str)
        
        self._gas_remaining_seconds -= 1
