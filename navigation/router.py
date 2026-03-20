from PySide6.QtCore import QObject, Signal

class Router(QObject):
    navigate = Signal(str)  # Emits the route name to navigate to

    def __init__(self):
        super().__init__()
        self._current_route = None

    def go_to(self, route_name):
        self._current_route = route_name
        self.navigate.emit(route_name)
    
    @property
    def current_route(self):
        return self._current_route

# Global router instance
router = Router()
