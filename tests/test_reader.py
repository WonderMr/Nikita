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
        """Проверка правильного маппинга статусов транзакций согласно документации 1С"""
        # По документации 1С: R=Rollback, U=Unfinished, C=Commit, N=No transaction
        self.assertEqual(reader.trans_id('НЕТ ТРАНЗАКЦИИ'), 'N')
        self.assertEqual(reader.trans_id('ЗАФИКСИРОВАНА'), 'C')      # Commit
        self.assertEqual(reader.trans_id('НЕ ЗАВЕРШЕНА'), 'U')       # Unfinished
        self.assertEqual(reader.trans_id('ОТМЕНЕНА'), 'R')           # Rollback
        # Проверка регистронезависимости
        self.assertEqual(reader.trans_id('зафиксирована'), 'C')
        self.assertEqual(reader.trans_id('не завершена'), 'U')
        self.assertEqual(reader.trans_id('отменена'), 'R')
        self.assertEqual(reader.trans_id('нет транзакции'), 'N')
    
    def test_trans_descr(self):
        """Проверка обратного преобразования: код транзакции → описание"""
        # Без fix - нормальное преобразование согласно документации 1С
        self.assertEqual(reader.trans_descr('R'), 'Отменена')         # Rollback
        self.assertEqual(reader.trans_descr('U'), 'Не завершена')     # Unfinished
        self.assertEqual(reader.trans_descr('C'), 'Зафиксирована')    # Commit
        self.assertEqual(reader.trans_descr('N'), 'Нет транзакции')   # No transaction
        
        # С fix=True - историческая логика для событий транзакций (C→U, R→C, U→R)
        self.assertEqual(reader.trans_descr('C', fix=True), 'Не завершена')      # C→U
        self.assertEqual(reader.trans_descr('R', fix=True), 'Зафиксирована')     # R→C
        self.assertEqual(reader.trans_descr('U', fix=True), 'Отменена')          # U→R

    def test_int_1c_time_to_obj(self):
        c1_time = 637134336000000 
        obj = reader.int_1c_time_to_obj(c1_time)
        self.assertEqual(len(obj), 6)

if __name__ == '__main__':
    unittest.main()
