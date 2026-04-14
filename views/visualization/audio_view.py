import os
from views.base_view import BaseView

class AudioView(BaseView):
    def __init__(self):
        ui_path = os.path.join("ui", "visualization", "tabs", "audio.ui")
        super().__init__(ui_path)
