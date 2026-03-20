import os
from views.base_view import BaseView

class MainMenuView(BaseView):
    def __init__(self):
        super().__init__(os.path.join("ui", "main_menu", "main_menu.ui"))
        self._setup_header_logos()
