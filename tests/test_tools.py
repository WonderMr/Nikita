import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tests.mock_env
tests.mock_env.setup_mocks()

from src.tools import tools

class TestTools(unittest.TestCase):
    def test_strtobool(self):
        self.assertTrue(tools.strtobool('y'))
        self.assertFalse(tools.strtobool('n'))

    def test_normalize_ib_name(self):
        self.assertEqual(tools.normalize_ib_name('base%name'), 'baseaAa_25name')

if __name__ == '__main__':
    unittest.main()
