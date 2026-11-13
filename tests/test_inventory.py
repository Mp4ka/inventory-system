"""Автоматические тесты операций с инвентарём и файлового хранения.

Запуск:
    python -m pytest
    python tests/test_inventory.py   (запуск файла напрямую)
"""

import os
import sys

# Корень проекта в sys.path, чтобы файл запускался и напрямую из IDE.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pytest

import inventory
import storage


@pytest.fixture
def records():
    return [
        {
            "inventory_number": "INV-001",
            "type": "ПК",
            "name": "Системный блок",
            "room": "301",
            "condition": "исправно",
        },
        {
            "inventory_number": "INV-002",
            "type": "Монитор",
            "name": "Монитор Dell",
            "room": "302",
            "condition": "исправно",
        },
    ]


def valid_record(number="INV-010", **overrides):
    data = {
        "inventory_number": number,
        "type": "ПК",
        "name": "Компьютер",
        "room": "301",
        "condition": "исправно",
    }
    data.update(overrides)
    return data


# --- Добавление ---

def test_add_valid_record(records):
    inventory.add_record(records, valid_record())
    assert inventory.find_by_number(records, "INV-010") is not None


def test_add_duplicate_number_rejected(records):
    with pytest.raises(ValueError):
        inventory.add_record(records, valid_record(number="INV-001"))


def test_add_empty_required_field_rejected(records):
    with pytest.raises(ValueError):
        inventory.add_record(records, valid_record(name=""))


def test_add_empty_number_rejected(records):
    with pytest.raises(ValueError):
        inventory.add_record(records, valid_record(number=""))


# --- Поиск ---

def test_search_by_existing_number(records):
    result = inventory.search(records, number="INV-001")
    assert len(result) == 1
    assert result[0]["name"] == "Системный блок"


def test_search_unknown_number_empty(records):
    assert inventory.search(records, number="INV-999") == []


def test_search_by_room(records):
    result = inventory.search(records, room="301")
    assert len(result) == 1
    assert result[0]["inventory_number"] == "INV-001"


def test_search_by_condition(records):
    result = inventory.search(records, condition="исправно")
    assert len(result) == 2


# --- Изменение ---

def test_update_existing_record(records):
    inventory.update_record(records, "INV-001", {"room": "305", "condition": "требует ремонта"})
    record = inventory.find_by_number(records, "INV-001")
    assert record["room"] == "305"
    assert record["condition"] == "требует ремонта"


def test_update_missing_record_raises(records):
    with pytest.raises(ValueError):
        inventory.update_record(records, "INV-999", {"room": "305"})


def test_update_to_duplicate_number_rejected(records):
    with pytest.raises(ValueError):
        inventory.update_record(records, "INV-001", {"inventory_number": "INV-002"})


# --- Удаление ---

def test_delete_existing_record(records):
    assert inventory.delete_record(records, "INV-001") is True
    assert inventory.find_by_number(records, "INV-001") is None


def test_delete_cancelled(records):
    assert inventory.delete_record(records, "INV-001", confirmed=False) is False
    assert inventory.find_by_number(records, "INV-001") is not None


def test_delete_missing_record_raises(records):
    with pytest.raises(ValueError):
        inventory.delete_record(records, "INV-999")


# --- Генерация номера ---

def test_generate_inventory_number(records):
    assert inventory.generate_inventory_number(records) == "INV-003"


# --- Хранение ---

def test_save_and_load_roundtrip(tmp_path, records):
    path = os.path.join(tmp_path, "data", "inventory.json")
    storage.save_data(path, records)
    loaded = storage.load_data(path)
    assert loaded == records


def test_load_missing_file_returns_empty(tmp_path):
    assert storage.load_data(os.path.join(tmp_path, "nope.json")) == []


def test_load_corrupt_json_returns_empty(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{ это не JSON", encoding="utf-8")
    assert storage.load_data(str(path)) == []


def test_load_empty_file_returns_empty(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text("", encoding="utf-8")
    assert storage.load_data(str(path)) == []


# --- Спринт 2: правила заполнения (проверка состояния) ---

def test_add_invalid_condition_rejected(records):
    with pytest.raises(ValueError):
        inventory.add_record(records, valid_record(condition="сломано"))


def test_add_allowed_condition_accepted(records):
    inventory.add_record(records, valid_record(number="INV-020", condition="требует ремонта"))
    assert inventory.find_by_number(records, "INV-020") is not None


def test_allowed_conditions_constant():
    assert set(inventory.ALLOWED_CONDITIONS) == {"исправно", "требует ремонта", "списано"}


# --- Спринт 3: поиск и изменение ---

def test_search_partial_number(records):
    result = inventory.search(records, number="001")
    assert len(result) == 1
    assert result[0]["inventory_number"] == "INV-001"


def test_search_partial_room(records):
    result = inventory.search(records, room="30")
    assert len(result) == 2


def test_update_invalid_condition_rejected(records):
    with pytest.raises(ValueError):
        inventory.update_record(records, "INV-001", {"condition": "сломано"})


def test_update_valid_condition_accepted(records):
    inventory.update_record(records, "INV-001", {"condition": "списано"})
    assert inventory.find_by_number(records, "INV-001")["condition"] == "списано"


# --- Спринт 4: файловое хранение ---

def test_save_data_creates_directory(tmp_path):
    path = os.path.join(tmp_path, "nested", "dir", "inventory.json")
    storage.save_data(path, [{"inventory_number": "INV-001"}])
    assert os.path.exists(path)


def test_load_non_list_json_returns_empty(tmp_path):
    path = tmp_path / "obj.json"
    path.write_text('{"a": 1}', encoding="utf-8")
    assert storage.load_data(str(path)) == []


def test_save_and_load_unicode(tmp_path):
    path = os.path.join(tmp_path, "data", "inventory.json")
    records = [{"inventory_number": "INV-001", "name": "Клавиатура «Logitech»", "condition": "исправно"}]
    storage.save_data(path, records)
    assert storage.load_data(path) == records


# --- Спринт 5: устойчивость (регрессия) ---

def test_update_empty_number_rejected(records):
    with pytest.raises(ValueError):
        inventory.update_record(records, "INV-001", {"inventory_number": ""})


def test_update_empty_required_field_rejected(records):
    with pytest.raises(ValueError):
        inventory.update_record(records, "INV-001", {"name": ""})


def test_update_keeps_record_unchanged_on_error(records):
    before = dict(inventory.find_by_number(records, "INV-001"))
    with pytest.raises(ValueError):
        inventory.update_record(records, "INV-001", {"name": ""})
    assert inventory.find_by_number(records, "INV-001") == before


# --- Спринт 6: оформление и финальная сборка ---

def test_render_card_contains_fields():
    import main
    record = {
        "inventory_number": "INV-777",
        "type": "Принтер",
        "name": "HP LaserJet",
        "room": "305",
        "condition": "списано",
    }
    text = "\n".join(main.render_card(record))
    assert "INV-777" in text
    assert "Принтер" in text
    assert "305" in text
    assert "списано" in text


if __name__ == "__main__":
    raise SystemExit(pytest.main([os.path.abspath(__file__), "-v"]))
