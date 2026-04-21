from PySide6.QtCore import QObject
from labjack import ljm

class GasService(QObject):
    def __init__(self):
        super().__init__()
        self.handle = None
        self._connected = False

    def connect(self):
        """Establece conexión con la LabJack."""
        try:
            # Abrir cualquier LabJack disponible por cualquier conexión
            self.handle = ljm.openS("ANY", "ANY", "ANY")
            self._connected = True
            return True
        except Exception as e:
            print(f"Error al conectar con LabJack: {e}")
            self._connected = False
            return False

    def disconnect(self):
        """Cierra la conexión con la LabJack."""
        if self.handle is not None:
            try:
                ljm.close(self.handle)
            except:
                pass
            self.handle = None
            self._connected = False

    def is_connected(self):
        return self._connected

    def read_channels(self, channels: list[str]) -> list[float] | None:
        """
        Lee los canales analógicos especificados (ej: ['AIN0', 'AIN1', ...]).
        Retorna una lista de voltajes o None si falla.
        """
        if not self._connected or self.handle is None:
            return None
        
        try:
            # LJM eReadNames lee múltiples registros por nombre
            return ljm.eReadNames(self.handle, len(channels), channels)
        except Exception as e:
            print(f"Error al leer de LabJack: {e}")
            return None
