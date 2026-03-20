from PySide6.QtCore import QObject

class CameraService(QObject):
    def __init__(self):
        super().__init__()
    
    def start_stream(self):
        pass
