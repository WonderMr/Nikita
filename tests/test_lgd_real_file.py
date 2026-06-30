# -*- coding: utf-8 -*-
"""
Интеграционный регресс-тест на РЕАЛЬНОМ журнале test_data/1cv8.lgd.

Гонит настоящий parser.parse_lgd_file поверх реального LGD-файла (заглушки только
на персистентность — Solr/SQLite-состояние) и проверяет, что каждая запись
доходит до коммита без KeyError и без вызова graceful_shutdown.

Регресс для бага "Exception while add_to_json 1" -> graceful_shutdown(111):
parse_lgd_file отдавал в add_to_json_data сырые int-коды из SQLite, а словари ЖР
ключуются строками -> KeyError(1) -> str(e)=="1" -> вся служба падала на старте.
Исправлено приведением кодов к str() (коммит 8b8ccd2). Этот тест ловит повтор.

По умолчанию обрабатывает первые NIKITA_LGD_TEST_LIMIT строк (20000, ~0.6 c).
NIKITA_LGD_TEST_LIMIT=0 -> весь файл (179580 строк, ~5 c).
"""
import os
import sys
import threading
import unittest
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tests.mock_env
tests.mock_env.setup_mocks()

from src import parser as P
from src import globals as g
from src.tools import tools as t
from src.dictionaries import dictionary as d
from src import sender as snd

LGD_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'test_data', '1cv8.lgd'))
BASE = 'UU'
ROW_LIMIT = int(os.getenv('NIKITA_LGD_TEST_LIMIT', '20000'))    # 0 -> весь файл
TOTAL_ROWS = 179580                                            # всего записей в фикстуре


def _make_parser_instance():
    """parser без запуска потоков/ClickHouse: только база Thread + нужные поля.
    parser наследует threading.Thread, поэтому .name — property и требует Thread.__init__."""
    inst = P.parser.__new__(P.parser)
    threading.Thread.__init__(inst)
    inst.name = 'lgd parser (test)'
    inst.json_data = {inst.name: []}
    inst.stopMe = False
    inst.chclient = None
    return inst


@unittest.skipUnless(os.path.exists(LGD_PATH), f"нет фикстуры {LGD_PATH}")
class TestParseRealLgd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        g.debug.on = False                                     # не писать в лог-файл
        d.read_new_ib_dictionary(BASE, LGD_PATH)               # реальные словари из того же .lgd
        cls.collected = []
        inst = _make_parser_instance()

        def fake_commit(pf_name, pf_base, file_state, batch_start_offset, records_to_log):
            # Solr и SQLite-состояние в тесте не нужны: фиксируем, что запись дошла до commit
            cls.collected.extend(records_to_log)
            del inst.json_data[inst.name][:]
            return True
        inst.commit_json_data = fake_commit

        real_count = P.t.get_lgd_evens_count                   # оригинал до патча
        def capped_count(path):
            max_row, min_row = real_count(path)
            if ROW_LIMIT and (max_row - min_row + 1) > ROW_LIMIT:
                max_row = min_row + ROW_LIMIT - 1
            return (max_row, min_row)

        with patch.object(t, 'graceful_shutdown') as gs, \
             patch.object(P.state_manager, 'get_file_state', return_value=None), \
             patch.object(P.t, 'get_lgd_evens_count', side_effect=capped_count):
            inst.parse_lgd_file(LGD_PATH, BASE)
            cls.gs_called = gs.called
            cls.gs_calls = list(gs.call_args_list)

    def test_parses_without_graceful_shutdown(self):
        """Все записи разбираются без KeyError -> add_to_json_data не зовёт graceful_shutdown."""
        self.assertFalse(
            self.gs_called,
            f"add_to_json_data упал и вызвал graceful_shutdown{self.gs_calls} — "
            f"повтор бага разбора LGD (int-коды vs строковые ключи словарей)"
        )

    def test_all_rows_reached_commit(self):
        """Парсер реально разобрал ожидаемое число записей (не «тихо» пропустил всё)."""
        expected = ROW_LIMIT if ROW_LIMIT else TOTAL_ROWS
        self.assertEqual(len(self.collected), expected)

    def test_records_project_to_valid_solr_docs(self):
        """Разобранные записи проецируются в Solr-документы с обязательным id (uniqueKey)
        и содержат ключевые поля LGD."""
        self.assertTrue(self.collected)
        for rec in self.collected[:200]:
            doc = snd.project_solr_doc(rec)
            self.assertTrue(doc.get('id'), "у Solr-документа нет id (uniqueKey схемы)")
            for field in ('date', 't_status', 'event_id', 'user_id'):
                self.assertIn(field, rec)


if __name__ == '__main__':
    unittest.main()
