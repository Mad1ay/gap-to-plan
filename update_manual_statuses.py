#!/usr/bin/env python3
"""
Manual status update script based on actual project progress
Updates backlog items with real statuses and explodes them into activity stages
"""

import pandas as pd
from datetime import datetime

INPUT_FILE = 'Final_Integrated_Plan_v2.csv'
OUTPUT_FILE = 'Final_Integrated_Plan_v3.csv'

# Manual status updates based on actual progress
MANUAL_UPDATES = {
    # DONE items (базові можливості системи)
    "Розгорнути тестове середовище Odoo. Встановити потрібні базові модулі (СRM, Склад, Інвойси, Співробітники, Контакти, Відвідуваність, Продажі, Закупки, Виробництво, Веб-сайт)": {
        "status": "Виконано",
        "comment": "Тестове середовище розгорнуто",
        "work_type": "Налаштування"
    },
    "Перевірка унікальності логіну користувача при створенні доступу до системи.": {
        "status": "Виконано",
        "comment": "Базова функція системи",
        "work_type": "Налаштування"
    },
    "Створити демонстраційні підрозділи в системі": {
        "status": "Виконано",
        "comment": "Тестові підрозділи створено",
        "work_type": "Налаштування"
    },
    "Створення, пошук, перегляд та редагування основних даних профілю (ПІБ, посада, відділ, контакти).": {
        "status": "Виконано",
        "comment": "Базова функція системи",
        "work_type": "Налаштування"
    },
    "Зберігання та управління інформацією про трудові договори співробітників (номер, дати, скан-копії).": {
        "status": "Виконано",
        "comment": "Базова функція системи",
        "work_type": "Налаштування"
    },
    "Відстеження кваліфікації, сертифікатів та навичок співробітників.": {
        "status": "Виконано",
        "comment": "Базова функція системи",
        "work_type": "Налаштування"
    },

    # IN PROGRESS items
    "Розгорнути stage Odoo. Робота по підтримці та адмініструванні середовища": {
        "status": "В роботі",
        "comment": "Stage середовище в процесі налаштування",
        "work_type": "Налаштування"
    },
    "Зберігання записів про час приходу/уходу (check-in/check-out) та розрахунок відпрацьованих годин.": {
        "status": "В роботі",
        "comment": "Заплановано на 4 спринт",
        "work_type": "Налаштування"
    },
    "Ручне створення, редагування та видалення записів відвідуваності в табелі співробітника.": {
        "status": "В роботі",
        "comment": "Заплановано на 4 спринт",
        "work_type": "Налаштування"
    },

    # DONE without documentation
    "Розробити функціонал \"Сімейних карт\", що дозволить кільком членам родини користуватися спільним бонусним/депозитним рахунком.": {
        "status": "Виконано",
        "comment": "Реалізовано, потрібна документація",
        "work_type": "Розробка"
    },
    "Призначення послуг, які може виконувати співробітник, на основі його посади з можливістю ручного коригування.": {
        "status": "Виконано",
        "comment": "Реалізовано, немає документації",
        "work_type": "Розробка"
    },

    # NOT RELEVANT
    "Прив'язка співробітника до кабінету (приміщення) для організації робочого простору.": {
        "status": "Скасовано",
        "comment": "Неактуально для проєкту",
        "work_type": "Backlog"
    },
    "Створення та управління плановими робочими графіками співробітників (зміни, вихідні, відпустки).": {
        "status": "Скасовано",
        "comment": "Неактуально для проєкту",
        "work_type": "Backlog"
    }
}

# Activity explosion rules for backlog items
ACTIVITY_RULES = {
    "Розробка": {
        "activities": [
            {"type": "Моделювання", "percentage": 0.1, "order": 1},
            {"type": "Розробка", "percentage": 0.6, "order": 2},
            {"type": "Налаштування", "percentage": 0.2, "order": 3},
            {"type": "Навчання", "percentage": 0.1, "order": 4}
        ]
    },
    "Кастомізація": {
        "activities": [
            {"type": "Моделювання", "percentage": 0.1, "order": 1},
            {"type": "Розробка", "percentage": 0.6, "order": 2},
            {"type": "Налаштування", "percentage": 0.2, "order": 3},
            {"type": "Навчання", "percentage": 0.1, "order": 4}
        ]
    },
    "Стандартний функціонал": {
        "activities": [
            {"type": "Налаштування", "percentage": 0.8, "order": 1},
            {"type": "Навчання", "percentage": 0.2, "order": 2}
        ]
    },
    "Налаштування": {
        "activities": [
            {"type": "Налаштування", "percentage": 0.8, "order": 1},
            {"type": "Навчання", "percentage": 0.2, "order": 2}
        ]
    }
}


