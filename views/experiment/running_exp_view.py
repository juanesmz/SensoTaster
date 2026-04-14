import os
from views.base_view import BaseView

class RunningExpView(BaseView):
    def __init__(self):
        super().__init__(os.path.join("ui", "experiment", "running_exp.ui"))
        # NO llamamos a _setup_header_logos() para mantener la página en blanco sin header
