"""Хранение данных в JSON: загрузка и сохранение с обработкой ошибок."""

import json
import os


def load_data(path):
    """Читает список записей из JSON-файла.

    Безопасно обрабатывает три ситуации:
    - файл отсутствует -> возвращается пустой список;
    - файл повреждён (некорректный JSON) -> пустой список;
    - файл не является списком -> пустой список.
    """
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return []
    return data if isinstance(data, list) else []


def save_data(path, records):
    """Сохраняет список записей в JSON-файл (создаёт каталог при необходимости)."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    return path
