import os
from views.base_view import BaseView

class ConfigurationView(BaseView):
    def __init__(self):
        super().__init__(os.path.join("ui", "experiment", "pages", "configuration.ui"))
