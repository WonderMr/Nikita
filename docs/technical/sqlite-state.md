# SQLite State Manager

Техническая документация по системе хранения состояния парсинга в SQLite.

---

## Содержание

- [Обзор](#обзор)
- [Структура базы данных](#структура-базы-данных)
- [Составной ключ](#составной-ключ)
- [API State Manager](#api-state-manager)
- [Миграция данных](#миграция-данных)
- [Потокобезопасность](#потокобезопасность)

---

## Обзор

### Назначение

State Manager хранит информацию о:
- Каких файлах журналов уже прочитано
- Сколько байт прочитано из каждого файла
- Истории отправленных блоков данных

Это позволяет:
- Продолжить парсинг после перезапуска с того же места
- Избежать дублирования данных в хранилищах
- Отслеживать прогресс обработки каждой базы

### Файл базы данных

**Расположение:**
- **Linux:** `/opt/Nikita/Nikita.parser.state.db`
- **Windows:** `C:\Program Files\Nikita\Nikita.parser.state.db`

**Формат:** SQLite 3

---

## Структура базы данных

### Таблица `file_states`

Хранит состояние обработки каждого файла журнала.

```sql
CREATE TABLE file_states (
    database_name TEXT NOT NULL,     -- Имя базы 1С
    file_basename TEXT NOT NULL,     -- Имя файла (без пути)
    filesize INTEGER,                -- Полный размер файла (байты)
    filesizeread INTEGER,            -- Сколько уже прочитано (байты)
    PRIMARY KEY (database_name, file_basename)
);
```

**Пример данных:**
```
database_name | file_basename   | filesize  | filesizeread
--------------|-----------------|-----------|-------------
PROD_ZUP      | 20251211.lgp    | 10485760  | 5242880
PROD_ZUP      | 20251210.lgp    | 20971520  | 20971520
TEST_UT11     | 20251211.lgp    | 5242880   | 2621440
```

### Таблица `committed_blocks`

История отправленных блоков данных.

```sql
CREATE TABLE committed_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    database_name TEXT NOT NULL,
    file_basename TEXT NOT NULL,
    offset_start INTEGER,
    offset_end INTEGER,
    data_records INTEGER,
    committed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Пример данных:**
```
id | database_name | file_basename | offset_start | offset_end | data_records | committed_at
---|---------------|---------------|--------------|------------|--------------|---------------------
1  | PROD_ZUP      | 20251211.lgp  | 0            | 1048576    | 200          | 2025-12-11 14:23:45
2  | PROD_ZUP      | 20251211.lgp  | 1048576      | 2097152    | 200          | 2025-12-11 14:24:10
```

**Назначение:**
- Аудит отправленных данных
- Подсчёт общего количества записей по базе
- Отладка (можно увидеть, когда и что было отправлено)

---

## Составной ключ

### Проблема старого подхода

**До версии 2.0 (только basename):**
```sql
PRIMARY KEY (filename)
```

**Проблема:** Если в системе несколько баз 1С с файлами с одинаковыми именами:
```
/path/to/base1/20251211.lgp
/path/to/base2/20251211.lgp
```

В таблице `file_states` они **перезаписывали** друг друга, так как имели одинаковый `filename`.

### Решение: Составной ключ

**С версии 2.0:**
```sql
PRIMARY KEY (database_name, file_basename)
```

Теперь каждая комбинация `(база, файл)` уникальна:
```
database_name | file_basename
--------------|---------------
base1         | 20251211.lgp
base2         | 20251211.lgp  ← нет коллизии!
```

### Преимущества

1. ✅ **Устранены коллизии** между одноимёнными файлами из разных баз
2. ✅ **Уменьшен размер БД** — хранится basename вместо полного пути
3. ✅ **Улучшена читаемость** — в БД видно `(base1, file.lgp)` вместо `/var/log/base1/file.lgp`
4. ✅ **Корректная работа с multiple bases**

---

## API State Manager

### Инициализация

```python
from src.state_manager import StateManager

state_manager = StateManager("Nikita.parser.state.db")
```

### Получение состояния файла

```python
state = state_manager.get_file_state(
    filename="/path/to/base1/20251211.lgp",
    database_name="PROD_ZUP"
)

# Результат:
# {
#     'filename': '/path/to/base1/20251211.lgp',
#     'filesize': 10485760,
#     'filesizeread': 5242880
# }
```

**Если файл ещё не обрабатывался:**
```python
# Вернёт начальное состояние:
# {'filename': '...', 'filesize': 0, 'filesizeread': 0}
```

### Обновление состояния файла

```python
state_manager.update_file_state(
    filename="/path/to/base1/20251211.lgp",
    filesize=10485760,
    filesizeread=6291456,  # Прочитали ещё 1 MB
    database_name="PROD_ZUP"
)
```

**Логика:**
- Если запись существует → UPDATE
- Если записи нет → INSERT

### Логирование отправленного блока

```python
state_manager.log_committed_block(
    filename="/path/to/base1/20251211.lgp",
    offset_start=0,
    offset_end=1048576,
    data_records=200,
    database_name="PROD_ZUP"
)
```

**Записывается в таблицу `committed_blocks`** для истории.

### Получение общего количества отправленных записей

```python
total = state_manager.get_total_records_sent("PROD_ZUP")
# Вернёт: 15432 (сумма data_records для database_name='PROD_ZUP')
```

---

## Миграция данных

### Автоматическая миграция при обновлении

При обновлении с версии 1.x → 2.0 State Manager автоматически выполняет миграцию:

**Алгоритм:**
1. Проверяет структуру таблиц (есть ли поле `database_name`)
2. Если нет — выполняет миграцию:
   - Переименовывает старые таблицы (`_old`)
   - Создаёт новые таблицы с правильной структурой
   - Мигрирует данные:
     - Извлекает basename из полных путей
     - Для старых записей `database_name = 'unknown'`
   - Удаляет старые таблицы

**Логирование:**
```
⚠️ Обнаружена старая структура file_states, выполняется миграция...
✓ Миграция file_states завершена (обработано 42 записи)
⚠️ Обнаружена старая структура committed_blocks, выполняется миграция...
✓ Миграция committed_blocks завершена (обработано 1523 записи)
```

### Ручная миграция (если нужно)

Если автоматическая миграция не сработала:

```sql
-- 1. Создать новые таблицы
CREATE TABLE file_states_new (
    database_name TEXT NOT NULL,
    file_basename TEXT NOT NULL,
    filesize INTEGER,
    filesizeread INTEGER,
    PRIMARY KEY (database_name, file_basename)
);

-- 2. Мигрировать данные
INSERT INTO file_states_new (database_name, file_basename, filesize, filesizeread)
SELECT 
    'unknown' as database_name,
    substr(filename, instr(filename, '/') + 1) as file_basename,
    filesize,
    filesizeread
FROM file_states;

-- 3. Удалить старую таблицу
DROP TABLE file_states;

-- 4. Переименовать новую таблицу
ALTER TABLE file_states_new RENAME TO file_states;
```

---

## Потокобезопасность

### Проблема

Несколько потоков парсеров одновременно обращаются к SQLite базе данных:
- Поток 1 обрабатывает базу "PROD_ZUP"
- Поток 2 обрабатывает базу "TEST_UT11"
- Оба одновременно читают/пишут в `file_states`

### Решение

State Manager использует `threading.Lock` для всех операций с БД:

```python
class StateManager:
    def __init__(self, db_path):
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(
            db_path,
            check_same_thread=False  # Разрешить использование из разных потоков
        )
    
    def get_file_state(self, filename, database_name):
        with self.lock:  # Блокировка
            cursor = self.conn.cursor()
            cursor.execute(...)
            # ...
```

**Гарантии:**
- Только один поток одновременно работает с БД
- Нет race conditions
- Нет повреждения данных

### SQLite WAL Mode

State Manager использует режим Write-Ahead Logging:

```python
cursor.execute("PRAGMA journal_mode=WAL")
```

**Преимущества:**
- Лучшая параллельность (читатели не блокируют писателей)
- Быстрее при множественных записях
- Меньше вероятность блокировок

---

## Примеры использования

### Пример 1: Простой цикл парсинга

```python
from src.state_manager import StateManager

state_manager = StateManager("Nikita.parser.state.db")

while True:
    # Получить состояние
    state = state_manager.get_file_state(
        "/path/to/file.lgp",
        "PROD_ZUP"
    )
    
    # Проверить размер файла
    current_size = os.path.getsize("/path/to/file.lgp")
    
    if current_size > state['filesizeread']:
        # Прочитать новые данные
        new_bytes = current_size - state['filesizeread']
        data = read_file("/path/to/file.lgp", state['filesizeread'], new_bytes)
        
        # Парсинг и отправка
        records = parse(data)
        send_to_clickhouse(records)
        
        # Обновить состояние
        state_manager.update_file_state(
            "/path/to/file.lgp",
            current_size,
            current_size,  # Прочитали всё
            "PROD_ZUP"
        )
    
    time.sleep(30)
```

### Пример 2: Обработка нескольких файлов одной базы

```python
files = [
    "/path/to/base/20251209.lgp",
    "/path/to/base/20251210.lgp",
    "/path/to/base/20251211.lgp"
]

for file in files:
    state = state_manager.get_file_state(file, "PROD_ZUP")
    
    # Файл уже полностью обработан?
    if state['filesizeread'] >= state['filesize']:
        continue  # Пропустить
    
    # Обработать файл
    # ...
```

---

## Отладка

### Просмотр содержимого БД

```bash
# Открыть в sqlite3
sqlite3 Nikita.parser.state.db

# Посмотреть состояние файлов
SELECT * FROM file_states;

# Посмотреть историю
SELECT * FROM committed_blocks ORDER BY committed_at DESC LIMIT 10;

# Статистика по базам
SELECT 
    database_name,
    COUNT(*) as files,
    SUM(filesizeread) as total_read
FROM file_states
GROUP BY database_name;
```

### Проверка целостности

```sql
-- Проверить consistency
PRAGMA integrity_check;

-- Размер БД
SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();
```

---

## Оптимизация

### Vacuum (очистка)

Периодически выполняйте VACUUM для оптимизации размера БД:

```bash
sqlite3 Nikita.parser.state.db "VACUUM;"
```

### Индексы

Таблица `committed_blocks` может вырасти большой. Добавьте индекс:

```sql
CREATE INDEX idx_committed_blocks_db_file 
ON committed_blocks(database_name, file_basename);
```

---

**Обновлено:** 2025-12-11  
**Версия:** 2.0.0  
**Источник:** Перенос и обновление SQLITE_OPTIMIZATION.md

