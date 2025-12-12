# Схема ClickHouse

Техническая документация по структуре таблиц ClickHouse для хранения журналов 1С.

---

## Содержание

- [Обзор](#обзор)
- [Создание базы данных](#создание-базы-данных)
- [Схема таблицы](#схема-таблицы)
- [Типы данных и оптимизация](#типы-данных-и-оптимизация)
- [Индексы и партиционирование](#индексы-и-партиционирование)
- [Примеры запросов](#примеры-запросов)
- [Обслуживание](#обслуживание)

---

## Обзор

### Структура хранения

Nikita создаёт:
- **Одну базу данных** (по умолчанию `zhr1c`)
- **Отдельную таблицу для каждой базы 1С** (например, `zhr1c.PROD_ZUP`, `zhr1c.TEST_UT11`)

**Преимущества:**
- Изоляция данных разных баз
- Простота управления (DROP TABLE для удаления базы)
- Возможность индивидуальных настроек TTL

---

## Создание базы данных

### Автоматическое создание

При первом запуске Nikita автоматически создаёт БД:

```sql
CREATE DATABASE IF NOT EXISTS zhr1c
ENGINE = Atomic
COMMENT 'База данных для журналов регистрации 1С с максимальным сжатием'
```

**Engine Atomic:**
- Поддержка транзакций
- Атомарное переименование таблиц
- Современный движок (ClickHouse 20.5+)

### Настройка

Имя базы данных задаётся в `.env`:
```ini
CLICKHOUSE_DATABASE=zhr1c
```

---

## Схема таблицы

### Автоматическое создание таблицы

Для каждой базы 1С создаётся таблица:

```sql
CREATE TABLE IF NOT EXISTS zhr1c.{TABLE_NAME} (
    DateTime                DateTime64(6)               CODEC(Delta, ZSTD(1)),
    TransactionStatus       LowCardinality(String)      CODEC(ZSTD(1)),
    TransactionDate         Nullable(DateTime64(6))     CODEC(Delta, ZSTD(1)),
    TransactionID           Nullable(Int64)             CODEC(ZSTD(1)),
    UserUUID                Nullable(UUID)              CODEC(ZSTD(1)),
    User                    LowCardinality(String)      CODEC(ZSTD(1)),
    Computer                LowCardinality(String)      CODEC(ZSTD(1)),
    Application             LowCardinality(String)      CODEC(ZSTD(1)),
    Connection              Nullable(Int32)             CODEC(ZSTD(1)),
    Event                   LowCardinality(String)      CODEC(ZSTD(1)),
    Level                   LowCardinality(String)      CODEC(ZSTD(1)),
    Comment                 String                      CODEC(ZSTD(1)),
    MetadataUUID            Nullable(UUID)              CODEC(ZSTD(1)),
    Metadata                String                      CODEC(ZSTD(1)),
    Data                    String                      CODEC(ZSTD(1)),
    DataPresentation        String                      CODEC(ZSTD(1)),
    WorkServer              LowCardinality(String)      CODEC(ZSTD(1)),
    PrimaryPort             Nullable(Int32)             CODEC(ZSTD(1)),
    SecondaryPort           Nullable(Int32)             CODEC(ZSTD(1)),
    Session                 Nullable(Int32)             CODEC(ZSTD(1))
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(DateTime)
ORDER BY (DateTime, Event)
TTL DateTime + INTERVAL 365 DAY
SETTINGS index_granularity = 8192
COMMENT 'Журнал регистрации 1С для базы {TABLE_NAME}'
```

### Описание полей

| Поле | Тип | Описание |
|------|-----|----------|
| `DateTime` | DateTime64(6) | Дата и время события (микросекунды) |
| `TransactionStatus` | LowCardinality(String) | Статус транзакции ('N', 'C', 'R', 'U') |
| `TransactionDate` | Nullable(DateTime64(6)) | Дата начала транзакции |
| `TransactionID` | Nullable(Int64) | Идентификатор транзакции |
| `UserUUID` | Nullable(UUID) | UUID пользователя |
| `User` | LowCardinality(String) | Имя пользователя |
| `Computer` | LowCardinality(String) | Имя компьютера |
| `Application` | LowCardinality(String) | Приложение (1cv8, rphost, etc) |
| `Connection` | Nullable(Int32) | Номер соединения |
| `Event` | LowCardinality(String) | Тип события |
| `Level` | LowCardinality(String) | Уровень важности |
| `Comment` | String | Комментарий |
| `MetadataUUID` | Nullable(UUID) | UUID объекта метаданных |
| `Metadata` | String | Имя объекта метаданных |
| `Data` | String | Дополнительные данные |
| `DataPresentation` | String | Представление данных |
| `WorkServer` | LowCardinality(String) | Рабочий сервер |
| `PrimaryPort` | Nullable(Int32) | Основной порт |
| `SecondaryPort` | Nullable(Int32) | Вспомогательный порт |
| `Session` | Nullable(Int32) | Номер сеанса |

---

## Типы данных и оптимизация

### DateTime64(6) — Временные метки

```sql
DateTime DateTime64(6) CODEC(Delta, ZSTD(1))
```

**Особенности:**
- Точность до микросекунд (6 цифр после запятой)
- **Delta кодирование:** эффективно для монотонно возрастающих значений
- **ZSTD(1):** дополнительное сжатие

**Степень сжатия:** ~10-20x от исходного размера

### LowCardinality(String) — Часто повторяющиеся значения

```sql
User LowCardinality(String) CODEC(ZSTD(1))
```

**Используется для:**
- Пользователи (обычно 10-100 уникальных)
- Компьютеры (обычно 5-50 уникальных)
- События (обычно 50-200 уникальных)
- Приложения (обычно 3-5 уникальных)
- Уровни важности (4 уникальных)

**Преимущества:**
- Словарное кодирование (вместо строки хранится индекс)
- Меньше RAM при запросах
- Быстрее JOIN и GROUP BY

**Степень сжатия:** ~50-100x

### String — Произвольный текст

```sql
Comment String CODEC(ZSTD(1))
```

**Используется для:**
- Комментарии (уникальные тексты)
- Данные (JSON, XML)
- Представление данных

**Степень сжатия:** ~3-5x с ZSTD

### Nullable — Необязательные поля

```sql
TransactionID Nullable(Int64)
```

**Причина:** Не все события имеют транзакцию, метаданные, порты и т.д.

**Overhead:** ~1 бит на значение (битовая маска NULL)

### UUID — Уникальные идентификаторы

```sql
UserUUID Nullable(UUID) CODEC(ZSTD(1))
```

**Преимущества:**
- Занимает 16 байт (вместо 36 для строки)
- Быстрее сравнение
- Поддержка индексов

---

## Индексы и партиционирование

### PRIMARY KEY / ORDER BY

```sql
ORDER BY (DateTime, Event)
```

**Назначение:**
- Первичная сортировка данных на диске
- Эффективные запросы по времени и типу события

**Примеры оптимальных запросов:**
```sql
-- Быстро (использует ORDER BY)
SELECT * FROM table WHERE DateTime >= '2025-12-01' AND DateTime < '2025-12-11'
SELECT * FROM table WHERE DateTime >= '2025-12-01' AND Event = 'Ошибка'

-- Медленно (не использует ORDER BY)
SELECT * FROM table WHERE User = 'Иванов'
```

### PARTITION BY

```sql
PARTITION BY toYYYYMM(DateTime)
```

**Назначение:**
- Разделение данных по месяцам
- Быстрое удаление старых данных (`ALTER TABLE DROP PARTITION`)
- Эффективные запросы по диапазонам дат

**Структура на диске:**
```
zhr1c/PROD_ZUP/
├── 202411_1_1_0/     # Ноябрь 2024
├── 202412_1_1_0/     # Декабрь 2024
└── 202501_1_1_0/     # Январь 2025
```

**Пример удаления старых данных:**
```sql
ALTER TABLE zhr1c.PROD_ZUP DROP PARTITION '202411'
```

### TTL — Автоматическое удаление

```sql
TTL DateTime + INTERVAL 365 DAY
```

**Назначение:**
- Автоматическое удаление данных старше 365 дней
- Экономия места на диске
- Соответствие политикам хранения данных

**Настройка периода хранения:**

В коде (требует изменения):
```python
ttl_days = 730  # 2 года
CREATE TABLE ... TTL DateTime + INTERVAL {ttl_days} DAY
```

Или после создания:
```sql
ALTER TABLE zhr1c.PROD_ZUP MODIFY TTL DateTime + INTERVAL 730 DAY
```

### Index Granularity

```sql
SETTINGS index_granularity = 8192
```

**Назначение:**
- Размер блока для первичного индекса
- 8192 строк = 1 индексная запись

**Компромисс:**
- Меньше значение = больше RAM, точнее поиск
- Больше значение = меньше RAM, медленнее поиск

**8192 — оптимально для большинства случаев**

---

## Примеры запросов

### Базовые запросы

#### Все события за день

```sql
SELECT *
FROM zhr1c.PROD_ZUP
WHERE toDate(DateTime) = '2025-12-11'
ORDER BY DateTime DESC
LIMIT 1000
```

#### События конкретного пользователя

```sql
SELECT DateTime, Event, Comment
FROM zhr1c.PROD_ZUP
WHERE User = 'Иванов И.И.'
  AND DateTime >= '2025-12-01'
ORDER BY DateTime DESC
```

### Аналитические запросы

#### Топ-10 пользователей по активности

```sql
SELECT 
    User,
    count() as EventCount
FROM zhr1c.PROD_ZUP
WHERE DateTime >= today() - INTERVAL 7 DAY
GROUP BY User
ORDER BY EventCount DESC
LIMIT 10
```

#### Ошибки за последние 24 часа

```sql
SELECT 
    DateTime,
    User,
    Event,
    Comment
FROM zhr1c.PROD_ZUP
WHERE DateTime >= now() - INTERVAL 24 HOUR
  AND Level = 'Ошибка'
ORDER BY DateTime DESC
```

#### Статистика событий по часам

```sql
SELECT 
    toStartOfHour(DateTime) as Hour,
    Event,
    count() as Count
FROM zhr1c.PROD_ZUP
WHERE DateTime >= today()
GROUP BY Hour, Event
ORDER BY Hour, Count DESC
```

### Транзакции

#### Незавершённые транзакции

```sql
SELECT 
    DateTime,
    User,
    TransactionID,
    Comment
FROM zhr1c.PROD_ZUP
WHERE TransactionStatus = 'U'
  AND DateTime >= today()
ORDER BY DateTime DESC
```

#### Откаченные транзакции (Rollback)

```sql
SELECT 
    DateTime,
    User,
    TransactionID,
    Event,
    Comment
FROM zhr1c.PROD_ZUP
WHERE TransactionStatus = 'R'
  AND DateTime >= today() - INTERVAL 7 DAY
ORDER BY DateTime DESC
```

---

## Обслуживание

### Просмотр размера таблиц

```sql
SELECT 
    table,
    formatReadableSize(sum(bytes)) as size,
    sum(rows) as rows,
    max(modification_time) as latest_modification
FROM system.parts
WHERE database = 'zhr1c' AND active
GROUP BY table
ORDER BY sum(bytes) DESC
```

### Просмотр партиций

```sql
SELECT 
    partition,
    sum(rows) as rows,
    formatReadableSize(sum(bytes)) as size
FROM system.parts
WHERE database = 'zhr1c' 
  AND table = 'PROD_ZUP'
  AND active
GROUP BY partition
ORDER BY partition
```

### Оптимизация таблицы

```sql
-- Принудительное слияние партиций
OPTIMIZE TABLE zhr1c.PROD_ZUP FINAL

-- Удаление помеченных TTL данных
OPTIMIZE TABLE zhr1c.PROD_ZUP FINAL CLEANUP
```

### Очистка старых данных

```sql
-- Удалить партицию за ноябрь 2024
ALTER TABLE zhr1c.PROD_ZUP DROP PARTITION '202411'

-- Удалить данные по условию (медленно!)
ALTER TABLE zhr1c.PROD_ZUP DELETE WHERE DateTime < '2024-01-01'
```

### Статистика сжатия

```sql
SELECT 
    table,
    formatReadableSize(sum(data_compressed_bytes)) as compressed,
    formatReadableSize(sum(data_uncompressed_bytes)) as uncompressed,
    round(sum(data_uncompressed_bytes) / sum(data_compressed_bytes), 2) as ratio
FROM system.parts
WHERE database = 'zhr1c' AND active
GROUP BY table
```

---

## Производительность

### Типичные показатели

**Железо:** 4 CPU, 16 GB RAM, SSD

| Операция | Производительность |
|----------|-------------------|
| INSERT (батч 200 записей) | <50ms |
| SELECT последние 1000 записей | <100ms |
| GROUP BY по часам (1 день) | <200ms |
| COUNT(*) вся таблица (100M записей) | ~5 секунд |

### Рекомендации по оптимизации

1. **Всегда фильтруйте по DateTime** — использует ORDER BY
2. **Используйте PREWHERE для фильтров** — быстрее WHERE
3. **Избегайте SELECT *** — указывайте нужные колонки
4. **Батчинг INSERT** — вставляйте пакетами, не по 1 записи
5. **Индексы** — рассмотрите добавление skip indices для часто используемых фильтров

---

**Обновлено:** 2025-12-11  
**Версия:** 2.0.0

