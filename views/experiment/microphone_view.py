"""
MicrophoneView
--------------
Vista de la página de micrófonos. Carga el .ui e inyecta el widget
de forma de onda en el waveformContainer.
"""

import os
from PySide6.QtWidgets import QVBoxLayout, QWidget
from views.base_view import BaseView
from ui.experiment.pages.microphone_chart_widget import MicrophoneChartWidget


class MicrophoneView(BaseView):
    def __init__(self):
        super().__init__(os.path.join("ui", "experiment", "pages", "microphone.ui"))
        self.chart_widget: MicrophoneChartWidget | None = None
        self._setup_chart()

    def _setup_chart(self):
        """Inyecta el MicrophoneChartWidget dentro del waveformContainer."""
        if not self.ui:
            return

        container: QWidget = self.ui.findChild(QWidget, "waveformContainer")
        if container is None:
            print("Warning: waveformContainer no encontrado en MicrophoneView")
            return

        self.chart_widget = MicrophoneChartWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.chart_widget)
