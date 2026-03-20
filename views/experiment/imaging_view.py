import os
from views.base_view import BaseView

class ImagingView(BaseView):
    def __init__(self):
        super().__init__(os.path.join("ui", "experiment", "pages", "imaging.ui"))
