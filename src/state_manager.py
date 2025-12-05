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
        # Если self_dir установлен - используем его, иначе идём на уровень вверх от src/
        if g.execution.self_dir and g.execution.self_dir != "":
            base_dir                                            =   g.execution.self_dir
        else:
            # Мы находимся в src/state_manager.py, нужно подняться на уровень вверх
            src_dir                                             =   os.path.dirname(os.path.abspath(__file__))
            base_dir                                            =   os.path.dirname(src_dir)  # корень проекта
        
        self.db_path                                            =   os.path.join(base_dir, "Nikita.parser.state.db")
        self.conn_lock                                          =   threading.Lock()
        
        t.debug_print(f"StateManager: База данных будет создана в {self.db_path}", "StateManager")
        self._init_db()

    def _init_db(self) -> None:
        """Инициализация базы данных SQLite"""
        try:
            t.debug_print(f"StateManager: Инициализация базы данных: {self.db_path}", "StateManager")
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
                        offset_start INTEGER,
                        offset_end INTEGER,
                        data_hash TEXT,
                        record_count INTEGER,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Индекс для быстрого поиска по имени файла
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_blocks_filename ON committed_blocks(filename)')
                
                conn.commit()
                conn.close()
                t.debug_print(f"✓ StateManager: База данных успешно инициализирована", "StateManager")
        except Exception as e:
            t.debug_print(f"✗ StateManager: Ошибка инициализации: {e}", "StateManager")
            import traceback
            t.debug_print(f"✗ StateManager: Traceback:\n{traceback.format_exc()}", "StateManager")

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

    def log_committed_block(self, filename: str, offset_start: int, offset_end: int, data_records: List[Any]) -> None:
        """
        Логирует закоммиченный блок с его хешем.
        """
        try:
            # Вычисляем хеш отправляемых данных
            # Используем json dumps с sort_keys для стабильности
            if data_records:
                data_str                                        =   json.dumps(data_records, sort_keys=True, default=str)
                data_hash                                       =   hashlib.sha256(data_str.encode('utf-8')).hexdigest()
                record_count                                    =   len(data_records)
            else:
                data_hash                                       =   "empty"
                record_count                                    =   0

            with self.conn_lock:
                conn                                            =   sqlite3.connect(self.db_path, check_same_thread=False)
                cursor                                          =   conn.cursor()
                cursor.execute('''
                    INSERT INTO committed_blocks (filename, offset_start, offset_end, data_hash, record_count)
                    VALUES (?, ?, ?, ?, ?)
                ''', (filename, offset_start, offset_end, data_hash, record_count))
                conn.commit()
                conn.close()
        except Exception as e:
            t.debug_print(f"Ошибка log_committed_block: {e}")

state_manager                                                   =   StateManager()
