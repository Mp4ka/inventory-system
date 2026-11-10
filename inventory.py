"""Операции с инвентарными записями (CRUD + поиск + проверка ввода).

Модуль не зависит от интерфейса и файлового хранилища,
поэтому его функции удобно покрывать автоматическими тестами.
"""

# Поля, без которых запись нельзя сохранить.
REQUIRED_FIELDS = ("inventory_number", "type", "name", "room", "condition")

# Все поля карточки оборудования в фиксированном порядке.
ALL_FIELDS = (
    "inventory_number",
    "type",
    "name",
    "room",
    "condition",
    "date_received",
    "responsible",
)


def _normalize(record):
    """Возвращает копию записи с обрезанными пробелами и строковыми значениями."""
    return {
        field: str(record.get(field, "")).strip()
        for field in ALL_FIELDS
    }


def _validate(record):
    """Проверяет обязательные поля. Поднимает ValueError при некорректном вводе."""
    for field in REQUIRED_FIELDS:
        value = record.get(field)
        if value is None or str(value).strip() == "":
            raise ValueError(f"Поле '{field}' не может быть пустым")


def find_by_number(records, number):
    """Возвращает запись по инвентарному номеру или None."""
    target = (number or "").strip()
    for record in records:
        if str(record.get("inventory_number", "")).strip() == target:
            return record
    return None


def generate_inventory_number(records, prefix="INV-"):
    """Генерирует следующий свободный инвентарный номер вида INV-001."""
    max_num = 0
    for record in records:
        num = str(record.get("inventory_number", ""))
        suffix = num[len(prefix):] if num.startswith(prefix) else ""
        if suffix.isdigit():
            max_num = max(max_num, int(suffix))
    return f"{prefix}{max_num + 1:03d}"


def add_record(records, record):
    """Добавляет запись. Отклоняет пустые обязательные поля и повтор номера."""
    _validate(record)
    normalized = _normalize(record)
    number = normalized["inventory_number"]
    if find_by_number(records, number) is not None:
        raise ValueError(f"Запись с инвентарным номером '{number}' уже существует")
    records.append(normalized)
    return normalized


def list_records(records):
    """Возвращает копию списка всех записей."""
    return list(records)


def search(records, number=None, room=None, type_=None, condition=None):
    """Ищет записи по любому сочетанию полей (регистр не учитывается)."""
    result = []
    for record in records:
        if number and str(record.get("inventory_number", "")).strip().lower() != number.strip().lower():
            continue
        if room and str(record.get("room", "")).strip().lower() != room.strip().lower():
            continue
        if type_ and str(record.get("type", "")).strip().lower() != type_.strip().lower():
            continue
        if condition and str(record.get("condition", "")).strip().lower() != condition.strip().lower():
            continue
        result.append(record)
    return result


def update_record(records, number, changes):
    """Изменяет поля записи по номеру. Не позволяет создать повтор номера."""
    record = find_by_number(records, number)
    if record is None:
        raise ValueError(f"Запись с номером '{number}' не найдена")
    new_number = str(changes.get("inventory_number", number)).strip()
    if new_number != str(record["inventory_number"]).strip():
        if find_by_number(records, new_number) is not None:
            raise ValueError(f"Запись с инвентарным номером '{new_number}' уже существует")
    for field in ALL_FIELDS:
        if field in changes:
            record[field] = str(changes[field]).strip()
    return record


def delete_record(records, number, confirmed=True):
    """Удаляет запись. Если подтверждение не дано — возвращает False без изменений."""
    if not confirmed:
        return False
    record = find_by_number(records, number)
    if record is None:
        raise ValueError(f"Запись с номером '{number}' не найдена")
    records.remove(record)
    return True
