import os
from views.base_view import BaseView

class SettingsView(BaseView):
    def __init__(self):
        ui_path = os.path.join(
            os.path.dirname(__file__), "..", "ui", "settings", "settings.ui"
        )
        super().__init__(os.path.abspath(ui_path))
        self._setup_header_logos()
