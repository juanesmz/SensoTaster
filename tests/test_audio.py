import unittest
from services.audio_service import AudioService

class TestAudioService(unittest.TestCase):
    def test_initialization(self):
        service = AudioService()
        self.assertIsNotNone(service)

if __name__ == '__main__':
    unittest.main()
