import unittest
import sys
import os
import re

# 1. Настройка окружения ДО импортов проекта
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tests.mock_env
tests.mock_env.setup_mocks()

# 2. Теперь можно импортировать модули проекта
from src import globals as g

class TestParserRegex(unittest.TestCase):
    def setUp(self):
        self.regex                                          =   g.rexp.my_parse_re

    def test_parse_valid_log_entry(self):
        """
        Тестирует парсинг валидной записи лога 1С старого формата (LGP).
        Строка составлена строго по регулярке sel_re из globals.py.
        """
        # Структура регулярки сложная, соберем строку по частям:
        # 1. Начало: {Date,Status,
        part1                                               =   ",\r\n{20231201120000,N,\r\n"
        
        # 2. Транзакция: {TransDate,TransID},User,Comp,App,Conn,Event,Sever,"Comment",
        part2                                               =   "{0,0},1,2,3,4,5,I,\"Test Comment\",1,\r\n"
        
        # 3. Данные: {"S","Data"},"Pres",Server,MainPort,AddPort,Session,
        # Важно: регулярка ожидает специфичное окончание для Data
        part3                                               =   "{\"S\",\"Data\"},\"Presentation\",6,7,8,9,1,\r\n"
        
        # 4. Разделители данных (ExtData): {Uuid, "Name", ID}
        part4                                               =   "{0}\r\n"
        
        # 5. Конец
        part5                                               =   "}"
        
        log_entry                                           =   part1 + part2 + part3 + part4 + part5
        
        # Проверяем поиск
        matches                                             =   self.regex.findall(log_entry)
        
        self.assertTrue(len(matches) > 0, "Регулярное выражение не нашло валидную запись лога")
        
        # Проверяем захват групп (первая группа - полная строка, остальные - части)
        # matches[0] это кортеж. 
        # matches[0][0] - полная строка
        # matches[0][1] - Дата (20231201120000)
        # matches[0][2] - Статус (N)
        
        first_match                                         =   matches[0]
        self.assertEqual(first_match[1], "20231201120000", "Ошибка парсинга даты")
        self.assertEqual(first_match[2], "N", "Ошибка парсинга статуса")
        self.assertEqual(first_match[11], "Test Comment", "Ошибка парсинга комментария")

    def test_file_extensions(self):
        self.assertTrue(g.rexp.is_lgP_file_re.search("log.lgp"))
        self.assertTrue(g.rexp.is_lgD_file_re.search("log.lgd"))
        self.assertFalse(g.rexp.is_lgP_file_re.search("log.txt"))

if __name__ == '__main__':
    unittest.main()
