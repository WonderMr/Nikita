import unittest
import sys
import os
import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tests.mock_env
tests.mock_env.setup_mocks()

from src.reader import reader

class TestReader(unittest.TestCase):
    def test_trans_id(self):
        self.assertEqual(reader.trans_id('НЕТ ТРАНЗАКЦИИ'), 'N')

    def test_int_1c_time_to_obj(self):
        c1_time = 637134336000000 
        obj = reader.int_1c_time_to_obj(c1_time)
        self.assertEqual(len(obj), 6)

if __name__ == '__main__':
    unittest.main()
