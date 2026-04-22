import os
import pyqtgraph as pg
from views.base_view import BaseView
from PySide6.QtWidgets import QVBoxLayout

class EMGView(BaseView):
    def __init__(self):
        ui_path = os.path.join("ui", "visualization", "tabs", "emg.ui")
        super().__init__(ui_path)
        self._setup_chart()

    def _setup_chart(self):
        layout = self.ui.findChild(QVBoxLayout, "verticalLayout")
        
        # Create pyqtgraph PlotWidget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w') # White background
        self.plot_widget.setLabel('left', 'Amplitud', units='µV')
        self.plot_widget.setLabel('bottom', 'Tiempo')
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        if layout:
            layout.addWidget(self.plot_widget)
        
        # Store curve items
        self.curves = []
        colors = ["#E91E63", "#2196F3", "#FF9800", "#9C27B0", "#009688", "#795548"]
        for i, color in enumerate(colors):
            curve = self.plot_widget.plot(pen=pg.mkPen(color, width=1.5), name=f"Sensor {i+1}")
            curve.hide()
            self.curves.append(curve)
