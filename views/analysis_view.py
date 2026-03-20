import os
from views.base_view import BaseView

class AnalysisView(BaseView):
    def __init__(self):
        super().__init__(os.path.join("ui", "analysis", "analysis.ui"))
        self._setup_header_logos()