def determine_work_category(detail_text):
    """
    Determine work category based on keywords in detail text
    """
    detail_lower = detail_text.lower()

    # Development keywords
    dev_keywords = ['розробити', 'розробка', 'створити функціонал', 'інтеграція',
                    'реалізувати', 'механізм', 'логіка', 'алгоритм']

    # Modeling keywords
    model_keywords = ['моделювання', 'технічна документація', 'тз', 'аналіз',
                      'проектування', 'архітектура']

    # Configuration keywords
    config_keywords = ['налаштування', 'налаштувати', 'конфігурація', 'встановити',
                       'прив\'язка', 'зберігання', 'управління', 'створення']

    # Check for development work
    if any(keyword in detail_lower for keyword in dev_keywords):
        return "Розробка"

    # Check for modeling work
    if any(keyword in detail_lower for keyword in model_keywords):
        return "Розробка"  # Modeling is part of development workflow

    # Check for configuration work
    if any(keyword in detail_lower for keyword in config_keywords):
        return "Налаштування"

    # Default to configuration for standard functionality
    return "Налаштування"


def explode_backlog_item(row, work_category):
    """
    Explode a backlog item into activity stages
    """
    activities = []

    if work_category not in ACTIVITY_RULES:
        # Keep as single backlog item if no rule
        return [row.copy()]

    rules = ACTIVITY_RULES[work_category]
    total_hours = row.get('Облік часу (план)', 0)

    try:
        total_hours = float(total_hours) if total_hours else 0
    except:
        total_hours = 0

    for activity_rule in rules['activities']:
        new_row = row.copy()
        new_row['Тип робіт'] = activity_rule['type']
        new_row['Облік часу (план)'] = round(total_hours * activity_rule['percentage'], 1)

        # Keep original status or set to backlog
        if pd.isna(new_row.get('Статус', '')) or new_row.get('Статус', '') == '':
            new_row['Статус'] = ''

        activities.append(new_row)

    return activities


def update_manual_statuses(input_file, output_file):
    """
    Main update function
    """
    print("="*70)
    print("MANUAL STATUS UPDATE AND BACKLOG EXPLOSION")
    print("="*70)
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print()

    # Load CSV
    print("Loading CSV...")
    df = pd.read_csv(input_file)
    print(f"✓ Loaded {len(df)} rows")
    print()

    # Statistics
    manual_updates = 0
    exploded_items = 0
    new_rows = []
    processed_details = set()

    # Process each row
    for idx, row in df.iterrows():
        detail = row.get('Деталізація', '').strip()
        current_status = row.get('Статус', '')

        # Check if this row needs manual update
        if detail in MANUAL_UPDATES:
            update_info = MANUAL_UPDATES[detail]

            # If this detail hasn't been processed yet
            if detail not in processed_details:
                # Update the row with manual status
                row['Статус'] = update_info['status']
                row['Коментарі'] = update_info['comment']
                row['Тип робіт'] = update_info['work_type']

                processed_details.add(detail)
                manual_updates += 1

                new_rows.append(row)
            # Skip duplicate entries of the same detail
            continue

        # If it's a backlog item with hours, explode it into activities
        elif row.get('Тип робіт', '') == 'Backlog' and row.get('Облік часу (план)', 0):
            try:
                hours = float(row['Облік часу (план)'])
                if hours > 0:
                    # Determine work category
                    work_category = determine_work_category(detail)

                    # Explode into activities
                    exploded = explode_backlog_item(row, work_category)
                    new_rows.extend(exploded)

                    exploded_items += 1
                    continue
            except:
                pass

        # Keep the row as-is
        new_rows.append(row)

    # Create new dataframe
    df_new = pd.DataFrame(new_rows)

    print(f"Updates applied:")
    print(f"  - Manual status updates: {manual_updates}")
    print(f"  - Backlog items exploded: {exploded_items}")
    print(f"  - Total rows: {len(df)} → {len(df_new)}")
    print()

    # Show status distribution
    print("Status distribution:")
    status_counts = df_new['Статус'].value_counts()
    for status, count in status_counts.items():
        print(f"  - {status if status else '(empty)'}: {count}")
    print()

    # Show work type distribution
    print("Work type distribution:")
    work_type_counts = df_new['Тип робіт'].value_counts()
    for work_type, count in work_type_counts.items():
        print(f"  - {work_type}: {count}")
    print()

    # Save
    print(f"Saving to {output_file}...")
    df_new.to_csv(output_file, index=False)
    print(f"✓ Saved {len(df_new)} rows")
    print()

    print("="*70)
    print("UPDATE COMPLETE")
    print("="*70)


def main():
    """Main execution"""
    try:
        update_manual_statuses(INPUT_FILE, OUTPUT_FILE)
    except FileNotFoundError:
        print(f"ERROR: Could not find {INPUT_FILE}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
