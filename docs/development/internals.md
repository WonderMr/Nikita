# Внутреннее устройство модулей Nikita

Подробное описание внутреннего устройства основных модулей проекта.

---

## Содержание

- [Обзор модулей](#обзор-модулей)
- [Nikita.py - Entry Point](#nikitapy---entry-point)
- [src/globals.py - Глобальное состояние](#srcglobalspy---глобальное-состояние)
- [src/reader.py - Чтение файлов](#srcreaderpy---чтение-файлов)
- [src/parser.py - Парсинг журналов](#srcparserpy---парсинг-журналов)
- [src/state_manager.py - Хранение состояния](#srcstate_managerpy---хранение-состояния)
- [src/sender.py - Отправка данных](#srcsenderpy---отправка-данных)
- [src/cherry.py - Web Server](#srccherrypy---web-server)
- [src/tools.py - Вспомогательные функции](#srctoolspy---вспомогательные-функции)

---

## Обзор модулей

### Иерархия вызовов

```
Nikita.py (Entry Point)
├── globals.py (Инициализация конфигурации)
├── parser.py (Создание потоков парсеров)
│   ├── reader.py (Чтение файлов)
│   ├── state_manager.py (Состояние)
│   └── sender.py (Отправка данных)
├── cherry.py (Web Server)
└── tools.py (Используется везде)
```

---

## Nikita.py - Entry Point

### Назначение

Точка входа приложения, управление жизненным циклом службы.

### Основные функции

#### `start_all()`

Запуск всех компонентов системы.

```python
def start_all():
    """
    1. Инициализация g.stats.start_time
    2. Запуск HTTP-сервера (cherry)
    3. Обнаружение баз 1С
    4. Создание потоков парсеров
    5. Запуск всех потоков
    """
    from datetime import datetime
    g.stats.start_time = datetime.now()
    
    # Запуск HTTP-сервера
    cherry_thread = threading.Thread(target=c.start_http_server)
    cherry_thread.start()
    
    # Обнаружение баз 1С и создание потоков
    # ...
```

#### `stop_all()`

Остановка всех компонентов.

```python
def stop_all():
    """
    1. Установка флагов остановки
    2. Ожидание завершения потоков
    3. Закрытие подключений
    """
    for thread in parser_threads:
        thread.stop_flag = True
    
    for thread in parser_threads:
        thread.join(timeout=30)
```

### Режимы запуска

#### Console Mode

```python
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'console':
        start_all()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop_all()
```

#### Windows Service

```python
class nikita_service(win32serviceutil.ServiceFramework):
    def SvcDoRun(self):
        start_all()
        while not self.Stop:
            time.sleep(g.waits.in_cycle_we_trust)
    
    def SvcStop(self):
        stop_all()
```

---

## src/globals.py - Глобальное состояние

### Назначение

Централизованное хранение конфигурации и состояния.

### Основные объекты

#### `g.conf` - Конфигурация

```python
class Config:
    # Читает .env и предоставляет доступ к параметрам
    clickhouse_host = os.getenv('CLICKHOUSE_HOST', 'localhost')
    clickhouse_port = int(os.getenv('CLICKHOUSE_PORT', 9000))
    # ...
```

**Использование:**
```python
from src import globals as g

host = g.conf.clickhouse_host
port = g.conf.clickhouse_port
```

#### `g.stats` - Статистика в реальном времени

```python
class Stats:
    start_time = None
    
    # ClickHouse
    clickhouse_total_sent = 0
    clickhouse_total_errors = 0
    clickhouse_last_success_time = None
    # ...
```

**Обновление:**
```python
g.stats.clickhouse_total_sent += 200
g.stats.clickhouse_last_success_time = datetime.now()
```

#### `g.parser` - Состояние парсера

```python
class ParserState:
    ibases = []  # Список обнаруженных баз 1С
    threads = []  # Список потоков парсеров
```

#### `g.ibases_lock` - Блокировка для потокобезопасности

```python
ibases_lock = threading.Lock()

# Использование
with g.ibases_lock:
    bases = g.parser.ibases.copy()
```

#### `g.rexp` - Регулярные выражения

```python
class RegexPatterns:
    # Скомпилированные регулярки для парсинга
    event_re = re.compile(r'...')
    trans_status_re = re.compile(r'...')
```

---

## src/reader.py - Чтение файлов

### Назначение

Чтение данных из журналов 1С (форматы `.lgf` и `.lgd`).

### Основные функции

#### `reader.read_lgp(filename, offset, limit)`

Чтение текстового журнала `.lgf`.

```python
def read_lgp(filename: str, offset: int, limit: int) -> str:
    """
    Читает данные из текстового журнала.
    
    Args:
        filename: Путь к файлу
        offset: Смещение (байты)
        limit: Количество байт для чтения
    
    Returns:
        Прочитанные данные (строка)
    """
    with open(filename, 'r', encoding='utf-8') as f:
        f.seek(offset)
        return f.read(limit)
```

**Особенности:**
- Построчное чтение
- Обработка переносов строк
- Handling кодировок (UTF-8, UTF-16)

#### `reader.read_lgd(filename, offset_ids)`

Чтение SQLite журнала `.lgd`.

```python
def read_lgd(filename: str, offset_ids: List[int]) -> List[Dict]:
    """
    Читает события из SQLite журнала по ID.
    
    Args:
        filename: Путь к .lgd файлу
        offset_ids: Список ID событий для чтения
    
    Returns:
        Список событий (словарей)
    """
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()
    
    # Параметризованный запрос
    placeholders = ','.join('?' * len(offset_ids))
    query = f"SELECT * FROM EventLog WHERE rowid IN ({placeholders})"
    cursor.execute(query, offset_ids)
    
    # ...
```

**Особенности:**
- SQL-запросы с параметрами (защита от SQL Injection)
- Маппинг полей SQLite → внутренний формат
- Обработка BLOB данных

#### `reader.trans_id(descr)`

Маппинг статусов транзакций.

```python
def trans_id(descr: str) -> str:
    """
    Преобразует описание статуса в код.
    
    'ЗАФИКСИРОВАНА' -> 'C' (Commit)
    'НЕ ЗАВЕРШЕНА' -> 'U' (Unfinished)
    'ОТМЕНЕНА' -> 'R' (Rollback)
    'НЕТ ТРАНЗАКЦИИ' -> 'N' (No transaction)
    """
    if descr == 'ЗАФИКСИРОВАНА': return 'C'
    if descr == 'НЕ ЗАВЕРШЕНА': return 'U'
    if descr == 'ОТМЕНЕНА': return 'R'
    return 'N'
```

---

## src/parser.py - Парсинг журналов

### Назначение

Основной модуль парсинга и координации потоков.

### Класс `lgp_parser_thread`

Поток парсера для одной базы 1С.

#### Инициализация

```python
class lgp_parser_thread(threading.Thread):
    def __init__(self, pf_base, pf_name, pf_format):
        """
        Args:
            pf_base: Имя базы 1С
            pf_name: Путь к каталогу журнала
            pf_format: Формат ('lgf' или 'lgd')
        """
        self.pf_base = pf_base
        self.pf_name = pf_name
        self.pf_format = pf_format
        self.stop_flag = False
```

#### Основной цикл `run()`

```python
def run(self):
    """
    Основной цикл парсера:
    
    1. Получить состояние файла из State Manager
    2. Проверить размер файла
    3. Если изменился - прочитать новые данные
    4. Распарсить события регулярными выражениями
    5. Сформировать батч (200 записей)
    6. Отправить через post_query()
    7. Обновить состояние
    8. Ждать N секунд
    9. Повторить
    """
    while not self.stop_flag:
        try:
            # Получить состояние
            state = state_manager.get_file_state(
                self.pf_name, 
                self.pf_base
            )
            
            # Проверить размер
            current_size = os.path.getsize(file_path)
            if current_size > state['filesizeread']:
                # Читать новые данные
                # Парсить
                # Отправить
                pass
            
            time.sleep(wait_time)
        except Exception as e:
            t.debug_print(f"✗ Ошибка в потоке парсера: {e}")
```

#### Метод `post_query(batch)`

Отправка батча в хранилища.

```python
def post_query(self, batch: List[Dict]):
    """
    Отправляет батч событий в ClickHouse, Solr, Redis.
    
    Логика:
    1. Если ClickHouse включен -> отправить в ClickHouse
    2. Если Solr включен -> отправить в Solr
    3. Если Redis включен -> добавить в очередь
    4. Обновить статистику
    """
    if g.conf.clickhouse_enabled:
        self.send_to_clickhouse(batch)
    
    if g.conf.solr_enabled:
        self.send_to_solr(batch)
    
    if g.conf.redis_enabled:
        self.send_to_redis(batch)
```

#### Метод `send_to_clickhouse(batch)`

```python
def send_to_clickhouse(self, batch: List[Dict]):
    """
    Отправка в ClickHouse с логированием.
    
    1. Проверка подключения
    2. Автосоздание таблицы (если нужно)
    3. Формирование INSERT запроса
    4. Выполнение запроса с таймером
    5. Обновление статистики
    6. Детальное логирование
    """
    start_time = time.time()
    
    try:
        # Формирование запроса
        query = f"INSERT INTO {table_name} VALUES"
        self.chclient.execute(query, batch)
        
        # Измерение времени
        elapsed = time.time() - start_time
        speed = len(batch) / elapsed
        
        # Логирование
        t.debug_print(f"✓ CLICKHOUSE: Успешно отправлено {len(batch)} записей")
        t.debug_print(f"✓ CLICKHOUSE: Время выполнения: {elapsed:.3f} сек ({speed:.1f} записей/сек)")
        
        # Статистика
        g.stats.clickhouse_total_sent += len(batch)
        g.stats.clickhouse_last_success_time = datetime.now()
        
    except Exception as e:
        t.debug_print(f"✗ CLICKHOUSE: Ошибка отправки: {str(e)}")
        g.stats.clickhouse_total_errors += 1
```

---

## src/state_manager.py - Хранение состояния

### Назначение

Хранение информации о прочитанных файлах в SQLite.

### Основные методы

#### `get_file_state(filename, database_name)`

```python
def get_file_state(self, filename: str, database_name: str = 'unknown') -> Dict:
    """
    Получить состояние файла из БД.
    
    Returns:
        {
            'filename': 'path/to/file.lgp',
            'filesize': 1000000,
            'filesizeread': 500000
        }
    """
    basename = os.path.basename(filename)
    
    with self.lock:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT filesize, filesizeread FROM file_states "
            "WHERE database_name = ? AND file_basename = ?",
            (database_name, basename)
        )
        # ...
```

#### `update_file_state(filename, filesize, filesizeread, database_name)`

```python
def update_file_state(
    self,
    filename: str,
    filesize: int,
    filesizeread: int,
    database_name: str = 'unknown'
):
    """
    Обновить состояние файла (INSERT или UPDATE).
    """
    basename = os.path.basename(filename)
    
    with self.lock:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO file_states "
            "(database_name, file_basename, filesize, filesizeread) "
            "VALUES (?, ?, ?, ?)",
            (database_name, basename, filesize, filesizeread)
        )
        self.conn.commit()
```

### Потокобезопасность

Все операции с БД обёрнуты в `threading.Lock`:

```python
class StateManager:
    def __init__(self, db_path):
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
    
    def any_operation(self):
        with self.lock:
            # Операции с БД
            pass
```

---

## src/sender.py - Отправка данных

### Назначение

Функции для отправки данных в различные хранилища.

### Основные функции

#### `send_to_clickhouse(client, table, batch)`

```python
def send_to_clickhouse(
    client: Client,
    table: str,
    batch: List[Dict]
) -> bool:
    """
    Отправка батча в ClickHouse.
    
    Args:
        client: Подключение ClickHouse
        table: Имя таблицы
        batch: Список событий
    
    Returns:
        True если успешно, False при ошибке
    """
    try:
        query = f"INSERT INTO {table} VALUES"
        client.execute(query, batch)
        return True
    except Exception as e:
        t.debug_print(f"✗ CLICKHOUSE: {str(e)}")
        return False
```

---

## src/cherry.py - Web Server

### Назначение

HTTP-сервер на базе CherryPy для мониторинга.

### Основные endpoints

#### `GET /` - Веб-панель

```python
class WebInterface:
    @cherrypy.expose
    def index(self):
        """
        Генерирует HTML веб-панели.
        
        1. Читает g.stats
        2. Формирует HTML с таблицами
        3. Возвращает браузеру
        """
        html = f"""
        <html>
        <head>
            <title>Nikita Monitoring</title>
            <style>...</style>
        </head>
        <body>
            <h1>Nikita / Nikita</h1>
            <p>Uptime: {uptime}</p>
            <!-- Таблицы статистики -->
        </body>
        </html>
        """
        return html
```

#### `GET /stats_api` - JSON API

```python
@cherrypy.expose
@cherrypy.tools.json_out()
def stats_api(self):
    """
    Возвращает статистику в формате JSON.
    
    Returns:
        {
            "uptime_seconds": 3600,
            "clickhouse": {...},
            "databases": [...]
        }
    """
    uptime = (datetime.now() - g.stats.start_time).total_seconds()
    
    return {
        "uptime_seconds": uptime,
        "clickhouse": {
            "enabled": g.conf.clickhouse_enabled,
            "total_sent": g.stats.clickhouse_total_sent,
            # ...
        },
        "databases": self._get_databases_info()
    }
```

---

## src/tools.py - Вспомогательные функции

### Назначение

Общие вспомогательные функции.

### Основные функции

#### `debug_print(message)`

Потокобезопасное логирование.

```python
log_lock = threading.Lock()

def debug_print(message: str):
    """
    Записывает сообщение в лог-файл и stdout.
    
    Формат: YYYY-MM-DD HH:MM:SS.ffffff:::module:::message
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    log_message = f"{timestamp}:::module:::{message}\n"
    
    with log_lock:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_message)
        print(log_message, end='')
```

#### `sqlite3_exec(db_path, query, params=None)`

Безопасное выполнение SQL-запросов.

```python
def sqlite3_exec(
    db_path: str,
    query: str,
    params: Optional[Tuple] = None
) -> List[Tuple]:
    """
    Выполняет SQL-запрос с параметрами.
    
    Args:
        db_path: Путь к БД SQLite
        query: SQL-запрос
        params: Параметры запроса (для защиты от SQL Injection)
    
    Returns:
        Результаты запроса
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        conn.commit()
        return results
    finally:
        if conn:
            conn.close()
```

---

## Взаимодействие модулей

### Пример: Полный цикл обработки события

```
1. Nikita.py запускает lgp_parser_thread
   ↓
2. lgp_parser_thread.run() получает состояние из StateManager
   ↓
3. reader.read_lgp() читает новые данные из файла
   ↓
4. parser парсит данные регулярными выражениями (g.rexp)
   ↓
5. parser.post_query() отправляет батч
   ↓
6. sender.send_to_clickhouse() вставляет в ClickHouse
   ↓
7. parser обновляет g.stats
   ↓
8. StateManager.update_file_state() сохраняет прогресс
   ↓
9. cherry.py отображает статистику на веб-панели
```

---

**Обновлено:** 2025-12-11  
**Версия:** 2.0.0

