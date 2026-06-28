import unittest
import sys
import os
import datetime
import tempfile

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

    def test_read_lgp_data_r12_keeps_outer_braces(self):
        """R12 (данные) должен возвращаться сырым значением 1С вместе с внешними {}.
        Регэксп sel_re (группа 13) срезает обрамляющие скобки, а ЗначениеИзСтрокиВнутр
        в обработке epf/Nikita требует полное значение вида {"S","..."}."""
        # Запись собрана строго по sel_re (см. tests/test_parser_regex.py).
        record = (
            ",\r\n{20231201120000,N,\r\n"
            "{0,0},1,2,3,4,5,I,\"Test Comment\",1,\r\n"
            "{\"S\",\"Data\"},\"Presentation\",6,7,8,9,1,\r\n"
            "{0}\r\n}"
        )
        raw = record.encode("utf-8")
        tmp_name = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".lgp") as tmp:
                tmp.write(raw)
                tmp_name = tmp.name
            rec = {"file_name": tmp_name, "pos": 0, "len": len(raw)}
            data = reader.read_lgp_data(rec, "TESTBASE")
            self.assertIsNotNone(data, "read_lgp_data вернул None — запись не распозналась")
            self.assertEqual(
                data[12], '{"S","Data"}',
                "R12 должен сохранять внешние фигурные скобки сырого значения 1С",
            )
        finally:
            if tmp_name and os.path.exists(tmp_name):
                os.remove(tmp_name)

    def test_decode_1c_data_scalar_passthrough(self):
        """Скаляры отдаются сырыми — их 1С десериализует сама."""
        self.assertEqual(reader.decode_1c_data('{"S","abc"}'), '{"S","abc"}')
        self.assertEqual(reader.decode_1c_data('{"U"}'), '{"U"}')
        self.assertEqual(reader.decode_1c_data('{"R",1:abc}'), '{"R",1:abc}')

    def test_decode_1c_data_p_flatten(self):
        """{"P",{...}} 1С не понимает → сворачиваем в Python в строковое значение {"S","..."}."""
        raw = (
            '{"P",\n{\n'
            '{"S","C:\\Program Files\\Nikita\\Nikita.epf"},\n'
            '{"S",""},\n{"B",0},\n{"S",""},\n{"B",1},\n{"S",""}\n}\n}'
        )
        self.assertEqual(
            reader.decode_1c_data(raw),
            '{"S","C:\\Program Files\\Nikita\\Nikita.epf; Нет; Да"}',
        )

    def test_decode_1c_data_p_escapes_quotes(self):
        """Кавычки внутри развёрнутого значения экранируются удвоением для ЗначениеИзСтрокиВнутр."""
        # внутреннее a"b (кавычка удвоена) → разворачиваем в a"b → кодируем обратно в a""b
        raw = '{"P",{{"S","a""b"}}}'
        self.assertEqual(reader.decode_1c_data(raw), '{"S","a""b"}')

    def test_read_lgp_data_r12_p_flatten(self):
        """LGP-путь: R12 со структурой {"P",{...}} приходит свёрнутым в {"S","..."}."""
        record = (
            ",\r\n{20231201120000,N,\r\n"
            "{0,0},1,2,3,4,5,I,\"c\",1,\r\n"
            "{\"P\",\r\n{\r\n{\"S\",\"C:\\path\"},\r\n{\"B\",0}\r\n}\r\n},\"Presentation\",6,7,8,9,1,\r\n"
            "{0}\r\n}"
        )
        raw = record.encode("utf-8")
        tmp_name = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".lgp") as tmp:
                tmp.write(raw)
                tmp_name = tmp.name
            data = reader.read_lgp_data({"file_name": tmp_name, "pos": 0, "len": len(raw)}, "TESTBASE")
            self.assertIsNotNone(data, "read_lgp_data вернул None — запись не распозналась")
            self.assertEqual(data[12], '{"S","C:\\path; Нет"}')
        finally:
            if tmp_name and os.path.exists(tmp_name):
                os.remove(tmp_name)

if __name__ == '__main__':
    unittest.main()
