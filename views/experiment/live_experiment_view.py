import os
from views.base_view import BaseView

class LiveExperimentView(BaseView):
    def __init__(self):
        super().__init__(os.path.join("ui", "experiment", "live_experiment.ui"))
        self._setup_header_logos()
