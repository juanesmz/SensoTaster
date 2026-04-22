import os
import pyqtgraph as pg
from PySide6.QtWidgets import QVBoxLayout
from views.base_view import BaseView

class AudioView(BaseView):
    def __init__(self):
        ui_path = os.path.join("ui", "visualization", "tabs", "audio.ui")
        super().__init__(ui_path)
        self._setup_plot()

    def _setup_plot(self):
        # Create pyqtgraph PlotWidget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w') # White background
        self.plot_widget.setLabel('left', 'Amplitud')
        self.plot_widget.setLabel('bottom', 'Tiempo', units='s')
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Playback marker (InfiniteLine)
        self.marker = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('r', width=2, style=pg.QtCore.Qt.DashLine))
        self.marker.hide()
        self.plot_widget.addItem(self.marker)
        
        # Add widget to layout
        layout = self.ui.findChild(QVBoxLayout, "verticalLayoutPlot")
        if layout:
            layout.addWidget(self.plot_widget)
        
        # Store curves
        self.curves = {}
