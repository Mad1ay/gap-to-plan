#!/usr/bin/env python3
"""
Post-processing script for Final_Integrated_Plan.csv
Applies date-based status updates, terminology cleanup, and fills missing comments
"""

import pandas as pd
from datetime import datetime

# Configuration
CURRENT_DATE = datetime(2025, 12, 11)
INPUT_FILE = 'Final_Integrated_Plan.csv'
OUTPUT_FILE = 'Final_Integrated_Plan_v2.csv'

# Terminology mapping
WORK_TYPE_MAPPING = {
    'Modeling': 'Моделювання',
    'Development': 'Розробка',
    'Configuration': 'Налаштування',
    'Setup': 'Налаштування',
    'Deployment': 'Деплоймент',
    'Training': 'Навчання',
    # Keep existing Ukrainian terms as-is
    'Моделювання': 'Моделювання',
    'Розробка': 'Розробка',
    'Налаштування': 'Налаштування',
    'Деплоймент': 'Деплоймент',
    'Навчання': 'Навчання',
    'Backlog': 'Backlog'
}


def parse_date_safe(date_str):
    """
    Safely parse date string to datetime object
    Returns None if parsing fails or if string is empty
    """
    if pd.isna(date_str) or date_str == '':
        return None

    try:
        # Try dd.mm.yyyy format
        return datetime.strptime(str(date_str).strip(), '%d.%m.%Y')
    except ValueError:
        try:
            # Try yyyy-mm-dd format
            return datetime.strptime(str(date_str).strip(), '%Y-%m-%d')
        except ValueError:
            return None


def determine_status(start_date, end_date, current_date):
    """
    Determine status based on dates and current date (Time Travel Logic)

    Rules:
    - If end_date < current_date -> "Виконано" (Done)
    - If start_date > current_date -> "Заплановано" (Planned)
    - If current_date is between start and end -> "В роботі" (In Progress)
    - If no dates -> keep existing status (likely "Backlog")
    """
    if end_date and end_date < current_date:
        return "Виконано"
    elif start_date and start_date > current_date:
        return "Заплановано"
    elif start_date and end_date and start_date <= current_date <= end_date:
        return "В роботі"
    else:
        # No valid dates or logic doesn't apply
        return None  # Keep existing status


def postprocess_plan(input_file, output_file, current_date):
    """
    Main post-processing function
    """
    print("="*70)
    print("POST-PROCESSING PROJECT PLAN")
    print("="*70)
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Current date for logic: {current_date.strftime('%d.%m.%Y')}")
    print()

    # Load CSV
    print("Loading CSV file...")
    df = pd.read_csv(input_file)
    print(f"✓ Loaded {len(df)} rows")
    print()

    # Store original values for comparison
    original_statuses = df['Статус'].copy()
    original_work_types = df['Тип робіт'].copy()
    original_comments = df['Коментарі'].copy()

    # =================================================================
    # 1. FIX STATUSES BASED ON DATES (Time Travel Logic)
    # =================================================================
    print("1. Applying Time Travel Logic to Статус...")

    status_updates = 0

    for idx, row in df.iterrows():
        # Parse dates
        start_date = parse_date_safe(row['Дата початку план'])
        end_date = parse_date_safe(row['Дата закінчення план'])

        # Determine new status
        new_status = determine_status(start_date, end_date, current_date)

        # Update if we have a new status
        if new_status:
            # Special handling: don't overwrite if it's already correctly set
            current_status = row['Статус']

            # Always update if logic suggests a change
            if pd.isna(current_status) or current_status == '' or current_status != new_status:
                # Don't change "Backlog" items that have no dates
                if current_status != 'Backlog' or (start_date or end_date):
                    df.at[idx, 'Статус'] = new_status
                    status_updates += 1

    print(f"  ✓ Updated {status_updates} status values")

    # Show status distribution
    status_counts = df['Статус'].value_counts()
    print("\n  Status distribution:")
    for status, count in status_counts.items():
        print(f"    - {status}: {count}")
    print()

    # =================================================================
    # 2. TERMINOLOGY CLEANUP (Тип робіт)
    # =================================================================
    print("2. Cleaning up Тип робіт terminology...")

    terminology_updates = 0

    for idx, row in df.iterrows():
        work_type = row['Тип робіт']

        if pd.notna(work_type) and work_type != '':
            # Check if we need to map it
            if work_type in WORK_TYPE_MAPPING:
                new_work_type = WORK_TYPE_MAPPING[work_type]
                if new_work_type != work_type:
                    df.at[idx, 'Тип робіт'] = new_work_type
                    terminology_updates += 1

    print(f"  ✓ Updated {terminology_updates} work type values")

    # Show work type distribution
    work_type_counts = df['Тип робіт'].value_counts()
    print("\n  Work type distribution:")
    for work_type, count in work_type_counts.items():
        print(f"    - {work_type}: {count}")
    print()

    # =================================================================
    # 3. FILL MISSING COMMENTS
    # =================================================================
    print("3. Filling missing Коментарі...")

    comment_updates = 0

    for idx, row in df.iterrows():
        comment = row['Коментарі']
        start_date = parse_date_safe(row['Дата початку план'])
        end_date = parse_date_safe(row['Дата закінчення план'])

        # If comment is empty but we have dates
        if (pd.isna(comment) or comment == '') and (start_date or end_date):
            df.at[idx, 'Коментарі'] = 'Scheduled based on Sprint Plan'
            comment_updates += 1

    print(f"  ✓ Filled {comment_updates} missing comments")
    print()

    # =================================================================
    # SAVE OUTPUT
    # =================================================================
    print(f"Saving to {output_file}...")
    df.to_csv(output_file, index=False)
    print(f"✓ Successfully saved {len(df)} rows")
    print()

    # =================================================================
    # SUMMARY
    # =================================================================
    print("="*70)
    print("POST-PROCESSING COMPLETE")
    print("="*70)
    print(f"Total changes:")
    print(f"  - Status updates: {status_updates}")
    print(f"  - Terminology updates: {terminology_updates}")
    print(f"  - Comment fills: {comment_updates}")
    print(f"  - Total rows: {len(df)}")
    print()
    print(f"Output file ready: {output_file}")
    print("="*70)


def main():
    """Main execution"""
    try:
        postprocess_plan(INPUT_FILE, OUTPUT_FILE, CURRENT_DATE)
    except FileNotFoundError:
        print(f"ERROR: Could not find input file '{INPUT_FILE}'")
        print("Please ensure the file exists in the current directory.")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
