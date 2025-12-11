import sys
import unittest.mock

# Этот код должен выполняться самым первым
def setup_mocks():
    if sys.platform != 'win32':
        # Мокаем servicemanager, чтобы src.tools мог импортироваться
        sys.modules['servicemanager'] = unittest.mock.MagicMock()
        sys.modules['win32event'] = unittest.mock.MagicMock()
        sys.modules['win32service'] = unittest.mock.MagicMock()
        sys.modules['win32serviceutil'] = unittest.mock.MagicMock()


