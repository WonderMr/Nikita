# Оптимизация SQLite: Составной ключ (database + basename)

## Суть изменений

**ДО:**
```
file_states:
  filename (PK) | filesize | filesizeread
  /var/log/1C/base1/20251209.lgp | 1000 | 500
  
committed_blocks:
  id | filename | basename | ...
  1 | /var/log/1C/base1/20251209.lgp | base1 | ...
```

**ПОСЛЕ:**
```
file_states:
  database_name (PK) | file_basename (PK) | filesize | filesizeread
  base1 | 20251209.lgp | 1000 | 500
  base2 | 20251209.lgp | 2000 | 1000  ← файл с тем же именем, но из другой базы
  
committed_blocks:
  id | database_name | file_basename | ...
  1 | base1 | 20251209.lgp | ...
  2 | base2 | 20251209.lgp | ...  ← нет коллизий!
```

## Проблемы первоначального решения

### ❌ Версия 1 (только basename)
```python
# ПЛОХО: Коллизии!
cursor.execute("SELECT ... WHERE filename = ?", ("20251209.lgp",))
# Какая база? base1 или base2? Неопределённость!
```

**Проблема:** Если в системе есть несколько баз 1С (`base1`, `base2`), и у них есть файлы с одинаковыми именами (`20251209.lgp`), то в таблице `file_states` (где `filename` — PRIMARY KEY) они будут **перезаписывать друг друга**.

Пример:
```
/var/log/1C/base1/20251209.lgp → basename: 20251209.lgp
/var/log/1C/base2/20251209.lgp → basename: 20251209.lgp (КОЛЛИЗИЯ!)
```

### ✅ Версия 2 (database_name + file_basename)
```python
# ХОРОШО: Составной ключ
cursor.execute(
    "SELECT ... WHERE database_name = ? AND file_basename = ?", 
    ("base1", "20251209.lgp")
)
# Теперь ясно: файл из базы base1
```

**Решение:** Составной PRIMARY KEY `(database_name, file_basename)` гарантирует уникальность записи для каждой комбинации база+файл.

## API Changes (Breaking)

### StateManager методы

#### `get_file_state(filename, database_name='unknown')`
```python
# Было:
state = state_manager.get_file_state("/path/to/file.lgp")

# Стало:
state = state_manager.get_file_state("/path/to/file.lgp", "base1")
```

#### `update_file_state(filename, filesize, filesizeread, database_name='unknown')`
```python
# Было:
state_manager.update_file_state("/path/to/file.lgp", 1000, 500)

# Стало:
state_manager.update_file_state("/path/to/file.lgp", 1000, 500, "base1")
```

#### `log_committed_block(filename, offset_start, offset_end, data_records, database_name='unknown')`
```python
# Было:
state_manager.log_committed_block(pf_name, 0, 1000, records, basename=pf_base)

# Стало:
state_manager.log_committed_block(pf_name, 0, 1000, records, database_name=pf_base)
# Параметр basename переименован в database_name для ясности
```

#### `get_total_records_sent(database_name)`
```python
# Было:
total = state_manager.get_total_records_sent("base1")  # basename

# Стало:
total = state_manager.get_total_records_sent("base1")  # database_name
# Упрощён: убран избыточный поиск по LIKE
```

## Миграция данных

**Автоматическая:** При первом запуске StateManager автоматически обнаружит старую структуру и выполнит миграцию:

1. Переименует старые таблицы (`_old`)
2. Создаст новые таблицы с правильной структурой
3. Мигрирует данные, извлекая basename из полных путей
4. Для старых записей без `database_name` установит `'unknown'`
5. Удалит старые таблицы

**Логирование:** Миграция логируется через `t.debug_print()`:
```
⚠️ Обнаружена старая структура file_states, выполняется миграция...
✓ Миграция file_states завершена
⚠️ Обнаружена старая структура committed_blocks, выполняется миграция...
✓ Миграция committed_blocks завершена
```

## Обновления в parser.py

Все вызовы StateManager в `src/parser.py` обновлены для передачи `pf_base` (имя базы 1С) как параметра `database_name`:

```python
# Примеры обновлённых вызовов:
_state = state_manager.get_file_state(pf_name, pf_base)

state_manager.update_file_state(
    file_state['filename'], 
    file_state['filesize'], 
    file_state['filesizeread'], 
    pf_base  # ← добавлен параметр
)

state_manager.log_committed_block(
    pf_name, 
    batch_start_offset, 
    file_state['filesizeread'], 
    records_to_log, 
    pf_base  # ← параметр basename переименован в database_name
)
```

## Преимущества

1. ✅ **Устранены коллизии** — файлы с одинаковыми именами из разных баз не конфликтуют
2. ✅ **Уменьшен размер БД** — хранится `basename` вместо полного пути
3. ✅ **Улучшена читаемость** — в БД видно `(base1, file.lgp)` вместо `/var/log/1C/base1/file.lgp`
4. ✅ **Корректная работа с multiple bases** — система теперь правильно работает с несколькими базами 1С
5. ✅ **Автоматическая миграция** — не нужно вручную запускать скрипты

## Тестирование

После внедрения рекомендуется протестировать:
1. Работу с одной базой 1С
2. Работу с несколькими базами 1С, имеющими файлы с одинаковыми именами
3. Миграцию со старой структуры БД (если есть prod данные)
4. Корректность счётчиков `get_total_records_sent()`
