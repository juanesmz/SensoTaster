from PySide6.QtCore import QObject

class ImagingController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view
