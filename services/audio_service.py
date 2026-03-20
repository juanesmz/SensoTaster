from PySide6.QtCore import QObject

class AudioService(QObject):
    def __init__(self):
        super().__init__()
    
    def start_recording(self):
        pass
    
    def stop_recording(self):
        pass
