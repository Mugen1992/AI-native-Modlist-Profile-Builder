"""Настройки для тестов."""

import sys
from pathlib import Path

# Добавляем корень репозитория в sys.path, чтобы импорты работали без установки пакета.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
