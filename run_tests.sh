#!/bin/bash
# Copyright (C) 2025 Nikita Development Team
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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

# 3. Запуск тестов с детализацией
echo "[INFO] Running tests..."
# Добавлен флаг -v для подробного вывода (verbose)
python3 -m unittest discover tests -v

echo "[INFO] Done."


