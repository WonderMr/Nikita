#!/bin/bash
# run_tests.sh - Запуск тестов Nikita на Linux

set -e # Остановить выполнение при ошибке

# 1. Настройка окружения
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# 2. Установка зависимостей
echo "[INFO] Installing test dependencies..."
pip install -r tests/requirements.test.txt > /dev/null 2>&1

# 3. Запуск тестов
echo "[INFO] Running tests..."
python3 -m unittest discover tests

echo "[INFO] Done."
