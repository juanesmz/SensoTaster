"""
MicrophoneChartWidget
---------------------
Widget de matplotlib embebido en Qt para visualizar la forma de onda
de audio (amplitud) de un micrófono en tiempo real.

- Inicia vacío (sin señal).
- Se actualiza llamando a update_waveform(samples) con un array numpy.
"""

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import QWidget, QVBoxLayout

WAVEFORM_COLOR  = "#1A1A1A"   # Negro/grafito, igual que la imagen
WAVEFORM_BG     = "#FFFFFF"
WINDOW_SAMPLES  = 4096        # Muestras visibles por defecto


class MicrophoneChartWidget(QWidget):
    """
    Widget de forma de onda de audio en tiempo real.

    Uso:
        widget.update_waveform(numpy_array)  # llamar desde el controlador
    """

    def __init__(self, window_samples: int = WINDOW_SAMPLES, parent=None):
        super().__init__(parent)
        self.window_samples = window_samples
        self._setup_figure()
        self._setup_layout()

    # ------------------------------------------------------------------ #
    #  Setup                                                               #
    # ------------------------------------------------------------------ #

    def _setup_figure(self):
        self.fig = Figure(figsize=(6, 2), dpi=96, tight_layout=True)
        self.fig.patch.set_facecolor(WAVEFORM_BG)

        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(WAVEFORM_BG)
        self.ax.set_ylim(-1.1, 1.1)
        self.ax.set_xlim(0, self.window_samples - 1)

        # Ocultar ejes para lograr el estilo limpio de la imagen
        self.ax.axis("off")

        # Línea de la forma de onda (invisible al inicio)
        x = np.arange(self.window_samples)
        (self.line,) = self.ax.plot(
            x, np.zeros(self.window_samples),
            color=WAVEFORM_COLOR, linewidth=0.8, visible=False
        )

        # Línea central de silencio (siempre visible)
        self.ax.axhline(0, color="#CCCCCC", linewidth=0.5, zorder=0)

        self.canvas = FigureCanvas(self.fig)

    def _setup_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    # ------------------------------------------------------------------ #
    #  API pública                                                         #
    # ------------------------------------------------------------------ #

    def update_waveform(self, samples: np.ndarray):
        """
        Actualiza la forma de onda con nuevas muestras de audio.

        Parameters
        ----------
        samples : np.ndarray  shape (N,) float32 normalizado [-1, 1]
        """
        if samples is None or len(samples) == 0:
            return

        # Hacer visible la línea en la primera actualización
        if not self.line.get_visible():
            self.line.set_visible(True)

        # Redimensionar buffer si la cantidad de muestras cambió
        n = len(samples)
        if n != self.window_samples:
            self.window_samples = n
            self.ax.set_xlim(0, n - 1)

        self.line.set_xdata(np.arange(n))
        self.line.set_ydata(samples)

        # Ajuste dinámico del eje Y con un pequeño margen
        peak = max(abs(samples.max()), abs(samples.min()), 0.05)
        self.ax.set_ylim(-peak * 1.15, peak * 1.15)

        self.canvas.draw_idle()

    def clear(self):
        """Limpia la forma de onda y oculta la línea."""
        self.line.set_ydata(np.zeros(self.window_samples))
        self.line.set_visible(False)
        self.canvas.draw_idle()
