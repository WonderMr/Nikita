# Journal2Ct / Nikita

Высокопроизводительный сервис парсинга и экспорта журналов событий 1С:Предприятие.
Поддерживает дуальный экспорт в **Solr** (для быстрого поиска) и **ClickHouse** (для аналитики), с буферизацией через **Redis** для надежности.

## Возможности

*   **Высокая производительность**: Многопоточный парсинг логов 1С.
*   **Поддержка форматов**: Работает как со старым текстовым форматом (`.lgp`), так и с новым SQLite (`.lgd`).
*   **Двойное хранилище**:
    *   **Solr**: Полнотекстовый поиск.
    *   **ClickHouse**: Колоночное хранение для аналитических запросов и длительного хранения.
*   **Надежность**: Встроенная очередь **Redis** гарантирует отсутствие потери данных при обслуживании баз данных или пиковых нагрузках.
*   **Кроссплатформенность**: Работает как служба **Windows** или демон **Linux**.
*   **Конфигурация**: Гибкая настройка через переменные окружения или файл `.ini`. Безопасное хранение секретов (поддержка `.env`).

## Требования

*   **Python 3.10+**
*   **Redis** (Рекомендуется для продакшна)
*   **Solr** (Опционально, для поиска)
*   **ClickHouse** (Опционально, для аналитики)
*   **Журналы сервера 1С:Предприятие** (доступные через файловую систему)

## Установка

1.  Клонируйте репозиторий:
    ```bash
    git clone https://github.com/your-repo/Nikita.git
    cd Nikita
    ```

2.  Создайте виртуальное окружение и установите зависимости:
    ```bash
    python -m venv venv
    # Linux
    source venv/bin/activate
    # Windows
    .\venv\Scripts\activate
    
    pip install -r requirments.lin  # Linux
    # или
    pip install -r requirments.win  # Windows
    ```

## Конфигурация

Приложение считывает настройки из переменных окружения и файла `.env`. Файл `.ini` больше не используется.

1.  Скопируйте пример конфигурации:
    ```bash
    cp env.example .env
    ```

2.  Отредактируйте `.env`. Вам необходимо указать настройки баз данных 1С:

    ```ini
    # 1C Settings
    # IBASE_N - это префикс для N-ной базы (0, 1, 2...)
    
    # База #0
    IBASE_0=PROD_ZUP_LOCAL
    IBASE_0_JR=/home/usr1cv8/.1cv8/1C/1cv8/reg_1541/uuid-uuid-uuid/1Cv8Log
    IBASE_0_FORMAT=lgf  # lgf (старый) или lgd (sqlite)

    # База #1
    IBASE_1=ANOTHER_BASE
    IBASE_1_JR=/path/to/another/log
    IBASE_1_FORMAT=lgd
    
    # Настройки ClickHouse
    CLICKHOUSE_ENABLED=True
    CLICKHOUSE_HOST=localhost
    CLICKHOUSE_PORT=9000
    CLICKHOUSE_USER=default
    CLICKHOUSE_PASSWORD=secret
    CLICKHOUSE_DATABASE=zhr1c

    # Настройки Redis
    REDIS_ENABLED=True
    REDIS_HOST=127.0.0.1
    REDIS_PORT=6379
    
    # Настройки Solr
    SOLR_ENABLED=False
    ```

3.  Запустите приложение. Оно автоматически создаст базу данных и таблицы в ClickHouse при первом получении данных.

## Использование / Развертывание

### Консольный режим (Отладка)

Запуск напрямую в консоли для просмотра логов и отладочной информации:

```bash
python Nikita.py console
```

### Linux (Systemd)

1.  Создайте unit-файл `/etc/systemd/system/journal2ct.service`:

    ```ini
    [Unit]
    Description=1C Journal Parser Service
    After=network.target redis.service

    [Service]
    Type=simple
    User=youruser
    WorkingDirectory=/opt/Nikita
    ExecStart=/opt/Nikita/venv/bin/python /opt/Nikita/Nikita.py console
    Restart=always
    EnvironmentFile=/opt/Nikita/.env

    [Install]
    WantedBy=multi-user.target
    ```

2.  Активируйте и запустите:
    ```bash
    sudo systemctl enable journal2ct
    sudo systemctl start journal2ct
    ```

### Windows Service

1.  Установка службы (требуются права Администратора):
    ```powershell
    python Nikita.py install
    ```

2.  Запуск службы:
    ```powershell
    python Nikita.py start
    ```

3.  Удаление службы:
    ```powershell
    python Nikita.py remove
    ```

## Архитектура

1.  **Parser Threads (Потоки парсера)**: Мониторят каталоги логов 1С (`.lgp`/`.lgd`). При появлении новых данных они парсятся и отправляются в список **Redis**.
2.  **Redis**: Выступает в роли персистентного буфера. Если ClickHouse/Solr недоступны, очередь растет, но данные сохраняются.
3.  **Sender Thread (Поток отправителя)**: Непрерывно забирает данные из Redis и пакетами отправляет их в **ClickHouse** и **Solr**.

## Устранение неполадок

*   **Логи**: Проверяйте каталог `debug/` для детальных логов.
*   **Redis**: Убедитесь, что Redis запущен, если `REDIS_ENABLED=True`.
*   **Права доступа**: Пользователь, от которого запущена служба, должен иметь права на чтение файлов логов 1С.
