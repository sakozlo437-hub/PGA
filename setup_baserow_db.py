#!/usr/bin/env python3
"""
Скрипт быстрой настройки базы данных Baserow.
Запускает автоматическое создание таблиц и полей.

Использование:
    python setup_baserow_db.py

Требуемые переменные окружения:
    - BASEROW_TOKEN
    - BASEROW_DATABASE_ID
"""

import sys
import os

# Добавляем src в путь импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from setup.baserow_setup import main

if __name__ == "__main__":
    main()
