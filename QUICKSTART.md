# Быстрый старт Nikita на Linux

## Установка за 5 команд

```bash
# 1. Установка в /opt/Nikita
sudo git clone https://github.com/your-repo/Nikita.git /opt/Nikita
cd /opt/Nikita

# 2. Создание виртуального окружения и установка зависимостей
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirments.lin

# 3. Копирование и настройка конфигурации
sudo cp env.example .env
sudo nano .env  # Отредактируйте: укажите пути к базам 1С, настройки ClickHouse

# 4. Установка systemd service через симлинк
sudo ln -s /opt/Nikita/Nikita.service /etc/systemd/system/Nikita.service
sudo systemctl daemon-reload

# 5. Запуск службы
sudo systemctl enable Nikita
sudo systemctl start Nikita
```

## Проверка работы

```bash
# Статус службы
sudo systemctl status Nikita

# Логи в реальном времени
sudo journalctl -u Nikita -f

# Веб-панель мониторинга
# Откройте в браузере: http://your-server:8984/
```

## Управление службой

```bash
# Перезапуск
sudo systemctl restart Nikita

# Остановка
sudo systemctl stop Nikita

# Отключение автозапуска
sudo systemctl disable Nikita

# Просмотр последних 100 строк логов
sudo journalctl -u Nikita -n 100
```

## Важные замечания

1. **Пользователь usr1cv8**: Служба запускается от пользователя `usr1cv8`. Если у вас другой пользователь, отредактируйте `Nikita.service` перед созданием симлинка:
   ```bash
   sudo nano /opt/Nikita/Nikita.service
   # Измените строки User= и Group=
   ```

2. **Права доступа**: Пользователь службы должен иметь доступ к каталогам журналов 1С:
   ```bash
   sudo usermod -a -G usr1cv8 nikita-user
   ```

3. **ClickHouse**: Убедитесь, что ClickHouse запущен:
   ```bash
   sudo systemctl status clickhouse-server
   ```

4. **Файл .env**: Обязательно настройте `.env` перед запуском. Минимальная конфигурация:
   - `C1_SRVINFO_PATH` - путь к базам 1С для автодетекта
   - `CLICKHOUSE_HOST`, `CLICKHOUSE_PORT` - подключение к ClickHouse
   - `HTTP_LISTEN_PORT` - порт веб-панели (по умолчанию 8984)

## Устранение проблем

### Служба не запускается
```bash
# Смотрим подробные логи
sudo journalctl -u Nikita -n 50 --no-pager

# Проверяем конфигурацию
/opt/Nikita/venv/bin/python /opt/Nikita/Nikita.py console
# Если видим ошибки - исправляем в .env
```

### Базы 1С не обнаружены
```bash
# Проверьте путь C1_SRVINFO_PATH в .env
# Проверьте права доступа к каталогам
ls -la /home/usr1cv8/.1cv8/1C/1cv8/
```

### Не открывается веб-панель
```bash
# Проверьте, что служба запущена
sudo systemctl status Nikita

# Проверьте настройку порта в .env
grep HTTP_LISTEN_PORT /opt/Nikita/.env

# Проверьте firewall
sudo ss -tlnp | grep 8984
```

## Полная документация

Смотрите `docs/README.md` для подробной информации о настройке, архитектуре и возможностях.
