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
                # ВАЖНО: Используем составной ключ (database_name + file_basename) для избежания коллизий
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS file_states (
                        database_name TEXT NOT NULL,
                        file_basename TEXT NOT NULL,
                        filesize INTEGER,
                        filesizeread INTEGER,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (database_name, file_basename)
                    )
                ''')
                
                # Таблица истории закоммиченных блоков
                # ВАЖНО: database_name - имя базы 1С, file_basename - только имя файла без пути
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS committed_blocks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        database_name TEXT,
                        file_basename TEXT,
                        offset_start INTEGER,
                        offset_end INTEGER,
                        data_hash TEXT,
                        record_count INTEGER,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Миграция старой структуры таблиц к новой (если нужно)
                # Проверяем, используется ли старая структура (filename вместо database_name + file_basename)
                try:
                    cursor.execute("SELECT database_name FROM file_states LIMIT 1")
                    # Новая структура уже существует
                except sqlite3.OperationalError:
                    # Старая структура, нужна миграция
                    t.debug_print("⚠️ Обнаружена старая структура file_states, выполняется миграция...", "StateManager")
                    cursor.execute('ALTER TABLE file_states RENAME TO file_states_old')
                    cursor.execute('''
                        CREATE TABLE file_states (
                            database_name TEXT NOT NULL,
                            file_basename TEXT NOT NULL,
                            filesize INTEGER,
                            filesizeread INTEGER,
                            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            PRIMARY KEY (database_name, file_basename)
                        )
                    ''')
                    # Миграция данных: извлекаем basename из старых записей
                    # Примечание: database_name будет пустым, т.к. в старой структуре его не было
                    cursor.execute('''
                        INSERT INTO file_states (database_name, file_basename, filesize, filesizeread, last_updated)
                        SELECT 'unknown', 
                               CASE 
                                   WHEN filename LIKE '%/%' THEN substr(filename, instr(filename, '/') + 1)
                                   WHEN filename LIKE '%\\%' THEN substr(filename, instr(filename, '\\') + 1)
                                   ELSE filename
                               END,
                               filesize, filesizeread, last_updated
                        FROM file_states_old
                    ''')
                    cursor.execute('DROP TABLE file_states_old')
                    t.debug_print("✓ Миграция file_states завершена", "StateManager")
                
                # Аналогичная проверка для committed_blocks
                try:
                    cursor.execute("SELECT database_name FROM committed_blocks LIMIT 1")
                except sqlite3.OperationalError:
                    # Старая структура с полем basename, меняем на database_name
                    t.debug_print("⚠️ Обнаружена старая структура committed_blocks, выполняется миграция...", "StateManager")
                    try:
                        # Проверяем, есть ли поле basename (промежуточная версия)
                        cursor.execute("SELECT basename FROM committed_blocks LIMIT 1")
                        has_basename = True
                    except sqlite3.OperationalError:
                        has_basename = False
                    
                    cursor.execute('ALTER TABLE committed_blocks RENAME TO committed_blocks_old')
                    cursor.execute('''
                        CREATE TABLE committed_blocks (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            database_name TEXT,
                            file_basename TEXT,
                            offset_start INTEGER,
                            offset_end INTEGER,
                            data_hash TEXT,
                            record_count INTEGER,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    if has_basename:
                        # Миграция из промежуточной версии (basename → database_name, filename → file_basename)
                        cursor.execute('''
                            INSERT INTO committed_blocks (id, database_name, file_basename, offset_start, offset_end, data_hash, record_count, timestamp)
                            SELECT id, basename,
                                   CASE 
                                       WHEN filename LIKE '%/%' THEN substr(filename, instr(filename, '/') + 1)
                                       WHEN filename LIKE '%\\%' THEN substr(filename, instr(filename, '\\') + 1)
                                       ELSE filename
                                   END,
                                   offset_start, offset_end, data_hash, record_count, timestamp
                            FROM committed_blocks_old
                        ''')
                    else:
                        # Миграция из старой версии (filename содержит полный путь)
                        cursor.execute('''
                            INSERT INTO committed_blocks (id, database_name, file_basename, offset_start, offset_end, data_hash, record_count, timestamp)
                            SELECT id, 'unknown',
                                   CASE 
                                       WHEN filename LIKE '%/%' THEN substr(filename, instr(filename, '/') + 1)
                                       WHEN filename LIKE '%\\%' THEN substr(filename, instr(filename, '\\') + 1)
                                       ELSE filename
                                   END,
                                   offset_start, offset_end, data_hash, record_count, timestamp
                            FROM committed_blocks_old
                        ''')
                    
                    cursor.execute('DROP TABLE committed_blocks_old')
                    t.debug_print("✓ Миграция committed_blocks завершена", "StateManager")
                
                # Индексы для быстрого поиска
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_states_db ON file_states(database_name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_blocks_database ON committed_blocks(database_name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_blocks_file ON committed_blocks(file_basename)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_blocks_db_file ON committed_blocks(database_name, file_basename)')
                
                conn.commit()
                conn.close()
                # t.debug_print(f"✓ StateManager: База данных успешно инициализирована", "StateManager")
        except Exception as e:
            # t.debug_print(f"✗ StateManager: Ошибка инициализации: {e}", "StateManager")
            print(f"✗ StateManager: Ошибка инициализации: {e}")
            import traceback
            print(f"✗ StateManager: Traceback:\n{traceback.format_exc()}")

    def get_file_state(self, filename: str, database_name: str = 'unknown') -> Optional[Dict[str, Any]]:
        """
        Получение состояния файла по имени
        
        Args:
            filename: Полный путь к файлу (будет преобразован в basename для хранения)
            database_name: Имя базы данных 1С (для избежания коллизий)
        
        Returns:
            Dict с filename, filesize, filesizeread или None
        """
        try:
            # Извлекаем только базовое имя файла для хранения
            file_basename                                       =   os.path.basename(filename)
            
            with self.conn_lock:
                conn                                            =   sqlite3.connect(self.db_path, check_same_thread=False)
                cursor                                          =   conn.cursor()
                cursor.execute(
                    "SELECT filesize, filesizeread FROM file_states WHERE database_name = ? AND file_basename = ?",
                    (database_name, file_basename)
                )
                row                                             =   cursor.fetchone()
                conn.close()
                
                if row:
                    return {'filename': filename, 'filesize': row[0], 'filesizeread': row[1]}
                return None
        except Exception as e:
            t.debug_print(f"Ошибка get_file_state: {e}")
            return None

    def update_file_state(self, filename: str, filesize: int, filesizeread: int, database_name: str = 'unknown') -> None:
        """
        Обновление состояния файла
        
        Args:
            filename: Полный путь к файлу (будет преобразован в basename для хранения)
            filesize: Размер файла
            filesizeread: Прочитанный размер
            database_name: Имя базы данных 1С (для избежания коллизий)
        """
        try:
            # Извлекаем только базовое имя файла для хранения
            file_basename                                       =   os.path.basename(filename)
            
            with self.conn_lock:
                conn                                            =   sqlite3.connect(self.db_path, check_same_thread=False)
                cursor                                          =   conn.cursor()
                # Используем INSERT OR REPLACE как совместимый способ
                cursor.execute('''
                    INSERT OR REPLACE INTO file_states (database_name, file_basename, filesize, filesizeread, last_updated)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (database_name, file_basename, filesize, filesizeread))
                conn.commit()
                conn.close()
        except Exception as e:
            t.debug_print(f"Ошибка update_file_state: {e}")

    def log_committed_block(self, filename: str, offset_start: int, offset_end: int, data_records: List[Any], database_name: str = 'unknown') -> None:
        """
        Логирует закоммиченный блок с его хешем.
        
        Args:
            filename: Полный путь к файлу (будет преобразован в basename для хранения)
            offset_start: Начальное смещение
            offset_end: Конечное смещение
            data_records: Массив отправленных записей
            database_name: Имя базы 1С (принимается вместо старого параметра basename)
        """
        try:
            # Извлекаем только базовое имя файла для хранения
            file_basename                                       =   os.path.basename(filename)
            
            # Если database_name не указан, пытаемся извлечь из первой записи (для обратной совместимости)
            if database_name == 'unknown' and data_records and len(data_records) > 0:
                first_record                                    =   data_records[0]
                if isinstance(first_record, dict) and 'ibase' in first_record:
                    database_name                               =   first_record['ibase']
            
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
                    INSERT INTO committed_blocks (database_name, file_basename, offset_start, offset_end, data_hash, record_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (database_name, file_basename, offset_start, offset_end, data_hash, record_count))
                conn.commit()
                conn.close()
                
                # Логируем для отладки
                t.debug_print(f"✓ Logged block: db={database_name}, file={file_basename}, records={record_count}", "StateManager")
        except Exception as e:
            t.debug_print(f"Ошибка log_committed_block: {e}", "StateManager")

    def get_total_records_sent(self, database_name: str) -> int:
        """
        Получение общего количества отправленных записей для базы
        
        Args:
            database_name: Имя базы данных 1С
        
        Returns:
            Общее количество отправленных записей
        """
        try:
            with self.conn_lock:
                conn                                            =   sqlite3.connect(self.db_path, check_same_thread=False)
                cursor                                          =   conn.cursor()
                
                # Ищем по database_name
                cursor.execute('''
                    SELECT SUM(record_count) FROM committed_blocks 
                    WHERE database_name = ?
                ''', (database_name,))
                row                                             =   cursor.fetchone()
                
                # Отладочный запрос: покажем все записи для этой базы
                cursor.execute('''
                    SELECT database_name, COUNT(*), SUM(record_count) 
                    FROM committed_blocks 
                    WHERE database_name = ?
                    GROUP BY database_name
                ''', (database_name,))
                debug_rows                                      =   cursor.fetchall()
                
                conn.close()
                
                result                                          =   int(row[0]) if row and row[0] else 0
                
                # Логируем для отладки
                if debug_rows:
                    for db_row in debug_rows:
                        t.debug_print(f"📊 DB query for '{database_name}': blocks={db_row[1]}, total_records={db_row[2]}", "StateManager")
                else:
                    t.debug_print(f"📊 DB query for '{database_name}': no records found", "StateManager")
                
                return result
        except Exception as e:
            t.debug_print(f"Ошибка get_total_records_sent: {e}", "StateManager")
            return 0

state_manager                                                   =   StateManager()
