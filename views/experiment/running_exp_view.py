import os
from views.base_view import BaseView

class RunningExpView(BaseView):
    def __init__(self):
        super().__init__(os.path.join("ui", "experiment", "running_exp.ui"))
        self._setup_header_logos()
