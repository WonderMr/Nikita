# Стиль кода проекта Nikita

Правила оформления кода для проекта Nikita.

---

## Содержание

- [Основные принципы](#основные-принципы)
- [Выравнивание по знаку равенства](#выравнивание-по-знаку-равенства)
- [Именование](#именование)
- [Type Hints](#type-hints)
- [Docstrings](#docstrings)
- [Комментарии](#комментарии)
- [Обработка ошибок](#обработка-ошибок)
- [Импорты](#импорты)

---

## Основные принципы

### 1. Минимализм и Прагматизм

**Правило:** Не создавайте лишних сущностей.

**Хорошо:**
```python
# Используем существующие библиотеки
import os.path
```

**Плохо:**
```python
# Добавляем новую зависимость без необходимости
from pathlib import Path
```

### 2. Читаемость важнее краткости

**Правило:** Код должен быть понятен джуну.

**Хорошо:**
```python
if file_size > previously_read_size:
    new_data_size = file_size - previously_read_size
    read_new_data(new_data_size)
```

**Плохо:**
```python
if fs > prs:
    rnd(fs - prs)
```

### 3. Явное лучше неявного

**Правило:** Не полагайтесь на неявное поведение.

**Хорошо:**
```python
def get_file_state(filename: str, database_name: str = 'unknown') -> Dict:
    pass
```

**Плохо:**
```python
def get_file_state(filename, database_name=None):
    database_name = database_name or 'unknown'  # Неявное преобразование
```

---

## Выравнивание по знаку равенства

### **КРИТИЧЕСКИ ВАЖНО: Это специфичный стиль проекта**

В проекте Nikita используется **выравнивание всех присваиваний по знаку равенства**.

### Правило

Все `=` в блоке присваиваний должны быть на одной вертикали с минимальным отступом **3 пробела** справа от самого длинного имени переменной.

### Примеры

**❌ Плохо (стандартный Python-стиль):**
```python
name = "Nikita"
description = "Service"
count = 1
very_long_variable_name = 42
```

**✅ Хорошо (стиль проекта Nikita):**
```python
name                                                =   "Nikita"
description                                         =   "Service"
count                                               =   1
very_long_variable_name                             =   42
```

### Как правильно выравнивать

1. Найдите самое длинное имя переменной в блоке
2. Добавьте минимум 3 пробела после него
3. Поставьте `=`
4. После `=` поставьте минимум 3 пробела
5. Выровняйте все остальные строки по этой позиции

**Пример выравнивания:**
```python
short                                               =   "value"
medium_length                                       =   "value"
very_very_long_variable_name                        =   "value"
another                                             =   "value"
```

### Блоки присваиваний

Выравнивание применяется к логически связанным блокам. Между блоками можно оставлять пустые строки:

```python
# Блок 1: Настройки подключения
clickhouse_host                                     =   "localhost"
clickhouse_port                                     =   9000
clickhouse_database                                 =   "zhr1c"

# Блок 2: Статистика
total_sent                                          =   0
total_errors                                        =   0
```

### Исключения

**Не выравнивайте:**

1. **Атрибуты класса с аннотациями:**
```python
class MyClass:
    name: str = "value"
    count: int = 42
```

2. **Словари:**
```python
config = {
    "host": "localhost",
    "port": 9000
}
```

3. **Присваивания внутри условий (однострочники):**
```python
if condition:
    x = 1
    return x
```

---

## Именование

### Переменные и функции

**Правило:** `snake_case` (слова через подчёркивание, строчные буквы)

```python
# Хорошо
file_name                                           =   "test.log"
total_records_sent                                  =   0

def parse_log_file(filename: str) -> List[Dict]:
    pass
```

### Классы

**Правило:** `CamelCase` или `snake_case` (если легаси)

```python
# Современный стиль (для новых классов)
class LogParser:
    pass

class StateManager:
    pass

# Легаси стиль (не менять в существующем коде)
class lgp_parser_thread:
    pass
```

### Константы

**Правило:** `UPPER_SNAKE_CASE` (заглавные буквы, слова через подчёркивание)

```python
MAX_BATCH_SIZE                                      =   200
DEFAULT_TIMEOUT                                     =   30
CLICKHOUSE_TABLE_PREFIX                             =   "zhr1c_"
```

### Приватные атрибуты

**Правило:** Префикс `_` (одно подчёркивание)

```python
class Parser:
    def __init__(self):
        self._internal_state                        =   {}
        self._connection                            =   None
```

### Избегайте сокращений

**Хорошо:**
```python
database_name                                       =   "prod"
connection_timeout                                  =   30
```

**Плохо:**
```python
db_nm                                               =   "prod"
conn_to                                             =   30
```

---

## Type Hints

### Правило

**Все новые функции должны иметь type hints.**

### Основные типы

```python
from typing import List, Dict, Optional, Any, Union, Tuple

def simple_function(name: str, count: int) -> bool:
    """Простые типы"""
    return True

def complex_function(
    data: List[Dict[str, Any]],
    config: Optional[Dict] = None
) -> Union[str, None]:
    """Сложные типы"""
    return "result" if config else None

def multiple_return(value: int) -> Tuple[bool, str]:
    """Множественный возврат"""
    return True, "success"
```

### Optional vs Union

**Используйте Optional для необязательных параметров:**
```python
def parse(filename: str, encoding: Optional[str] = None) -> Dict:
    pass
```

**Используйте Union для нескольких возможных типов:**
```python
def get_value(key: str) -> Union[str, int, None]:
    pass
```

### Аннотации переменных

```python
# Для сложных структур данных
records: List[Dict[str, Any]]                       =   []
config: Dict[str, Union[str, int]]                  =   {}
connection: Optional[Connection]                    =   None
```

### Генерики

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self, value: T):
        self.value: T = value
```

---

## Docstrings

### Правило

**Все нетривиальные функции должны иметь docstring на русском языке.**

### Формат

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Краткое описание функции (одна строка).
    
    Более подробное описание функции, если нужно.
    Может быть многострочным.
    
    Args:
        param1: Описание первого параметра
        param2: Описание второго параметра
    
    Returns:
        Описание возвращаемого значения
    
    Raises:
        ValueError: Когда param1 пустая строка
        ConnectionError: При ошибке подключения
    
    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        True
    """
    pass
```

### Примеры

**Простая функция:**
```python
def get_file_size(filename: str) -> int:
    """
    Возвращает размер файла в байтах.
    
    Args:
        filename: Путь к файлу
    
    Returns:
        Размер файла в байтах
    
    Raises:
        FileNotFoundError: Если файл не найден
    """
    return os.path.getsize(filename)
```

**Класс:**
```python
class StateManager:
    """
    Менеджер состояния парсинга.
    
    Хранит информацию о прочитанных файлах в SQLite базе данных
    для возможности продолжения парсинга после перезапуска.
    
    Attributes:
        db_path: Путь к файлу базы данных SQLite
        connection: Подключение к базе данных
    """
    
    def __init__(self, db_path: str):
        """
        Инициализация State Manager.
        
        Args:
            db_path: Путь к файлу базы данных SQLite
        """
        pass
```

---

## Комментарии

### Правило

**Комментарии на русском языке. Комментируйте "почему", а не "что".**

### Хорошие комментарии

```python
# Используем составной ключ для избежания коллизий между базами
PRIMARY KEY (database_name, file_basename)

# Ждём 5 секунд, чтобы 1С освободила файл журнала
time.sleep(5)

# ВАЖНО: Этот костыль нужен для совместимости со старыми версиями 1С
if version < "8.3.10":
    apply_workaround()
```

### Плохие комментарии

```python
# Присваиваем значение переменной
count = 0

# Вызываем функцию
result = parse_file(filename)
```

### Разделители блоков

Используйте существующий стиль разделителей:

```python
# ======================================================================================================================
# Секция 1: Инициализация
# ======================================================================================================================

code_here()

# ======================================================================================================================
# Секция 2: Обработка данных
# ======================================================================================================================

more_code()
```

### TODO комментарии

```python
# TODO: Добавить поддержку формата .lgx (см. Issue #42)
# TODO(username): Оптимизировать запрос (медленно на больших базах)
# FIXME: Костыль, нужно переписать после релиза
# HACK: Обходной путь для бага в clickhouse-driver 0.2.4
```

---

## Обработка ошибок

### Правило

**Всегда обрабатывайте ошибки. Никогда не используйте пустой `except: pass`.**

### Базовый шаблон

```python
try:
    result                                          =   risky_operation()
except SpecificError as e:
    t.debug_print(f"✗ Ошибка операции: {str(e)}")
    return None
```

### Множественные except

```python
try:
    data                                            =   parse_file(filename)
except FileNotFoundError as e:
    t.debug_print(f"✗ Файл не найден: {filename}")
    return None
except PermissionError as e:
    t.debug_print(f"✗ Нет доступа к файлу: {filename}")
    return None
except Exception as e:
    t.debug_print(f"✗ Неожиданная ошибка: {str(e)}")
    import traceback
    t.debug_print(traceback.format_exc())
    return None
```

### Finally для освобождения ресурсов

```python
connection                                          =   None
try:
    connection                                      =   connect_to_db()
    result                                          =   connection.execute(query)
except ConnectionError as e:
    t.debug_print(f"✗ Ошибка подключения: {str(e)}")
finally:
    if connection:
        connection.close()
```

### Context managers (предпочтительно)

```python
# Хорошо: автоматическое закрытие
try:
    with open(filename, 'r') as f:
        data                                        =   f.read()
except FileNotFoundError as e:
    t.debug_print(f"✗ Файл не найден: {filename}")
```

### Логирование ошибок

```python
try:
    result                                          =   operation()
except Exception as e:
    # Логирование с символом ✗
    t.debug_print(f"✗ Ошибка операции: {str(e)}")
    
    # Обновление статистики
    g.stats.clickhouse_total_errors                 +=  1
    g.stats.clickhouse_last_error_time              =   datetime.now()
    g.stats.clickhouse_last_error_msg               =   str(e)
```

---

## Импорты

### Порядок импортов

```python
# 1. Стандартная библиотека
import os
import sys
import time
from typing import List, Dict

# 2. Сторонние библиотеки
import psutil
import requests
from clickhouse_driver import Client

# 3. Локальные модули
from src import globals as g
from src import parser as p
from src.tools import tools as t
```

### Алиасы

Используйте существующие алиасы проекта:

```python
from src import globals as g
from src import parser as p
from src.reader import reader as r
from src.tools import tools as t
from src import cherry as c
```

### Избегайте `import *`

**Плохо:**
```python
from src.globals import *
```

**Хорошо:**
```python
from src import globals as g
```

---

## Дополнительные правила

### Длина строки

**Рекомендуется:** максимум 120 символов

**Исключение:** Строки с выравниванием по `=` могут быть длиннее.

### Пробелы

```python
# Вокруг операторов
a = b + c

# После запятых
func(a, b, c)

# НЕ внутри скобок
func(a, b)  # ✓
func( a, b )  # ✗
```

### Пустые строки

```python
# Одна пустая строка между методами класса
class MyClass:
    def method1(self):
        pass
    
    def method2(self):
        pass

# Две пустые строки между классами/функциями верхнего уровня
def function1():
    pass


def function2():
    pass
```

---

## Проверка стиля

### Визуальная проверка

Откройте файл в редакторе и визуально проверьте:
- ✅ Все `=` на одной вертикали в блоках присваиваний
- ✅ Type hints для новых функций
- ✅ Docstrings на русском языке
- ✅ Обработка ошибок везде

### Автоматизация (будущее)

Планируется добавить:
- Pre-commit hook для проверки выравнивания
- Линтер с custom правилами

---

## Заключение

**Помните:**
1. **Выравнивание по `=`** — обязательно
2. **Type hints** — для новых функций
3. **Docstrings** — на русском
4. **Обработка ошибок** — всегда
5. **Читаемость** — превыше всего

Если сомневаетесь — смотрите на существующий код проекта.

---

**Обновлено:** 2025-12-11  
**Версия:** 2.0.0

