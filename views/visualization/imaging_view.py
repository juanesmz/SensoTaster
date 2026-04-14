import os
from views.base_view import BaseView

class ImagingView(BaseView):
    def __init__(self):
        ui_path = os.path.join("ui", "visualization", "tabs", "imaging.ui")
        super().__init__(ui_path)
