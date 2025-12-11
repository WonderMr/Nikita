# Мониторинг Nikita

Полное руководство по мониторингу службы Nikita: веб-панель, JSON API, интеграция с системами мониторинга.

---

## Содержание

- [Веб-панель мониторинга](#веб-панель-мониторинга)
- [JSON API](#json-api)
- [Логирование](#логирование)
- [Интеграция с системами мониторинга](#интеграция-с-системами-мониторинга)
- [Статистика в реальном времени](#статистика-в-реальном-времени)

---

## Веб-панель мониторинга

### Доступ

После запуска службы откройте браузер:

```
http://localhost:8984/
```

Если изменили порт в `.env` (`HTTP_LISTEN_PORT`), используйте свой порт.

### Структура панели

#### 1. Заголовок и информация о системе

- **Название службы:** Nikita / Nikita
- **Uptime:** время работы с момента запуска (формат: `2ч 15м 30с`)
- **Последняя активность:** время последней отправки данных

#### 2. Статистика сервисов

Компактная таблица с колонками:

| Сервис | Статус | Хост | БД | Записей | Ошибок |
|--------|--------|------|----|---------| -------|
| ClickHouse | 🟢 Подключено | localhost:9000 | zhr1c | 15432 | 0 |
| Solr | Отключено | - | - | - | - |
| Redis | Отключено | - | - | - | - |

**Статусы:**
- 🟢 **Зелёный** — сервис работает нормально, нет ошибок
- 🔴 **Красный** — есть проблемы с подключением или отправкой
- **Отключено** — сервис выключен в конфигурации (`.env`)

#### 3. Последние ошибки

Блок "🚨 Последние ошибки" показывает последние 5 ошибок:
- Время возникновения
- Тип сервиса (ClickHouse/Solr/Redis)
- Краткое описание ошибки

Если ошибок нет — отображается "Нет ошибок".

#### 4. Список обрабатываемых баз 1С

Таблица всех баз данных 1С:

| Имя базы | Путь | Формат | Размер | Обработано | Прогресс |
|----------|------|--------|--------|------------|----------|
| PROD_ZUP | /path/to/1Cv8Log | lgd | 1.2 GB | 980 MB | ▓▓▓▓▓▓▓▓░░ 81% |

**Поля:**
- **Имя базы** — название информационной базы 1С
- **Путь** — путь к каталогу журнала регистрации
- **Формат** — `lgf` (старый текстовый) или `lgd` (SQLite)
- **Размер** — общий размер журналов
- **Обработано** — объём обработанных данных
- **Прогресс** — процент обработки с прогресс-баром

### Автообновление

Страница автоматически обновляется каждые **30 секунд**.

Для ручного обновления нажмите `F5` или кнопку обновления браузера.

---

## JSON API

### Endpoint

```
GET http://localhost:8984/stats_api
```

### Формат ответа

```json
{
  "uptime_seconds": 5461,
  "uptime_formatted": "1ч 31м 1с",
  "total_records_parsed": 0,
  "clickhouse": {
    "enabled": true,
    "host": "localhost",
    "port": 9000,
    "database": "zhr1c",
    "connection_ok": true,
    "total_sent": 15432,
    "total_errors": 0,
    "last_success_time": "2025-12-11T14:23:45.123456",
    "last_error_time": null,
    "last_error_msg": ""
  },
  "solr": {
    "enabled": false
  },
  "redis": {
    "enabled": false
  },
  "last_errors": [],
  "databases": [
    {
      "name": "PROD_ZUP",
      "path": "/home/usr1cv8/.1cv8/1C/1cv8/reg_1541/uuid/1Cv8Log",
      "format": "lgd",
      "total_size": 1258291200,
      "parsed_size": 1020510208,
      "percent": 81.11
    }
  ]
}
```

### Описание полей

#### Общие поля

| Поле | Тип | Описание |
|------|-----|----------|
| `uptime_seconds` | integer | Время работы в секундах |
| `uptime_formatted` | string | Время работы в читаемом формате |
| `total_records_parsed` | integer | Всего распарсено записей |

#### Секция `clickhouse`

| Поле | Тип | Описание |
|------|-----|----------|
| `enabled` | boolean | Включен ли сервис |
| `host` | string | Хост подключения |
| `port` | integer | Порт подключения |
| `database` | string | Имя базы данных |
| `connection_ok` | boolean | Статус подключения (true/false) |
| `total_sent` | integer | Всего отправлено записей |
| `total_errors` | integer | Всего ошибок отправки |
| `last_success_time` | string\|null | ISO-формат времени последней успешной отправки |
| `last_error_time` | string\|null | ISO-формат времени последней ошибки |
| `last_error_msg` | string | Текст последней ошибки |

#### Секция `solr` и `redis`

Аналогичная структура. Если `enabled: false`, остальные поля отсутствуют.

#### Массив `last_errors`

Список последних 10 ошибок:
```json
{
  "time": "2025-12-11T14:20:00.000000",
  "type": "ClickHouse",
  "message": "Connection timeout"
}
```

#### Массив `databases`

Список обрабатываемых баз 1С:
```json
{
  "name": "PROD_ZUP",
  "path": "/path/to/1Cv8Log",
  "format": "lgd",
  "total_size": 1258291200,
  "parsed_size": 1020510208,
  "percent": 81.11
}
```

### Примеры использования

#### cURL

```bash
# Получить всю статистику
curl http://localhost:8984/stats_api

# С форматированием (jq)
curl -s http://localhost:8984/stats_api | jq

# Только статус ClickHouse
curl -s http://localhost:8984/stats_api | jq '.clickhouse.connection_ok'

# Количество отправленных записей
curl -s http://localhost:8984/stats_api | jq '.clickhouse.total_sent'

# Список баз
curl -s http://localhost:8984/stats_api | jq '.databases[].name'
```

#### Python

```python
import requests

response = requests.get('http://localhost:8984/stats_api')
data = response.json()

print(f"Uptime: {data['uptime_formatted']}")
print(f"ClickHouse OK: {data['clickhouse']['connection_ok']}")
print(f"Sent: {data['clickhouse']['total_sent']}")
```

#### PowerShell

```powershell
$stats = Invoke-RestMethod http://localhost:8984/stats_api
Write-Host "Uptime: $($stats.uptime_formatted)"
Write-Host "ClickHouse: $($stats.clickhouse.connection_ok)"
```

---

## Логирование

### Расширенная система логирования

Nikita использует детальное логирование с символами для быстрой визуальной идентификации:
- ✓ — успешные операции
- ✗ — ошибки
- → — начало операции
- 📊 — статистика

### Примеры логов

#### Успешная отправка в ClickHouse

```
2025-12-11 14:23:45.123456:::lgp parser:::→ CLICKHOUSE: Начинаем отправку пакета для базы 'PROD_ZUP' (записей: 200)
2025-12-11 14:23:45.156789:::lgp parser:::✓ CLICKHOUSE: Успешно отправлено 200 записей в таблицу zhr1c.PROD_ZUP
2025-12-11 14:23:45.156789:::lgp parser:::✓ CLICKHOUSE: Время выполнения: 0.033 сек (6060.6 записей/сек)
2025-12-11 14:23:45.156789:::lgp parser:::✓ CLICKHOUSE: Всего отправлено за сессию: 15432 записей
```

#### Ошибка отправки

```
2025-12-11 14:25:10.123456:::lgp parser:::✗ CLICKHOUSE: Ошибка отправки: Connection refused
2025-12-11 14:25:10.123456:::lgp parser:::✗ CLICKHOUSE: Traceback:
  File "src/parser.py", line 456, in send_to_clickhouse
    self.chclient.execute(query, batch)
  clickhouse_driver.errors.NetworkError: Code: 210. Connection refused
```

### Расположение логов

**Linux:**
```
/opt/Nikita/debug/Nikita.<PID>.log
```

**Windows:**
```
C:\Program Files\Nikita\debug\Nikita.<PID>.log
```

### Просмотр логов

#### Linux

```bash
# Все логи в реальном времени
tail -f /opt/Nikita/debug/Nikita.*.log

# Только ошибки
tail -f /opt/Nikita/debug/Nikita.*.log | grep "✗"

# Только успешные операции
tail -f /opt/Nikita/debug/Nikita.*.log | grep "✓"

# Только ClickHouse операции
tail -f /opt/Nikita/debug/Nikita.*.log | grep "CLICKHOUSE"

# Последние 100 строк
tail -100 /opt/Nikita/debug/Nikita.*.log

# Логи systemd
sudo journalctl -u Nikita -f
```

#### Windows

```powershell
# Последние 50 строк (с обновлением)
Get-Content "C:\Program Files\Nikita\debug\Nikita.*.log" -Tail 50 -Wait

# Только ошибки
Get-Content "C:\Program Files\Nikita\debug\Nikita.*.log" | Select-String "✗"

# С форматированием
Get-Content "C:\Program Files\Nikita\debug\Nikita.*.log" -Tail 100 | Format-Table -AutoSize
```

### Уровни детализации

Управляется через `.env`:

```ini
# Глобальная отладка (можно включить через веб-интерфейс)
DEBUG_ENABLED=false

# Подробное логирование парсера
DEBUG_PARSER=false
```

**Рекомендации:**
- Для продакшн: `DEBUG_ENABLED=false`, `DEBUG_PARSER=false`
- Для отладки: `DEBUG_ENABLED=true`, `DEBUG_PARSER=true`
- Для диагностики проблем: включайте временно через веб-интерфейс

---

## Интеграция с системами мониторинга

### Prometheus

#### Способ 1: Простой экспортер (Python)

Создайте файл `nikita_exporter.py`:

```python
#!/usr/bin/env python3
import requests
import time
from prometheus_client import Gauge, start_http_server

# Создаём метрики
clickhouse_sent = Gauge('nikita_clickhouse_sent', 'ClickHouse records sent')
clickhouse_errors = Gauge('nikita_clickhouse_errors', 'ClickHouse errors')
connection_ok = Gauge('nikita_connection_ok', 'Connection status', ['service'])
uptime_seconds = Gauge('nikita_uptime_seconds', 'Service uptime')

# Запускаем HTTP-сервер Prometheus на порту 9100
start_http_server(9100)

print("Nikita exporter started on :9100")

while True:
    try:
        stats = requests.get('http://localhost:8984/stats_api', timeout=5).json()
        
        # Обновляем метрики
        uptime_seconds.set(stats['uptime_seconds'])
        
        if stats.get('clickhouse', {}).get('enabled'):
            clickhouse_sent.set(stats['clickhouse']['total_sent'])
            clickhouse_errors.set(stats['clickhouse']['total_errors'])
            connection_ok.labels(service='clickhouse').set(
                1 if stats['clickhouse']['connection_ok'] else 0
            )
        
        time.sleep(15)  # Обновление каждые 15 секунд
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(15)
```

Запустите:
```bash
python3 nikita_exporter.py &
```

Добавьте в `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'nikita'
    static_configs:
      - targets: ['localhost:9100']
```

#### Способ 2: Текстовый коллектор

```bash
#!/bin/bash
# /usr/local/bin/nikita_textfile_collector.sh

STATS=$(curl -s http://localhost:8984/stats_api)

echo "# HELP nikita_clickhouse_sent Total records sent to ClickHouse"
echo "# TYPE nikita_clickhouse_sent counter"
echo "nikita_clickhouse_sent $(echo $STATS | jq '.clickhouse.total_sent')"

echo "# HELP nikita_connection_ok Connection status (1=ok, 0=error)"
echo "# TYPE nikita_connection_ok gauge"
if [ "$(echo $STATS | jq '.clickhouse.connection_ok')" = "true" ]; then
    echo 'nikita_connection_ok{service="clickhouse"} 1'
else
    echo 'nikita_connection_ok{service="clickhouse"} 0'
fi
```

Настройте node_exporter с `--collector.textfile.directory`.

### Zabbix

Создайте скрипт `/etc/zabbix/scripts/nikita_stats.sh`:

```bash
#!/bin/bash

case "$1" in
    clickhouse.sent)
        curl -s http://localhost:8984/stats_api | jq '.clickhouse.total_sent'
        ;;
    clickhouse.errors)
        curl -s http://localhost:8984/stats_api | jq '.clickhouse.total_errors'
        ;;
    clickhouse.connection)
        curl -s http://localhost:8984/stats_api | jq '.clickhouse.connection_ok' | sed 's/true/1/;s/false/0/'
        ;;
    uptime)
        curl -s http://localhost:8984/stats_api | jq '.uptime_seconds'
        ;;
    *)
        echo "Usage: $0 {clickhouse.sent|clickhouse.errors|clickhouse.connection|uptime}"
        exit 1
        ;;
esac
```

Сделайте исполняемым:
```bash
chmod +x /etc/zabbix/scripts/nikita_stats.sh
```

В Zabbix создайте элементы данных:
- **Ключ:** `system.run[/etc/zabbix/scripts/nikita_stats.sh clickhouse.sent]`
- **Тип:** Числовой (целое положительное)
- **Интервал обновления:** 60 секунд

### Grafana

Используйте Prometheus в качестве источника данных.

**Пример панелей:**

1. **Singlestat: Статус подключения**
   - Запрос: `nikita_connection_ok{service="clickhouse"}`
   - Thresholds: 0 = red, 1 = green

2. **Graph: Записей отправлено**
   - Запрос: `rate(nikita_clickhouse_sent[5m])`
   - Заголовок: "Записей/сек в ClickHouse"

3. **Graph: Uptime**
   - Запрос: `nikita_uptime_seconds`
   - Форматирование: секунды → дни/часы

4. **Table: Список баз**
   - Используйте JSON API plugin
   - URL: `http://localhost:8984/stats_api`
   - JSONPath: `$.databases[*]`

---

## Статистика в реальном времени

### Архитектура статистики

Nikita использует глобальный объект `g.stats` для сбора статистики:

```python
# Структура g.stats
class Stats:
    start_time = datetime.now()
    
    # ClickHouse
    clickhouse_total_sent = 0
    clickhouse_total_errors = 0
    clickhouse_last_success_time = None
    clickhouse_last_error_time = None
    clickhouse_last_error_msg = ""
    clickhouse_connection_ok = False
    
    # Solr
    solr_total_sent = 0
    solr_total_errors = 0
    # ...
    
    # Redis
    redis_total_queued = 0
    redis_queue_size = 0
    # ...
    
    # Общее
    total_records_parsed = 0
    last_errors = []  # Последние 10 ошибок
```

### Автоматическое обновление

Статистика обновляется автоматически при каждой операции:

```python
# При успешной отправке
g.stats.clickhouse_total_sent += 200
g.stats.clickhouse_last_success_time = datetime.now()

# При ошибке
g.stats.clickhouse_total_errors += 1
g.stats.clickhouse_last_error_time = datetime.now()
g.stats.clickhouse_last_error_msg = str(error)
g.stats.last_errors.append((datetime.now(), "ClickHouse", str(error)))
```

### Применение

- **Веб-панель** — читает `g.stats` для отображения
- **JSON API** — сериализует `g.stats` в JSON
- **Логи** — выводят счётчики из `g.stats`

---

## Диагностика проблем

### Быстрая проверка здоровья системы

```bash
# 1. Проверить статус службы
sudo systemctl status Nikita  # Linux
sc query Nikita  # Windows

# 2. Проверить веб-панель
curl -I http://localhost:8984/

# 3. Проверить API
curl -s http://localhost:8984/stats_api | jq '.clickhouse.connection_ok'

# 4. Проверить логи на ошибки
tail -50 /opt/Nikita/debug/Nikita.*.log | grep "✗"
```

### Типичные проблемы

#### 1. ClickHouse недоступен (🔴 на панели)

**Проверка:**
```bash
clickhouse-client --query "SELECT 1"
```

**Решение:**
```bash
sudo systemctl status clickhouse-server
sudo systemctl start clickhouse-server
```

#### 2. Базы 1С не обнаружены

**Проверка:**
```bash
curl -s http://localhost:8984/stats_api | jq '.databases'
```

**Решение:**
- Проверьте `C1_SRVINFO_PATH` в `.env`
- Проверьте права доступа к каталогам журналов

#### 3. Высокое количество ошибок

**Проверка:**
```bash
curl -s http://localhost:8984/stats_api | jq '.last_errors'
```

**Решение:**
- Смотрите детали ошибок в блоке "Последние ошибки" на веб-панели
- Анализируйте логи с `grep "✗"`

---

**Обновлено:** 2025-12-11  
**Версия:** 2.0.0  
**Источники:** Объединение MONITORING_QUICKSTART.md и MONITORING_IMPROVEMENTS.md

