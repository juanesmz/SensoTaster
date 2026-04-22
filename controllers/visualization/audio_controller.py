import os
import numpy as np
import soundfile as sf
from PySide6.QtCore import QObject, QUrl
from PySide6.QtWidgets import QComboBox, QPushButton
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import pyqtgraph as pg

class AudioController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view
        self.audio_data = {}  # {filename: (data, samplerate)}
        self.current_directory = ""
        
        # Initialize Qt Multimedia Player
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)
        
        self._setup_connections()

    def _setup_connections(self):
        self.combo_audio = self.view.ui.findChild(QComboBox, "comboAudio")
        self.btn_play = self.view.ui.findChild(QPushButton, "btnPlay")
        
        if self.btn_play:
            self.btn_play.clicked.connect(self._toggle_playback)
            
        # Connect player signals for marker update
        self.player.positionChanged.connect(self._update_playback_marker)
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)

    def load_data(self, directory):
        """Loads WAV files for visualization."""
        self.current_directory = directory
        audio_dir = os.path.join(directory, "Audio")
        if not os.path.isdir(audio_dir):
            return

        wav_files = sorted([f for f in os.listdir(audio_dir) if f.lower().endswith(".wav")])
        if not wav_files:
            return

        self.audio_data = {}
        self.view.plot_widget.clear()
        
        self.view.marker = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('r', width=2, style=pg.QtCore.Qt.DashLine))
        self.view.marker.hide()
        self.view.plot_widget.addItem(self.view.marker)
        
        colors = ["#007bff", "#28a745", "#dc3545", "#ffc107", "#17a2b8", "#6610f2"]
        
        for i, filename in enumerate(wav_files):
            path = os.path.join(audio_dir, filename)
            try:
                data, samplerate = sf.read(path)
                self.audio_data[filename] = (data, samplerate)
                
                vis_data = data[:, 0] if len(data.shape) > 1 else data
                duration = len(data) / samplerate
                t = np.linspace(0, duration, len(vis_data))
                
                color = colors[i % len(colors)]
                self.view.plot_widget.plot(t, vis_data, pen=pg.mkPen(color, width=1), name=filename)
                
            except Exception as e:
                print(f"Error cargando audio {filename}: {e}")

        if self.combo_audio:
            self.combo_audio.clear()
            self.combo_audio.addItems(wav_files)
        
        self.view.plot_widget.autoRange()

    def _toggle_playback(self):
        """Starts or stops audio playback using QMediaPlayer."""
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.stop()
            return

        filename = self.combo_audio.currentText()
        if filename:
            path = os.path.join(self.current_directory, "Audio", filename)
            if os.path.exists(path):
                self.player.setSource(QUrl.fromLocalFile(path))
                self.player.play()

    def _update_playback_marker(self, position_ms):
        """Updates the vertical marker position based on QMediaPlayer position."""
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            seconds = position_ms / 1000.0
            self.view.marker.setValue(seconds)
            self.view.marker.show()

    def _on_playback_state_changed(self, state):
        """Updates UI based on player state."""
        if state == QMediaPlayer.PlayingState:
            self.btn_play.setText("Detener")
            self.btn_play.setStyleSheet("background-color: #dc3545; color: white;")
        else:
            self.btn_play.setText("Reproducir Audio")
            self.btn_play.setStyleSheet("")
            self.view.marker.hide()
