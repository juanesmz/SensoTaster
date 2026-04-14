import os
import cv2
import time
import wave
import csv
import serial
import numpy as np
import sounddevice as sd
from datetime import datetime
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QPushButton, QMessageBox
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
                        line = ser.readline().decode('utf-8', errors='ignore').strip()
                        if not line: continue
                        parts = line.split(', ')
                        values = []
                        for p in parts:
                            try: values.append(float(p))
                            except: pass
                        if len(values) >= 6:
                            self.data_received.emit(values[:6])
                    else:
                        self.msleep(5)
        except Exception as e:
            print(f"[SerialRecorderWorker] Error: {e}")

    def stop(self):
        self._running = False
        self.wait(2000)

class GasRecorderWorker(QThread):
    """Hilo para leer datos de LabJack y guardar en CSV por 15 segundos."""
    def __init__(self, filename, sensors_config, duration=15):
        super().__init__()
        self.filename = filename
        self.config = sensors_config # list of (sensor_name, reference)
        self.duration = duration
        self._running = False

    def run(self):
        self._running = True
        refs = [c[1] for c in self.config]
        num_sensors = len(refs)
        
        try:
            import random
            from labjack import ljm
            handle = None
            try:
                handle = ljm.openS("ANY", "ANY", "ANY")
                names = [f"AIN{i}" for i in range(num_sensors)]
            except:
                print("[GasRecorderWorker] LabJack no encontrado. Iniciando Simulación.")
                handle = None

            os.makedirs(os.path.dirname(self.filename), exist_ok=True)
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp"] + refs)
                
                start_time = time.time()
                while self._running and (time.time() - start_time < self.duration):
                    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    if handle:
                        results = ljm.eReadNames(handle, num_sensors, names)
                    else:
                        # Simulación
                        results = [round(random.uniform(0.5, 2.5), 3) for _ in range(num_sensors)]
                    
                    writer.writerow([ts] + results)
                    time.sleep(0.5) # Lectura cada 500ms
                    
            if handle:
                ljm.close(handle)
        except Exception as e:
            print(f"[GasRecorderWorker] Error: {e}")
        finally:
            print(f"[GasRecorderWorker] Captura finalizada ({self.filename})")

    def stop(self):
        self._running = False
        self.wait(2000)

class RunningExpController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view
        self._audio_recorders = {} 
        self._emg_files = {} 
        self._emg_handles = {} 
        self._emg_worker = None
        self._gas_worker = None
        self._setup_connections()

    def _setup_connections(self):
        for i in range(1, 7):
            btn = self.view.ui.findChild(QPushButton, f"btnStopUser{i}")
            if btn:
                btn.clicked.connect(self._make_stop_handler(i))

    def _make_stop_handler(self, idx):
        return lambda: self._on_stop_user(idx)

    def prepare_session(self, base_path, modules_status, omitted_modules, user_data, 
                        camera_index=0, mic_list=None, emg_indices=None, gas_config=None):
        self.session_params = {
            "base_path": base_path,
            "modules_status": modules_status,
            "omitted_modules": omitted_modules,
            "user_data": user_data,
            "camera_index": camera_index,
            "mic_list": mic_list or [],
            "emg_indices": emg_indices or [],
            "gas_config": gas_config or []
        }

    def start_session(self):
        if not hasattr(self, "session_params"): return
        params = self.session_params
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
            
            # Imagenes
            if params["modules_status"][4] and not params["omitted_modules"][4]:
                img_dir = os.path.join(session_dir, "Imagenes")
                os.makedirs(img_dir, exist_ok=True)
                self._capture_photos(img_dir, params["camera_index"])
            
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
            
            # Nota: El gas_worker se detiene solo a los 15s o al salir
            reply = QMessageBox.question(self.view, "Finalizar", "¿Desea finalizar el experimento?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                if self._gas_worker: self._gas_worker.stop()
                router.go_to("main_menu")

    def _capture_photos(self, directory, camera_index):
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened(): cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened(): return
        for _ in range(5): cap.read(); time.sleep(0.1)
        for i in range(1, 11):
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(os.path.join(directory, f"foto_{i}.jpg"), frame)
                time.sleep(0.1)
        cap.release()
