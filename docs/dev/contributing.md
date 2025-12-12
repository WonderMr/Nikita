# Руководство контрибьютора

Руководство по участию в разработке проекта Nikita.

---

## Содержание

- [Начало работы](#начало-работы)
- [Настройка окружения разработки](#настройка-окружения-разработки)
- [Процесс разработки](#процесс-разработки)
- [Запуск тестов](#запуск-тестов)
- [Создание Pull Request](#создание-pull-request)
- [Code Review](#code-review)
- [Стандарты кодирования](#стандарты-кодирования)

---

## Начало работы

Спасибо за интерес к проекту Nikita! Мы приветствуем вклад от сообщества.

### Прежде чем начать

1. Проверьте [существующие Issues](https://github.com/your-org/Nikita/issues) — возможно, кто-то уже работает над вашей идеей
2. Для больших изменений сначала создайте Issue для обсуждения
3. Прочитайте [Стиль кода](code-style.md) — мы используем специфичный стиль выравнивания

### Что можно улучшить

**Приветствуются:**
- Исправления багов
- Улучшение документации
- Оптимизация производительности
- Добавление тестов
- Улучшение логирования и обработки ошибок

**Требуют обсуждения (создайте Issue):**
- Новая функциональность
- Изменение API
- Добавление новых зависимостей
- Архитектурные изменения

---

## Настройка окружения разработки

### Требования

- Python 3.10+
- Git
- ClickHouse (опционально, для полного тестирования)
- Redis (опционально)

### Шаг 1: Fork и клонирование

```bash
# Сделайте fork на GitHub, затем:
git clone https://github.com/ваш-username/Nikita.git
cd Nikita

# Добавьте upstream remote
git remote add upstream https://github.com/your-org/Nikita.git
```

### Шаг 2: Создание виртуального окружения

**Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.lin
pip install -r tests/requirements.test.txt
```

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.win
pip install -r tests\requirements.test.txt
```

### Шаг 3: Настройка конфигурации

```bash
# Создайте .env для разработки
cp env.example .env
nano .env
```

Минимальная конфигурация для разработки:
```ini
# Тестовые базы 1С (укажите свои)
C1_SRVINFO_PATH=/path/to/test/bases

# ClickHouse (локальный)
CLICKHOUSE_ENABLED=true
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9000
CLICKHOUSE_DATABASE=zhr1c_dev

# Без Solr и Redis для простоты
SOLR_ENABLED=false
REDIS_ENABLED=false

# Веб-сервер
HTTP_LISTEN_INTERFACE=127.0.0.1
HTTP_LISTEN_PORT=8984

# Отладка включена
DEBUG_ENABLED=true
DEBUG_PARSER=true

# Один поток для удобства отладки
PARSER_THREADS=1
```

### Шаг 4: Запуск в консольном режиме

```bash
python Nikita.py console
```

Вы должны увидеть:
- Загрузку конфигурации
- Обнаружение баз 1С
- Запуск потоков парсера
- Логи в реальном времени

Для остановки: `Ctrl+C`

---

## Процесс разработки

### Создание feature branch

```bash
# Обновите main
git checkout main
git pull upstream main

# Создайте feature branch
git checkout -b feature/my-awesome-feature
```

**Именование веток:**
- `feature/` — новая функциональность
- `bugfix/` — исправление бага
- `docs/` — изменения в документации
- `refactor/` — рефакторинг без изменения функциональности

### Внесение изменений

1. **Делайте небольшие, логичные коммиты**

```bash
git add файл1.py файл2.py
git commit -m "Добавлена функция X для улучшения Y"
```

2. **Пишите понятные commit messages**

**Хорошо:**
```
Исправлена утечка памяти в State Manager

- Добавлено закрытие SQLite connection в finally
- Обновлены тесты для проверки
- Fixes #123
```

**Плохо:**
```
fix bug
```

3. **Следуйте стилю кода проекта**

См. [code-style.md](code-style.md) — особенно важно выравнивание по `=`.

**Пример правильного стиля:**
```python
variable_name                                       =   "value"
another_variable                                    =   42
very_long_variable_name_here                        =   "test"
```

### Документирование изменений

**Для новых функций добавьте docstring:**
```python
def my_new_function(param1: str, param2: int) -> bool:
    """
    Краткое описание функции.
    
    Args:
        param1: Описание первого параметра
        param2: Описание второго параметра
    
    Returns:
        True если успешно, False иначе
    
    Raises:
        ValueError: Если param1 пустая строка
    """
    pass
```

**Обновите CHANGELOG.md:**
```markdown
## [Unreleased]

### Added
- Новая функция `my_new_function()` для обработки X
```

---

## Запуск тестов

### Структура тестов

```
tests/
├── __init__.py
├── requirements.test.txt      # Зависимости для тестов
├── test_parser_regex.py       # Тесты регулярных выражений
├── test_reader.py              # Тесты модуля reader
├── test_tools.py               # Тесты вспомогательных функций
└── mock_env.py                 # Моки для тестирования
```

### Запуск всех тестов

**Linux:**
```bash
./run_tests.sh
```

**Windows:**
```powershell
.\scripts\run-tests.ps1
```

### Запуск отдельных тестов

```bash
# Активируйте venv
source venv/bin/activate  # Linux
.\venv\Scripts\activate   # Windows

# Запустите конкретный тест
python -m unittest tests.test_parser_regex

# Запустите конкретный тест-кейс
python -m unittest tests.test_parser_regex.TestParserRegex.test_event_regex

# С подробным выводом
python -m unittest tests.test_parser_regex -v
```

### Написание тестов

При добавлении новой функциональности добавьте тесты:

```python
import unittest
from src import globals as g
from src.tools import tools as t

class TestMyFeature(unittest.TestCase):
    def setUp(self):
        """Выполняется перед каждым тестом"""
        # Настройка тестового окружения
        pass
    
    def tearDown(self):
        """Выполняется после каждого теста"""
        # Очистка
        pass
    
    def test_basic_functionality(self):
        """Тест базовой функциональности"""
        result = my_function("test")
        self.assertEqual(result, "expected")
    
    def test_error_handling(self):
        """Тест обработки ошибок"""
        with self.assertRaises(ValueError):
            my_function("")

if __name__ == '__main__':
    unittest.main()
```

### Покрытие кодов тестами

```bash
# Установите coverage
pip install coverage

# Запустите с coverage
coverage run -m unittest discover tests/
coverage report
coverage html  # HTML-отчёт в htmlcov/
```

---

## Создание Pull Request

### Подготовка к PR

```bash
# Убедитесь, что код соответствует стилю
# (Визуально проверьте выравнивание)

# Запустите тесты
./run_tests.sh

# Обновите ветку от upstream
git fetch upstream
git rebase upstream/main

# Запушьте в свой fork
git push origin feature/my-awesome-feature
```

### Создание PR на GitHub

1. Откройте https://github.com/your-org/Nikita
2. Нажмите "New Pull Request"
3. Выберите свою ветку

**Заполните шаблон PR:**
```markdown
## Описание

Краткое описание изменений.

## Тип изменений

- [ ] Исправление бага
- [ ] Новая функциональность
- [ ] Breaking change (изменение API)
- [ ] Документация

## Как протестировано?

- [ ] Добавлены новые тесты
- [ ] Все существующие тесты проходят
- [ ] Протестировано вручную

## Checklist

- [ ] Код соответствует стилю проекта
- [ ] Обновлён CHANGELOG.md
- [ ] Добавлена документация (если нужно)
- [ ] Нет breaking changes (или описаны в CHANGELOG)

## Связанные Issues

Fixes #123
```

### После создания PR

- **CI/CD** автоматически запустит тесты
- **Maintainer** проведёт code review
- Внесите правки по замечаниям:

```bash
# Внесите изменения
git add .
git commit -m "Исправлены замечания из review"
git push origin feature/my-awesome-feature
```

PR автоматически обновится.

---

## Code Review

### Что проверяется

**Maintainer проверит:**
1. ✅ Соответствие стилю кода (особенно выравнивание)
2. ✅ Наличие type hints для новых функций
3. ✅ Качество docstrings
4. ✅ Обработку ошибок
5. ✅ Потокобезопасность (если работа с общими данными)
6. ✅ Тесты (покрытие новой функциональности)
7. ✅ Документацию (если изменён API)
8. ✅ Обратную совместимость

### Типичные замечания

**1. Выравнивание не соблюдено:**
```python
# ❌ Плохо
name = "Nikita"
description = "Service"

# ✅ Хорошо
name                                                =   "Nikita"
description                                         =   "Service"
```

**2. Отсутствуют type hints:**
```python
# ❌ Плохо
def parse_log(filename):
    pass

# ✅ Хорошо
def parse_log(filename: str) -> List[Dict[str, Any]]:
    pass
```

**3. Нет обработки ошибок:**
```python
# ❌ Плохо
file = open(filename)
data = file.read()

# ✅ Хорошо
try:
    with open(filename, 'r') as file:
        data = file.read()
except FileNotFoundError as e:
    t.debug_print(f"✗ Файл не найден: {filename}")
    return None
```

**4. Не потокобезопасно:**
```python
# ❌ Плохо
g.parser.ibases.append(new_base)

# ✅ Хорошо
with g.ibases_lock:
    g.parser.ibases.append(new_base)
```

### Реакция на замечания

- Воспринимайте конструктивно — это помогает улучшить код
- Задавайте вопросы, если что-то непонятно
- Благодарите за review

---

## Стандарты кодирования

### Кратко

1. **Выравнивание по `=`** — обязательно (см. [code-style.md](code-style.md))
2. **Type hints** — для всех новых функций
3. **Docstrings** — на русском языке
4. **Комментарии** — на русском языке
5. **Обработка ошибок** — всегда в `try...except`
6. **Логирование** — через `t.debug_print()`
7. **Потокобезопасность** — используйте Lock для общих данных

### Подробнее

См. полный документ [code-style.md](code-style.md).

---

## Дополнительные ресурсы

### Документация проекта

- [Архитектура](architecture.md) — понимание структуры системы
- [Внутреннее устройство](internals.md) — описание модулей
- [Стиль кода](code-style.md) — правила оформления

### Внешние ресурсы

- [Python Style Guide (PEP 8)](https://peps.python.org/pep-0008/)
- [Type Hints (PEP 484)](https://peps.python.org/pep-0484/)
- [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/)

---

## Получение помощи

**Есть вопросы?**

1. Проверьте [Issues на GitHub](https://github.com/your-org/Nikita/issues)
2. Создайте новый Issue с тегом `question`
3. Или напишите в PR — maintainer поможет

**Нашли баг?**

Создайте Issue с описанием:
- Что делали
- Что ожидали
- Что получили
- Логи (если есть)

---

## Благодарности

Спасибо за вклад в проект Nikita! Каждый Pull Request делает проект лучше.

**Лучшие контрибьюторы будут упомянуты в CHANGELOG.md**

---

**Обновлено:** 2025-12-11  
**Версия:** 2.0.0

