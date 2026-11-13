"""Консольное приложение «Система учёта инвентаря компьютерных классов».

Запуск: python main.py
Логика операций находится в inventory.py, хранение — в storage.py.
"""

import os

import inventory
import storage

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "inventory.json")


def save(records):
    """Сохраняет текущее состояние инвентаря в файл."""
    storage.save_data(DATA_PATH, records)


def print_record(record):
    """Выводит карточку оборудования в одну строку."""
    print(
        f"[{record['inventory_number']}] {record['type']} — {record['name']} "
        f"| кабинет {record['room']} | {record['condition']}"
        + (f" | с {record['date_received']}" if record.get("date_received") else "")
        + (f" | отв.: {record['responsible']}" if record.get("responsible") else "")
    )


def input_record():
    """Собирает данные карточки с клавиатуры."""
    print("Заполните поля карточки оборудования.")
    return {
        "inventory_number": input("Инвентарный номер: ").strip(),
        "type": input("Тип (ПК/монитор/принтер и др.): ").strip(),
        "name": input("Наименование: ").strip(),
        "room": input("Кабинет: ").strip(),
        "condition": input("Состояние (исправно/требует ремонта/списано): ").strip(),
        "date_received": input("Дата поступления (необязательно): ").strip(),
        "responsible": input("Ответственное лицо (необязательно): ").strip(),
    }


def show_all(records):
    if not records:
        print("Инвентарь пуст.")
        return
    print(f"Всего записей: {len(records)}")
    for record in records:
        print_record(record)


def add(records):
    record = input_record()
    if not record["inventory_number"]:
        record["inventory_number"] = inventory.generate_inventory_number(records)
        print(f"Номер сгенерирован автоматически: {record['inventory_number']}")
    try:
        inventory.add_record(records, record)
        save(records)
        print("Запись добавлена.")
    except ValueError as e:
        print(f"Ошибка: {e}")


def edit(records):
    number = input("Инвентарный номер записи для изменения: ").strip()
    record = inventory.find_by_number(records, number)
    if record is None:
        print("Запись не найдена.")
        return
    print("Введите новые значения (пустое поле — оставить прежним).")
    changes = {}
    for field in inventory.ALL_FIELDS:
        value = input(f"{field} [{record[field]}]: ").strip()
        if value:
            changes[field] = value
    try:
        inventory.update_record(records, number, changes)
        save(records)
        print("Запись изменена.")
    except ValueError as e:
        print(f"Ошибка: {e}")


def delete(records):
    number = input("Инвентарный номер записи для удаления: ").strip()
    confirm = input("Удалить запись? (да/нет): ").strip().lower()
    try:
        deleted = inventory.delete_record(records, number, confirmed=confirm in ("да", "yes", "y"))
        if deleted:
            save(records)
            print("Запись удалена.")
        else:
            print("Удаление отменено.")
    except ValueError as e:
        print(f"Ошибка: {e}")


def search(records):
    print("Оставьте поля пустыми, чтобы не учитывать их при поиске.")
    number = input("Номер: ").strip()
    room = input("Кабинет: ").strip()
    type_ = input("Тип: ").strip()
    condition = input("Состояние: ").strip()
    found = inventory.search(records, number=number or None, room=room or None,
                             type_=type_ or None, condition=condition or None)
    if not found:
        print("Не найдено.")
        return
    print(f"Найдено записей: {len(found)}")
    for record in found:
        print_record(record)


MENU = """
Меню:
1. Показать оборудование
2. Добавить запись
3. Изменить запись
4. Удалить запись
5. Поиск
0. Сохранить и выйти
"""


def main():
    records = storage.load_data(DATA_PATH)
    print("Система учёта инвентаря компьютерных классов")
    while True:
        print(MENU)
        choice = input("Выберите пункт: ").strip()
        if choice == "1":
            show_all(records)
        elif choice == "2":
            add(records)
        elif choice == "3":
            edit(records)
        elif choice == "4":
            delete(records)
        elif choice == "5":
            search(records)
        elif choice == "0":
            storage.save_data(DATA_PATH, records)
            print("Данные сохранены. До свидания!")
            break
        else:
            print("Неизвестная команда, попробуйте ещё раз.")


if __name__ == "__main__":
    main()
