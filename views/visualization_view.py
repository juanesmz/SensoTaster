import os
from views.base_view import BaseView

class VisualizationView(BaseView):
    def __init__(self):
        super().__init__(os.path.join("ui", "visualization", "visualization.ui"))
        self._setup_header_logos()
