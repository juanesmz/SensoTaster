from PySide6.QtCore import QObject

class GasService(QObject):
    def __init__(self):
        super().__init__()
    
    def read_sensor(self):
        pass
