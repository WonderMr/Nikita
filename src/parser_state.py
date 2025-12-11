# -*- coding: utf-8 -*-
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

"""
Nikita.parser.state - Модуль доступа к состоянию парсера

Этот файл предоставляет удобный доступ к системе управления состоянием парсера.
Состояние хранится в SQLite базе данных: Nikita.parser.state.db

Использование:
    from Nikita.parser.state import state_manager
    
    # Получить состояние файла
    state = state_manager.get_file_state("filename.lgp")
    
    # Обновить состояние
    state_manager.update_file_state("filename.lgp", filesize=1000, filesizeread=500)
    
    # Залогировать отправленный блок
    state_manager.log_committed_block("filename.lgp", offset_start=0, offset_end=1000, data_records=[...])
"""

from src.state_manager import state_manager

__all__                                                     =   ['state_manager']

if __name__ == '__main__':
    print("Nikita Parser State Manager")
    print(f"Database path: {state_manager.db_path}")
    print("\nДоступные методы:")
    print("  - get_file_state(filename) -> dict или None")
    print("  - update_file_state(filename, filesize, filesizeread)")
    print("  - log_committed_block(filename, offset_start, offset_end, data_records)")

