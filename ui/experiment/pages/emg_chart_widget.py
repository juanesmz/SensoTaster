"""
EMGChartWidget
--------------
Widget de matplotlib embebido en Qt que dibuja señales EMG en tiempo real.

Modos:
  - Muestra todas las líneas cuya visibilidad esté activada.
  - La visibilidad se controla externamente mediante set_channel_visible().

El gráfico inicia vacío (sin datos). Los datos se inyectan con update_data().
"""

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import QWidget, QVBoxLayout


# Paleta y etiquetas por canal (6 sensores)
CHANNEL_COLORS = ["#E91E63", "#2196F3", "#FF9800", "#9C27B0", "#009688", "#795548"]
CHANNEL_LABELS = [
    "Sensor_1",
    "Sensor_2",
    "Sensor_3",
    "Sensor_4",
    "Sensor_5",
    "Sensor_6",
]
NUM_CHANNELS = len(CHANNEL_COLORS)


class EMGChartWidget(QWidget):
    """
    Widget reutilizable con gráfico EMG en tiempo real.

    Parámetros
    ----------
    window_size : int
        Número de muestras visibles en el eje X.
    """

    def __init__(self, window_size: int = 200, parent=None):
        super().__init__(parent)
        self.window_size = window_size
        # Visibilidad por canal (todos visibles por defecto)
        self._channel_visible: list[bool] = [True] * NUM_CHANNELS

        self._setup_figure()
        self._setup_layout()

    # ------------------------------------------------------------------ #
    #  API pública: visibilidad                                           #
    # ------------------------------------------------------------------ #

    def set_channel_visible(self, index: int, visible: bool):
        """Muestra u oculta un canal específico."""
        if 0 <= index < NUM_CHANNELS:
            self._channel_visible[index] = visible
            self._apply_visibility()
            self._refresh_legend()
            self.canvas.draw_idle()

    # Mantener compatibilidad con active_channel (por si se usa en otro lado)
    @property
    def active_channel(self) -> int:
        return -1

    @active_channel.setter
    def active_channel(self, index: int):
        pass  # ya no se usa, la visibilidad se controla con checkboxes

    # ------------------------------------------------------------------ #
    #  Setup                                                               #
    # ------------------------------------------------------------------ #

    def _setup_figure(self):
        self.fig = Figure(figsize=(5, 3), dpi=96, tight_layout=True)
        self.fig.patch.set_facecolor("#FAFAFA")

        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#FAFAFA")
        self.ax.set_xlabel("Tiempo (0.25 s)", fontsize=8, color="#555555")
        self.ax.set_ylabel("Amplitud (µV)", fontsize=8, color="#555555")
        self.ax.tick_params(colors="#777777", labelsize=7)
        for spine in self.ax.spines.values():
            spine.set_edgecolor("#CCCCCC")
        self.ax.grid(True, linestyle="--", linewidth=0.4, color="#DDDDDD")

        # Crear líneas vacías (una por canal, todas visibles al inicio)
        x = np.arange(self.window_size)
        self.lines = []
        for color, label in zip(CHANNEL_COLORS, CHANNEL_LABELS):
            (line,) = self.ax.plot(
                x, np.zeros(self.window_size),
                color=color, linewidth=1.2, label=label, visible=True
            )
            self.lines.append(line)

        self.legend = self.ax.legend(
            loc="upper left", fontsize=6, framealpha=0.6, ncol=2
        )
        self.ax.set_xlim(0, self.window_size - 1)
        self.ax.set_ylim(0, 400)

        self.canvas = FigureCanvas(self.fig)

    def _setup_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    # ------------------------------------------------------------------ #
    #  Visibilidad                                                          #
    # ------------------------------------------------------------------ #

    def _apply_visibility(self):
        """Muestra solo los canales marcados como visibles."""
        for i, line in enumerate(self.lines):
            line.set_visible(self._channel_visible[i])

    def _refresh_legend(self):
        """Reconstruye la leyenda mostrando solo las líneas visibles."""
        visible_lines = [l for l in self.lines if l.get_visible()]
        if visible_lines:
            self.ax.legend(
                handles=visible_lines,
                loc="upper left",
                fontsize=6,
                framealpha=0.6,
                ncol=2,
            )
        else:
            leg = self.ax.get_legend()
            if leg:
                leg.remove()

    # ------------------------------------------------------------------ #
    #  API pública: recibir datos del controlador                          #
    # ------------------------------------------------------------------ #

    def update_data(self, channels_data: list):
        """
        Actualiza las líneas del gráfico con los buffers recibidos.

        Parameters
        ----------
        channels_data : list[np.ndarray]
            Lista de arrays numpy, uno por canal (orden fijo 0-5).
        """
        x = np.arange(len(channels_data[0]))

        for i, data in enumerate(channels_data):
            if i < len(self.lines):
                self.lines[i].set_xdata(x)
                self.lines[i].set_ydata(data)

        # Auto-scale Y axis
        all_visible = [channels_data[i] for i in range(len(channels_data))
                       if i < len(self.lines) and self.lines[i].get_visible()]
        if all_visible:
            max_val = max(np.max(d) for d in all_visible)
            self.ax.set_ylim(0, max(max_val * 1.1, 50))

        self.ax.set_xlim(0, len(channels_data[0]) - 1)
        self.canvas.draw_idle()
