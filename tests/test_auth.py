import unittest
from services.auth_service import AuthService

class TestAuthService(unittest.TestCase):
    def test_login(self):
        service = AuthService()
        result = service.login("user", "pass")
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
