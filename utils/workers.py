from PySide6.QtCore import QThread, Signal

class BaseWorker(QThread):
    finished_task = Signal(object)
    
    def run(self):
        # Override this method
        pass
