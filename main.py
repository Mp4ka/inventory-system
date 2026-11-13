"""Консольное приложение «Система учёта инвентаря компьютерных классов».

Запуск: python main.py
Логика операций находится в inventory.py, хранение — в storage.py.
"""

import os
import sys

import inventory
import storage

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "inventory.json")


# --- Цвета и оформление -----------------------------------------------------

class C:
    """ANSI-коды цветов."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


# Если вывод перенаправлен (не терминал), цвета отключаем, чтобы не было мусора.
if not sys.stdout.isatty():
    for _name in ("RESET", "BOLD", "DIM", "RED", "GREEN", "YELLOW",
                  "BLUE", "MAGENTA", "CYAN", "WHITE", "GRAY"):
        setattr(C, _name, "")


def _can_encode(text):
    """Проверяет, можно ли вывести символы в текущей кодировке stdout."""
    enc = sys.stdout.encoding or "utf-8"
    try:
        text.encode(enc)
        return True
    except (UnicodeEncodeError, LookupError):
        return False


# Рамка из псевдографики, если кодировка её поддерживает; иначе — ASCII.
if _can_encode("┌┐└┘─│"):
    TL, TR, BL, BR, H, V = "┌", "┐", "└", "┘", "─", "│"
    DOT = " · "
else:
    TL = TR = BL = BR = "+"
    H, V = "-", "|"
    DOT = " | "


# Цвет состояния оборудования.
CONDITION_COLORS = {
    "исправно": C.GREEN,
    "требует ремонта": C.YELLOW,
    "списано": C.RED,
}


def _enable_ansi():
    """Включает обработку ANSI-кодов в консоли Windows."""
    if os.name != "nt":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def _pad(plain, colored, width):
    """Дополняет цветную строку пробелами до ширины plain-строки."""
    return colored + " " * max(0, width - len(plain))


def _card_parts(record):
    """Возвращает три текстовые строки карточки (без цветов)."""
    header = f"{record['type']}  {record['inventory_number']}"
    name = str(record["name"])
    line = f"Кабинет {record['room']}{DOT}{record['condition']}"
    if record.get("date_received"):
        line += f"{DOT}с {record['date_received']}"
    if record.get("responsible"):
        line += f"{DOT}отв.: {record['responsible']}"
    return header, name, line


def render_card(record):
    """Возвращает карточку оборудования в рамке без цветов (для тестов)."""
    header, name, line = _card_parts(record)
    width = max(len(header), len(name), len(line), 42)
    return [
        TL + H * (width + 2) + TR,
        V + " " + header.ljust(width) + " " + V,
        V + " " + name.ljust(width) + " " + V,
        V + " " + line.ljust(width) + " " + V,
        BL + H * (width + 2) + BR,
    ]


def print_card(record):
    """Печатает карточку: рамка, подсветка типа и состояния."""
    header, name, line = _card_parts(record)
    width = max(len(header), len(name), len(line), 42)
    cond = str(record["condition"])
    cond_color = CONDITION_COLORS.get(cond.lower(), C.WHITE)

    header_c = f"{C.BOLD}{C.CYAN}{record['type']}{C.RESET}  {C.GRAY}{record['inventory_number']}{C.RESET}"
    name_c = f"{C.WHITE}{name}{C.RESET}"
    line_c = f"Кабинет {C.WHITE}{record['room']}{C.RESET}{DOT}{cond_color}{cond}{C.RESET}"
    if record.get("date_received"):
        line_c += f"{DOT}с {record['date_received']}"
    if record.get("responsible"):
        line_c += f"{DOT}отв.: {record['responsible']}"

    print(C.GRAY + TL + H * (width + 2) + TR + C.RESET)
    print(C.GRAY + V + " " + C.RESET + _pad(header, header_c, width) + C.GRAY + " " + V + C.RESET)
    print(C.GRAY + V + " " + C.RESET + _pad(name, name_c, width) + C.GRAY + " " + V + C.RESET)
    print(C.GRAY + V + " " + C.RESET + _pad(line, line_c, width) + C.GRAY + " " + V + C.RESET)
    print(C.GRAY + BL + H * (width + 2) + BR + C.RESET)


# --- Ввод с проверкой и предложением исправить ------------------------------

def ask_required(prompt, label):
    """Спрашивает обязательное поле и сразу предлагает исправить пустое."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print(f"{C.RED}Поле «{label}» не может быть пустым. Введите ещё раз.{C.RESET}")


def ask_condition():
    """Спрашивает состояние и сразу переспрашивает недопустимое."""
    allowed = " / ".join(inventory.ALLOWED_CONDITIONS)
    while True:
        value = input(f"Состояние ({allowed}): ").strip()
        if value.lower() in inventory.ALLOWED_CONDITIONS:
            return value
        print(
            f"{C.RED}Недопустимое состояние «{value}». "
            f"Введите одно из: {', '.join(inventory.ALLOWED_CONDITIONS)}.{C.RESET}"
        )


