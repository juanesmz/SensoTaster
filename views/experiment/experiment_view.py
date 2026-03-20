import os
from views.base_view import BaseView

class ExperimentView(BaseView):
    def __init__(self):
        super().__init__(os.path.join("ui", "experiment", "experiment.ui"))
        self._setup_header_logos()
        # Here we would access self.ui.sidebarMenu and self.ui.contentStack
