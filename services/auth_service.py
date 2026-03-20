from PySide6.QtCore import QObject

class AuthService(QObject):
    def __init__(self):
        super().__init__()
    
    def login(self, username, password):
        return True