def ask_retry(message):
    """Спрашивает, хочет ли пользователь исправить ошибку."""
    answer = input(f"{C.YELLOW}{message} (да/нет): {C.RESET}").strip().lower()
    return answer in ("да", "yes", "y", "1")


def input_record():
    """Собирает данные карточки с клавиатуры, проверяя поля сразу."""
    print(f"{C.BOLD}Заполните поля карточки оборудования.{C.RESET}")
    return {
        "inventory_number": input("Инвентарный номер (пусто — сгенерировать): ").strip(),
        "type": ask_required("Тип (ПК/монитор/принтер и др.): ", "тип"),
        "name": ask_required("Наименование: ", "наименование"),
        "room": ask_required("Кабинет: ", "кабинет"),
        "condition": ask_condition(),
        "date_received": input("Дата поступления (необязательно): ").strip(),
        "responsible": input("Ответственное лицо (необязательно): ").strip(),
    }


# --- Операции ---------------------------------------------------------------

def save(records):
    """Сохраняет текущее состояние инвентаря в файл."""
    storage.save_data(DATA_PATH, records)


def show_all(records):
    if not records:
        print(f"{C.YELLOW}Инвентарь пуст.{C.RESET}")
        return
    print(f"{C.BOLD}Всего записей: {len(records)}{C.RESET}")
    for record in records:
        print_card(record)


def add(records):
    while True:
        record = input_record()
        if not record["inventory_number"]:
            record["inventory_number"] = inventory.generate_inventory_number(records)
            print(f"{C.CYAN}Номер сгенерирован автоматически: {record['inventory_number']}{C.RESET}")
        try:
            inventory.add_record(records, record)
            save(records)
            print(f"{C.GREEN}Запись добавлена.{C.RESET}")
            return
        except ValueError as e:
            print(f"{C.RED}Ошибка: {e}{C.RESET}")
            if not ask_retry("Исправить запись?"):
                return


def edit(records):
    while True:
        number = input("Инвентарный номер записи для изменения: ").strip()
        record = inventory.find_by_number(records, number)
        if record is None:
            print(f"{C.RED}Запись не найдена.{C.RESET}")
            if not ask_retry("Попробовать другой номер?"):
                return
            continue
        print(f"{C.BOLD}Введите новые значения (пустое поле — оставить прежним).{C.RESET}")
        changes = {}
        for field in inventory.ALL_FIELDS:
            value = input(f"{field} [{record[field]}]: ").strip()
            if value:
                changes[field] = value
        try:
            inventory.update_record(records, number, changes)
            save(records)
            print(f"{C.GREEN}Запись изменена.{C.RESET}")
            return
        except ValueError as e:
            print(f"{C.RED}Ошибка: {e}{C.RESET}")
            if not ask_retry("Исправить?"):
                return


def delete(records):
    while True:
        number = input("Инвентарный номер записи для удаления: ").strip()
        record = inventory.find_by_number(records, number)
        if record is None:
            print(f"{C.RED}Запись не найдена.{C.RESET}")
            if not ask_retry("Попробовать другой номер?"):
                return
            continue
        confirm = input(f"Удалить «{record['name']}»? (да/нет): ").strip().lower()
        if confirm not in ("да", "yes", "y"):
            print(f"{C.YELLOW}Удаление отменено.{C.RESET}")
            return
        inventory.delete_record(records, number, confirmed=True)
        save(records)
        print(f"{C.GREEN}Запись удалена.{C.RESET}")
        return


def search(records):
    print(f"{C.BOLD}Оставьте поля пустыми, чтобы не учитывать их при поиске.{C.RESET}")
    number = input("Номер: ").strip()
    room = input("Кабинет: ").strip()
    type_ = input("Тип: ").strip()
    condition = input("Состояние: ").strip()
    found = inventory.search(records, number=number or None, room=room or None,
                             type_=type_ or None, condition=condition or None)
    if not found:
        print(f"{C.YELLOW}Ничего не найдено.{C.RESET}")
        return
    print(f"{C.GREEN}Найдено записей: {len(found)}{C.RESET}")
    for record in found:
        print_card(record)


def show_menu():
    print(f"\n{C.BOLD}{C.BLUE}Меню:{C.RESET}")
    for key, label in [
        ("1", "Показать оборудование"),
        ("2", "Добавить запись"),
        ("3", "Изменить запись"),
        ("4", "Удалить запись"),
        ("5", "Поиск"),
        ("0", "Сохранить и выйти"),
    ]:
        print(f"  {C.CYAN}{key}{C.RESET}) {label}")


def main():
    _enable_ansi()
    records = storage.load_data(DATA_PATH)
    print(f"{C.BOLD}{C.CYAN}Система учёта инвентаря компьютерных классов{C.RESET}")
    print(f"{C.GRAY}Записей в базе: {len(records)}{C.RESET}")
    while True:
        show_menu()
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
            print(f"{C.GREEN}Данные сохранены. До свидания!{C.RESET}")
            break
        else:
            print(f"{C.RED}Неизвестная команда, попробуйте ещё раз.{C.RESET}")


if __name__ == "__main__":
    main()
