# Архитектура Nikita

Описание архитектуры системы парсинга и экспорта журналов регистрации 1С:Предприятие.

---

## Содержание

- [Общий обзор](#общий-обзор)
- [Архитектурная диаграмма](#архитектурная-диаграмма)
- [Компоненты системы](#компоненты-системы)
- [Поток данных](#поток-данных)
- [Многопоточность](#многопоточность)
- [Хранение состояния](#хранение-состояния)
- [Масштабируемость](#масштабируемость)

---

## Общий обзор

Nikita — это многопоточный сервис, который:
1. **Мониторит** каталоги журналов 1С:Предприятие
2. **Парсит** события из файлов `.lgf` (текстовых) и `.lgd` (SQLite)
3. **Отправляет** данные в хранилища (ClickHouse, Solr, Redis)
4. **Предоставляет** веб-панель мониторинга и JSON API

---

## Архитектурная диаграмма

### Общая архитектура

```mermaid
graph TB
    subgraph c1 [1C Enterprise]
        lgf[".lgf файлы<br/>(текстовые журналы)"]
        lgd[".lgd файлы<br/>(SQLite журналы)"]
    end

    subgraph nikita [Nikita Service]
        reader[Reader Module<br/>Чтение файлов]
        parser[Parser Module<br/>Парсинг событий]
        state[State Manager<br/>SQLite]
        sender[Sender Module<br/>Отправка батчей]
        web[Web Server<br/>CherryPy]
    end

    subgraph storage [Data Storage]
        ch[ClickHouse<br/>Колоночное хранилище]
        solr[Solr<br/>Полнотекстовый поиск]
        redis[Redis<br/>Буферизация]
    end

    subgraph monitoring [Monitoring]
        browser[Веб-панель<br/>localhost:8984]
        prom[Prometheus/Zabbix<br/>JSON API]
    end

    lgf --> reader
    lgd --> reader
    reader --> parser
    parser --> state
    parser --> sender
    sender --> ch
    sender --> solr
    sender --> redis
    web --> browser
    web --> prom
    parser --> web
    sender --> web
```

### Поток данных при парсинге

```mermaid
sequenceDiagram
    participant F as Файл журнала
    participant R as Reader
    participant P as Parser
    participant SM as State Manager
    participant S as Sender
    participant CH as ClickHouse

    loop Каждые N секунд
        P->>SM: Получить состояние файла
        SM-->>P: (filesize, filesizeread)
        P->>F: Проверить размер файла
        
        alt Файл изменился
            P->>R: Прочитать новые данные
            R-->>P: Сырые строки событий
            P->>P: Парсинг регулярными выражениями
            P->>S: Отправить батч (200 записей)
            S->>CH: INSERT INTO таблица
            CH-->>S: ✓ OK
            S-->>P: ✓ Успешно
            P->>SM: Обновить состояние
            SM-->>P: ✓ Сохранено
        end
    end
```

### Многопоточная архитектура

```mermaid
graph TB
    subgraph main [Main Thread]
        service[Service Entry Point]
    end

    subgraph workers [Worker Threads]
        p1[Parser Thread 1<br/>База: PROD_ZUP]
        p2[Parser Thread 2<br/>База: TEST_UT11]
        p3[Parser Thread 3<br/>База: EXTERNAL]
        pn[Parser Thread N<br/>...]
    end

    subgraph shared [Shared Resources]
        conf[g.conf<br/>Конфигурация]
        stats[g.stats<br/>Статистика]
        ibases[g.parser.ibases<br/>Список баз<br/>+ threading.Lock]
        statemgr[State Manager<br/>SQLite + Lock]
    end

    subgraph httpserver [HTTP Server Thread]
        cherry[CherryPy<br/>:8984]
    end

    service --> p1
    service --> p2
    service --> p3
    service --> pn
    service --> cherry

    p1 --> conf
    p2 --> conf
    p3 --> conf
    pn --> conf

    p1 --> stats
    p2 --> stats
    p3 --> stats
    pn --> stats

    p1 --> ibases
    p2 --> ibases
    p3 --> ibases
    pn --> ibases

    p1 --> statemgr
    p2 --> statemgr
    p3 --> statemgr
    pn --> statemgr

    cherry --> stats
    cherry --> ibases
```

---

## Компоненты системы

### 1. Entry Point (`Nikita.py`)

**Назначение:** Точка входа, управление жизненным циклом службы.

**Ключевые функции:**
- `start_all()` — запуск всех компонентов
- `stop_all()` — остановка всех потоков
- `nikita_service` (Windows) — класс Windows Service
- Обработка сигналов (Linux daemon)

**Режимы запуска:**
```bash
python Nikita.py console   # Консольный режим (отладка)
python Nikita.py install   # Установка службы (Windows)
python Nikita.py start     # Запуск службы (Windows)
python Nikita.py stop      # Остановка службы (Windows)
python Nikita.py remove    # Удаление службы (Windows)
```

### 2. Globals (`src/globals.py`)

**Назначение:** Глобальная конфигурация и состояние.

**Основные объекты:**
- `g.conf` — параметры из `.env`
- `g.stats` — статистика в реальном времени
- `g.parser` — состояние парсера
- `g.rexp` — скомпилированные регулярные выражения
- `g.ibases_lock` — блокировка для потокобезопасности

**Пример использования:**
```python
from src import globals as g

# Чтение конфигурации
clickhouse_host = g.conf.clickhouse_host

# Обновление статистики
g.stats.clickhouse_total_sent += 200

# Потокобезопасный доступ к списку баз
with g.ibases_lock:
    bases = g.parser.ibases.copy()
```

### 3. Reader (`src/reader.py`)

**Назначение:** Чтение файлов журналов (`.lgf` и `.lgd`).

**Ключевые функции:**
- `reader.read_lgp()` — чтение текстовых журналов `.lgf`
- `reader.read_lgd()` — чтение SQLite журналов `.lgd`
- `reader.trans_id()` — маппинг статусов транзакций

**Форматы:**
- **LGF** — старый текстовый формат (построчный парсинг)
- **LGD** — SQLite база данных (SQL-запросы)

### 4. Parser (`src/parser.py`)

**Назначение:** Основной модуль парсинга и координации.

**Ключевые классы:**
- `lgp_parser_thread` — поток парсера для одной базы 1С

**Ключевые методы:**
- `run()` — основной цикл потока
- `post_query()` — отправка батча в хранилища
- `send_to_clickhouse()` — отправка в ClickHouse
- `send_to_solr()` — отправка в Solr
- `read_ib_dictionary()` — чтение словарей 1С

**Алгоритм работы:**
1. Получить состояние файла из State Manager
2. Проверить размер файла
3. Если файл изменился — прочитать новые данные через Reader
4. Распарсить события регулярными выражениями
5. Сформировать батч (по умолчанию 200 записей)
6. Отправить через Sender
7. Обновить состояние в State Manager
8. Повторять каждые N секунд

### 5. State Manager (`src/state_manager.py`)

**Назначение:** Хранение состояния парсинга в SQLite.

**База данных:** `Nikita.parser.state.db`

**Таблицы:**
- `file_states` — состояние файлов (размер, прочитано)
- `committed_blocks` — история отправленных блоков и идемпотентный барьер

**Ключевые методы:**
- `get_file_state(filename, database_name)` — получить состояние файла
- `update_file_state(...)` — обновить состояние
- `log_committed_block(...)` — записать отправленный блок
- `is_block_committed(...)` — проверить, был ли блок уже успешно отправлен
- `get_total_records_sent(database_name)` — счётчик записей

**Структура file_states:**
```sql
CREATE TABLE file_states (
    database_name TEXT,
    file_basename TEXT,
    filesize INTEGER,
    filesizeread INTEGER,
    PRIMARY KEY (database_name, file_basename)
);
```

### 6. Sender (`src/sender.py`)

> **Важно про Redis:** основной путь парсера вызывает `post_query(..., bypass_redis=True)` и отправляет batch
> синхронно. Семантика Redis `main`/`processing`/`ack`/`requeue` применяется к очереди Sender при
> `bypass_redis=False`; перевод parser path на асинхронную очередь требует отдельного изменения, где
> `file_states` продвигается только после `ack` от `sender_thread`.

**Назначение:** Отправка данных в хранилища.

**Ключевые функции:**
- `send_to_clickhouse()` — вставка в ClickHouse
- `send_to_solr()` — индексация в Solr
- `send_to_redis()` — добавление в очередь Redis

**Особенности:**
- Батчевая отправка (по умолчанию 200 записей)
- Автоматическое создание таблиц в ClickHouse
- Обработка ошибок и повторные попытки
- Логирование с временем выполнения

### 7. Web Server (`src/cherry.py`)

**Назначение:** HTTP-сервер мониторинга (CherryPy).

**Endpoints:**
- `GET /` — веб-панель мониторинга (HTML)
- `GET /stats_api` — JSON API для интеграции

**Данные на панели:**
- Uptime службы
- Статус подключений (🟢/🔴)
- Счётчики отправленных записей
- Последние ошибки
- Список баз 1С с прогрессом

### 8. Tools (`src/tools.py`)

**Назначение:** Вспомогательные функции.

**Ключевые функции:**
- `debug_print()` — потокобезопасное логирование
- `sqlite3_exec()` — выполнение SQL-запросов
- `strtobool()` — парсинг логических значений

---

## Поток данных

### Детальный поток обработки события

```mermaid
flowchart TD
    Start([Запуск потока парсера]) --> CheckState
    CheckState[Получить состояние файла из SQLite]
    CheckState --> CheckSize[Проверить размер файла]
    
    CheckSize --> Changed{Файл изменился?}
    Changed -->|Нет| Sleep[Ожидание N сек]
    Sleep --> CheckState
    
    Changed -->|Да| ReadData[Прочитать новые данные]
    ReadData --> ParseRegex[Парсинг регулярными выражениями]
    ParseRegex --> Batch{Набрано 200 записей?}
    
    Batch -->|Нет| Continue[Продолжить чтение]
    Continue --> ParseRegex
    
    Batch -->|Да| SendBatch[Отправить батч]
    SendBatch --> CH{ClickHouse включен?}
    
    CH -->|Да| SendCH[INSERT в ClickHouse]
    SendCH --> CHResult{Успех?}
    CHResult -->|Да| UpdateStats1[Обновить g.stats]
    CHResult -->|Нет| LogError1[Записать ошибку]
    
    CH -->|Нет| Solr
    UpdateStats1 --> Solr
    LogError1 --> Solr
    
    Solr{Solr включен?}
    Solr -->|Да| SendSolr[POST в Solr]
    SendSolr --> SolrResult{Успех?}
    SolrResult -->|Да| UpdateStats2[Обновить g.stats]
    SolrResult -->|Нет| LogError2[Записать ошибку]
    
    Solr -->|Нет| UpdateState
    UpdateStats2 --> UpdateState
    LogError2 --> UpdateState
    
    UpdateState[Обновить состояние в SQLite]
    UpdateState --> CheckState
```

---

## Многопоточность

### Модель потоков

Nikita использует **многопоточную модель** с потоком на каждую базу 1С:

```python
# Упрощённый пример
for база in список_баз:
    поток = Thread(target=парсер_функция, args=(база,))
    поток.start()
```

### Потокобезопасность

**Проблема:** Несколько потоков обращаются к общим данным.

**Решение:**
1. **threading.Lock** для критических секций
2. **SQLite** с журналированием WAL
3. **Неизменяемые данные** (конфигурация)

**Примеры:**

```python
# 1. Блокировка для списка баз
with g.ibases_lock:
    bases = g.parser.ibases.copy()

# 2. Блокировка для логирования
with tools.log_lock:
    file.write(message)

# 3. State Manager внутренне использует Lock
state_manager.update_file_state(...)  # Потокобезопасно
```

### Распределение нагрузки

**Автоматическое:**
- По умолчанию создаётся по 1 потоку на базу 1С
- Если баз больше, чем ядер CPU — всё равно по 1 потоку на базу
- Каждый поток работает независимо

**Ручное:**
```ini
# .env
PARSER_THREADS=4  # Ограничить 4 потоками
```

---

## Хранение состояния

### SQLite State Database

**Файл:** `Nikita.parser.state.db`

**Назначение:**
- Запомнить, сколько прочитано из каждого файла
- Продолжить с того же места после перезапуска
- Избежать дублирования данных

**Схема:**

```sql
-- Состояние файлов
CREATE TABLE file_states (
    database_name TEXT NOT NULL,     -- Имя базы 1С
    file_basename TEXT NOT NULL,     -- Имя файла (без пути)
    filesize INTEGER,                -- Полный размер файла
    filesizeread INTEGER,            -- Сколько уже прочитано
    PRIMARY KEY (database_name, file_basename)
);

-- История отправленных блоков
CREATE TABLE committed_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    database_name TEXT,
    file_basename TEXT,
    offset_start INTEGER,
    offset_end INTEGER,
    data_records INTEGER,
    committed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Пример запроса:**
```python
state = state_manager.get_file_state("/path/to/file.lgp", "База1")
# {'filesize': 1000000, 'filesizeread': 500000}

# Продолжаем чтение с позиции 500000
```

### Миграция состояния

При обновлении с версии 1.x → 2.0:
- Автоматическая миграция старой структуры
- Старые данные сохраняются
- Логируется в `debug/Nikita.*.log`

---

## Масштабируемость

### Вертикальное масштабирование

**Увеличение ресурсов одного сервера:**

1. **CPU:**
   - Увеличьте `PARSER_THREADS` в `.env`
   - Рекомендуется: по 1 потоку на базу 1С

2. **Память:**
   - Увеличьте `SOLR_MEM_MAX` (если используется Solr)
   - Nikita сам потребляет ~200-500 MB

3. **Диск:**
   - Используйте SSD для журналов 1С
   - Используйте SSD для ClickHouse

### Горизонтальное масштабирование

**Несколько экземпляров Nikita:**

**Сценарий:** У вас 100 баз 1С, распределённых по разным серверам.

**Решение:**
1. Запустите Nikita на каждом сервере с 1С
2. Все отправляют в один ClickHouse кластер
3. Каждый экземпляр обрабатывает свои базы

**Пример:**
```
Сервер 1C №1 (20 баз) → Nikita №1 ─┐
Сервер 1C №2 (30 баз) → Nikita №2 ─┼→ ClickHouse кластер
Сервер 1C №3 (50 баз) → Nikita №3 ─┘
```

### Масштабирование ClickHouse

Для больших объёмов данных используйте кластер ClickHouse:
- **Sharding** — распределение данных по серверам
- **Replication** — репликация для отказоустойчивости
- **Distributed таблицы** — прозрачный доступ

См. [ClickHouse Documentation](https://clickhouse.com/docs/ru/engines/table-engines/special/distributed)

---

## Производительность

### Типичные показатели

**Железо:** 4 CPU cores, 8 GB RAM, SSD

| Параметр | Значение |
|----------|----------|
| Баз 1С | 10 |
| События/сек | 1000-5000 |
| Задержка отправки | <50ms (локальный ClickHouse) |
| Потребление CPU | 10-30% |
| Потребление RAM | 200-500 MB |

### Оптимизация

1. **Используйте `.lgd` вместо `.lgf`** — SQLite быстрее текстового парсинга
2. **Локальный ClickHouse** — минимизация сетевой задержки
3. **SSD диски** — быстрое чтение журналов
4. **Отключите Solr** — если не нужен полнотекстовый поиск
5. **Используйте Redis** — буферизация при пиковых нагрузках

---

## Дополнительно

### Диаграмма развёртывания

```mermaid
graph TB
    subgraph server1c [1C Server]
        c1app[1C:Предприятие]
        logs[Журналы регистрации]
    end

    subgraph appserver [Application Server]
        nikita[Nikita Service]
    end

    subgraph dbserver [Database Server]
        ch[ClickHouse]
    end

    subgraph optional [Optional Services]
        solr[Solr Server]
        redis[Redis Server]
    end

    c1app --> logs
    logs --> nikita
    nikita --> ch
    nikita -.-> solr
    nikita -.-> redis
```

---

**Обновлено:** 2025-12-11  
**Версия:** 2.0.0

