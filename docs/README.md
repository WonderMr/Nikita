# Документация Nikita

Добро пожаловать в документацию проекта Nikita — высокопроизводительного сервиса парсинга и экспорта журналов регистрации 1С:Предприятие.

---

## Навигация по документации

### Быстрый старт

- **[README](../README.md)** — краткое введение в проект
- **[Быстрый старт](../QUICKSTART.md)** — установка за 5-10 минут (Linux/Windows)
- **[История изменений](../CHANGELOG.md)** — список изменений по версиям

### Для администраторов

#### Установка и конфигурация

- **[Установка](installation.md)** — подробное руководство по установке на Linux и Windows
- **[Конфигурация](configuration.md)** — полное описание параметров `.env` файла
- **[Скрипты](scripts.md)** — описание вспомогательных скриптов проекта

#### Эксплуатация

- **[Мониторинг](monitoring.md)** — веб-панель, JSON API, интеграция с Prometheus/Zabbix/Grafana
- **[Устранение неполадок](troubleshooting.md)** — FAQ, типичные проблемы и их решения

### Для разработчиков

#### Начало работы

- **[Руководство контрибьютора](development/contributing.md)** — как участвовать в разработке
- **[Стиль кода](development/code-style.md)** — правила оформления кода проекта
- **[Сборка дистрибутива](../BUILD.md)** — создание Windows-инсталлятора

#### Архитектура и внутреннее устройство

- **[Архитектура системы](architecture.md)** — компоненты, потоки данных, диаграммы
- **[Внутреннее устройство модулей](development/internals.md)** — описание основных модулей

#### Технические документы

- **[SQLite State Manager](technical/sqlite-state.md)** — хранение состояния парсинга
- **[Форматы журналов 1С](technical/log-formats.md)** — структура файлов `.lgf` и `.lgd`
- **[Схема ClickHouse](technical/clickhouse-schema.md)** — структура таблиц и оптимизация

---

## Структура документации

```
docs/
├── README.md                    # Этот файл (индекс)
├── installation.md              # Подробная установка
├── configuration.md             # Параметры .env
├── architecture.md              # Архитектура системы
├── monitoring.md                # Мониторинг
├── troubleshooting.md           # Устранение неполадок
├── scripts.md                   # Вспомогательные скрипты
├── development/                 # Для разработчиков
│   ├── contributing.md          # Руководство контрибьютора
│   ├── code-style.md            # Стиль кода
│   └── internals.md             # Внутреннее устройство
└── technical/                   # Технические детали
    ├── sqlite-state.md          # SQLite состояние
    ├── log-formats.md           # Форматы lgf/lgd
    └── clickhouse-schema.md     # Схема ClickHouse
```

---

## Дополнительные ресурсы

### Внешние ссылки

- [Документация 1С:Предприятие](https://its.1c.ru/db/metod8dev)
- [ClickHouse Documentation](https://clickhouse.com/docs/ru/)
- [Apache Solr Documentation](https://solr.apache.org/guide/)
- [Redis Documentation](https://redis.io/docs/)

### Сообщество

- **GitHub Issues** — сообщения об ошибках и запросы функций
- **Pull Requests** — ваш вклад в проект приветствуется!

---

## Помощь

Если вы не нашли ответ на свой вопрос:

1. Проверьте **[Устранение неполадок](troubleshooting.md)** — FAQ и типичные проблемы
2. Просмотрите **[GitHub Issues](https://github.com/your-org/Nikita/issues)** — возможно, кто-то уже сталкивался с этой проблемой
3. Создайте новый **[Issue](https://github.com/your-org/Nikita/issues/new)** с подробным описанием проблемы

---

**Обновлено:** 2025-12-11  
**Версия документации:** 2.0.0
