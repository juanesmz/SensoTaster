from PySide6.QtCore import QObject

class EmgService(QObject):
    def __init__(self):
        super().__init__()
    
    def connect_device(self):
        pass
