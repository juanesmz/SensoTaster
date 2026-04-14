import os
from views.base_view import BaseView

class GasSensorsView(BaseView):
    def __init__(self):
        ui_path = os.path.join("ui", "visualization", "tabs", "gas_sensors.ui")
        super().__init__(ui_path)
