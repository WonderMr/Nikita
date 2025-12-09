import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tests.mock_env
tests.mock_env.setup_mocks()

class TestImports(unittest.TestCase):
    def test_import_all_modules(self):
        """Проверка импорта всех модулей проекта"""
        try:
            from src import globals
            from src import parser
            from src import reader
            from src import tools
            from src import sender
            # cherry может требовать cherrypy, который есть в requirements.test.txt
            from src import cherry
        except ImportError as e:
            self.fail(f"Ошибка импорта модулей: {e}")

if __name__ == '__main__':
    unittest.main()
