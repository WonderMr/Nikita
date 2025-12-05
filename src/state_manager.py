# -*- coding: utf-8 -*-
import sqlite3
import threading
import json
import hashlib
import os
from typing import Optional, Dict, Any, List
from src import globals as g
from src.tools import tools as t

class StateManager:
    _instance                                                   =   None
    _lock                                                       =   threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance                               =   super(StateManager, cls).__new__(cls)
                    cls._instance._initialized                  =   False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized                                       =   True
        
        # Определяем корневой каталог проекта
        # Если self_dir установлен - используем его
        if g.execution.self_dir and g.execution.self_dir != "":
            base_dir                                            =   g.execution.self_dir
        else:
            # Мы находимся в src/state_manager.py, нужно подняться на уровень вверх
            src_dir                                             =   os.path.dirname(os.path.abspath(__file__))
            base_dir                                            =   os.path.dirname(src_dir)  # корень проекта
            
            # Дополнительная проверка: если мы всё ещё в src (странная структура), поднимемся ещё выше
            if os.path.basename(base_dir) == "src":
                 base_dir                                       =   os.path.dirname(base_dir)

        self.db_path                                            =   os.path.join(base_dir, "Nikita.parser.state.db")
        self.conn_lock                                          =   threading.Lock()
        
        # t.debug_print(f"StateManager: База данных будет создана в {self.db_path}", "StateManager")
        self._init_db()

    def _init_db(self) -> None:
        """Инициализация базы данных SQLite"""
        try:
            # t.debug_print(f"StateManager: Инициализация базы данных: {self.db_path}", "StateManager")
            with self.conn_lock:
                conn                                            =   sqlite3.connect(self.db_path, check_same_thread=False)
                cursor                                          =   conn.cursor()
                
                # Таблица состояний файлов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS file_states (
                        filename TEXT PRIMARY KEY,
                        filesize INTEGER,
                        filesizeread INTEGER,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Таблица истории закоммиченных блоков
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS committed_blocks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT,
                        basename TEXT,
                        offset_start INTEGER,
                        offset_end INTEGER,
                        data_hash TEXT,
                        record_count INTEGER,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Проверяем существование колонки basename, если нет - добавляем
                try:
                    cursor.execute("SELECT basename FROM committed_blocks LIMIT 1")
                except sqlite3.OperationalError:
                    # Колонка не существует, добавляем её
                    cursor.execute('ALTER TABLE committed_blocks ADD COLUMN basename TEXT')
                
                # Индексы для быстрого поиска
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_blocks_filename ON committed_blocks(filename)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_blocks_basename ON committed_blocks(basename)')
                
                conn.commit()
                conn.close()
                # t.debug_print(f"✓ StateManager: База данных успешно инициализирована", "StateManager")
        except Exception as e:
            # t.debug_print(f"✗ StateManager: Ошибка инициализации: {e}", "StateManager")
            print(f"✗ StateManager: Ошибка инициализации: {e}")
            import traceback
            print(f"✗ StateManager: Traceback:\n{traceback.format_exc()}")

    def get_file_state(self, filename: str) -> Optional[Dict[str, Any]]:
        """Получение состояния файла по имени"""
        try:
            with self.conn_lock:
                conn                                            =   sqlite3.connect(self.db_path, check_same_thread=False)
                cursor                                          =   conn.cursor()
                cursor.execute("SELECT filesize, filesizeread FROM file_states WHERE filename = ?", (filename,))
                row                                             =   cursor.fetchone()
                conn.close()
                
                if row:
                    return {'filename': filename, 'filesize': row[0], 'filesizeread': row[1]}
                return None
        except Exception as e:
            t.debug_print(f"Ошибка get_file_state: {e}")
            return None

    def update_file_state(self, filename: str, filesize: int, filesizeread: int) -> None:
        """Обновление состояния файла"""
        try:
            with self.conn_lock:
                conn                                            =   sqlite3.connect(self.db_path, check_same_thread=False)
                cursor                                          =   conn.cursor()
                # Используем INSERT OR REPLACE как совместимый способ
                cursor.execute('''
                    INSERT OR REPLACE INTO file_states (filename, filesize, filesizeread, last_updated)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (filename, filesize, filesizeread))
                conn.commit()
                conn.close()
        except Exception as e:
            t.debug_print(f"Ошибка update_file_state: {e}")

    def log_committed_block(self, filename: str, offset_start: int, offset_end: int, data_records: List[Any], basename: str = None) -> None:
        """
        Логирует закоммиченный блок с его хешем.
        
        Args:
            filename: Полный путь к файлу
            offset_start: Начальное смещение
            offset_end: Конечное смещение
            data_records: Массив отправленных записей
            basename: Имя базы (опционально, извлекается из первой записи если не указано)
        """
        try:
            # Вычисляем хеш отправляемых данных
            # Используем json dumps с sort_keys для стабильности
            if data_records:
                data_str                                        =   json.dumps(data_records, sort_keys=True, default=str)
                data_hash                                       =   hashlib.sha256(data_str.encode('utf-8')).hexdigest()
                record_count                                    =   len(data_records)
                
                # Извлекаем имя базы из первой записи, если не указано
                if not basename and len(data_records) > 0:
                    first_record                                =   data_records[0]
                    if isinstance(first_record, dict) and 'ibase' in first_record:
                        basename                                =   first_record['ibase']
            else:
                data_hash                                       =   "empty"
                record_count                                    =   0

            with self.conn_lock:
                conn                                            =   sqlite3.connect(self.db_path, check_same_thread=False)
                cursor                                          =   conn.cursor()
                cursor.execute('''
                    INSERT INTO committed_blocks (filename, basename, offset_start, offset_end, data_hash, record_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (filename, basename, offset_start, offset_end, data_hash, record_count))
                conn.commit()
                conn.close()
                
                # Логируем для отладки
                t.debug_print(f"✓ Logged block: basename={basename}, records={record_count}, file={os.path.basename(filename) if filename else 'None'}", "StateManager")
        except Exception as e:
            t.debug_print(f"Ошибка log_committed_block: {e}", "StateManager")

    def get_total_records_sent(self, basename: str) -> int:
        """
        Получение общего количества отправленных записей для базы
        
        Args:
            basename: Имя базы (нормализованное или денормализованное)
        
        Returns:
            Общее количество отправленных записей
        """
        try:
            with self.conn_lock:
                conn                                            =   sqlite3.connect(self.db_path, check_same_thread=False)
                cursor                                          =   conn.cursor()
                
                # Ищем по basename (если есть) или по filename (для обратной совместимости)
                cursor.execute('''
                    SELECT SUM(record_count) FROM committed_blocks 
                    WHERE basename = ? OR filename LIKE ?
                ''', (basename, f'%{basename}%'))
                row                                             =   cursor.fetchone()
                
                # Отладочный запрос: покажем все записи для этой базы
                cursor.execute('''
                    SELECT basename, COUNT(*), SUM(record_count) 
                    FROM committed_blocks 
                    WHERE basename = ? OR filename LIKE ?
                    GROUP BY basename
                ''', (basename, f'%{basename}%'))
                debug_rows                                      =   cursor.fetchall()
                
                conn.close()
                
                result                                          =   int(row[0]) if row and row[0] else 0
                
                # Логируем для отладки
                if debug_rows:
                    for db_row in debug_rows:
                        t.debug_print(f"📊 DB query for '{basename}': found basename='{db_row[0]}', blocks={db_row[1]}, total_records={db_row[2]}", "StateManager")
                else:
                    t.debug_print(f"📊 DB query for '{basename}': no records found", "StateManager")
                
                return result
        except Exception as e:
            t.debug_print(f"Ошибка get_total_records_sent: {e}", "StateManager")
            return 0

state_manager                                                   =   StateManager()
