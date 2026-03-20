from PySide6.QtCore import QObject, Signal

class GlobalSignals(QObject):
    experiment_started = Signal()
    experiment_stopped = Signal()
    data_received = Signal(object)

signals = GlobalSignals()
