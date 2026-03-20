from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox
from navigation.router import router

class LoginController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view
        # Connect signals from view here
        self.view.ui.btnAccess.clicked.connect(self.login)
        self.view.ui.inputPass.returnPressed.connect(self.login)
    
    def login(self):
        username = self.view.ui.inputUser.text()
        password = self.view.ui.inputPass.text()
        
        if username == 'user' and password == '1234':
            router.go_to("main_menu")
        else:
            QMessageBox.warning(self.view, "Error de acceso", "Usuario o contraseña incorrectos.")
