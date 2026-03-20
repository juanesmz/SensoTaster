from PySide6.QtCore import QObject

class StorageService(QObject):
    def __init__(self):
        super().__init__()
    
    def save_experiment(self, config, data):
        pass
