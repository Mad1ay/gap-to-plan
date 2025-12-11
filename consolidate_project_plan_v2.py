#!/usr/bin/env python3
"""
Project Documentation Consolidation Script v2
Enhanced version with better matching and reporting
"""

import csv
import glob
import os
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional
import re


class ProjectPlanConsolidator:
    def __init__(self):
        self.sprint_map = {}
        self.gap_data = []
        self.output_rows = []
        self.match_report = []

    def fuzzy_match_score(self, str1: str, str2: str) -> float:
        """Enhanced fuzzy matching with keyword detection"""
        s1 = str1.lower().strip()
        s2 = str2.lower().strip()

        # Direct match
        if s1 == s2:
            return 1.0

        # Full containment
        if s1 in s2 or s2 in s1:
            return 0.95

        # Extract keywords (remove common words)
        stop_words = {'та', 'і', 'в', 'на', 'з', 'по', 'для', 'що', 'який', 'яка', 'яке',
                      'від', 'до', 'за', 'про', 'при', 'під', 'над', 'через', 'у'}

        def extract_keywords(text):
            words = re.findall(r'\w+', text.lower())
            return set(w for w in words if len(w) > 3 and w not in stop_words)

        keywords1 = extract_keywords(s1)
        keywords2 = extract_keywords(s2)

        if keywords1 and keywords2:
            # Jaccard similarity for keywords
            intersection = len(keywords1 & keywords2)
            union = len(keywords1 | keywords2)
            keyword_score = intersection / union if union > 0 else 0

            # If significant keyword overlap, boost score
            if keyword_score > 0.4:
                return 0.7 + (keyword_score * 0.3)

        # Sequence matcher as fallback
        return SequenceMatcher(None, s1, s2).ratio()

    def find_best_match(self, task_name: str, threshold: float = 0.5) -> Optional[Tuple[str, Dict, float]]:
        """Find best matching sprint task with score"""
        best_match = None
        best_sprint_task = None
        best_score = threshold

        for sprint_task, sprint_info in self.sprint_map.items():
            score = self.fuzzy_match_score(task_name, sprint_task)
            if score > best_score:
                best_score = score
                best_match = sprint_info
                best_sprint_task = sprint_task

        if best_match:
            return best_sprint_task, best_match, best_score
        return None

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date from various formats"""
        if not date_str or date_str.strip() == '':
            return None

        date_formats = [
            '%d.%m.%Y',
            '%Y-%m-%d',
            '%d/%m/%Y',
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None

    def calculate_activity_dates(self, start_date: datetime, end_date: datetime,
                                percentage: float, offset_percentage: float = 0) -> Tuple[datetime, datetime]:
        """Calculate start and end dates for an activity"""
        total_duration = (end_date - start_date).days

        activity_start_offset = int(total_duration * offset_percentage)
        activity_duration = max(1, int(total_duration * percentage))

        activity_start = start_date + timedelta(days=activity_start_offset)
        activity_end = activity_start + timedelta(days=activity_duration)

        if activity_end > end_date:
            activity_end = end_date

        return activity_start, activity_end

    def read_sprint_files(self, sprint_pattern: str = "*Спринт*.csv"):
        """Read all sprint files"""
        print("Reading sprint files...")

        sprint_files = sorted(glob.glob(sprint_pattern))

        for sprint_file in sprint_files:
            print(f"  Processing: {sprint_file}")

            sprint_num_match = re.search(r'(\d+)\s+Спринт', sprint_file)
            sprint_num = sprint_num_match.group(1) if sprint_num_match else "Unknown"

            try:
                with open(sprint_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)

                    sprint_start = None
                    sprint_end = None

                    for row in rows:
                        if 'Дата початку спринта' in row and 'Дата завершення спринта' in row:
                            start_str = row['Дата початку спринта']
                            end_str = row['Дата завершення спринта']

                            if start_str and end_str:
                                sprint_start = self.parse_date(start_str)
                                sprint_end = self.parse_date(end_str)

                                if sprint_start and sprint_end:
                                    break

                    for row in rows:
                        task_name = row.get('Задача', '').strip()
                        if task_name and task_name != 'Задача' and not task_name.startswith('Всього'):
                            self.sprint_map[task_name] = {
                                'sprint_num': sprint_num,
                                'start_date': sprint_start,
                                'end_date': sprint_end,
                                'hours': row.get('Оцінка (год)', ''),
                                'group': row.get('Група', '')
                            }

            except Exception as e:
                print(f"  Error reading {sprint_file}: {e}")

        print(f"  Total tasks mapped: {len(self.sprint_map)}")

    def read_gap_analysis(self, gap_file: str):
        """Read GAP Analysis file"""
        print(f"\nReading GAP Analysis: {gap_file}")

        try:
            with open(gap_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.gap_data = list(reader)
                print(f"  Total GAP entries: {len(self.gap_data)}")
        except Exception as e:
            print(f"  Error reading GAP file: {e}")

    def explode_activities(self, gap_row: Dict, sprint_info: Dict) -> List[Dict]:
        """Create multiple activity rows based on coverage type"""
        activities = []

        coverage = gap_row.get('Покриття вимоги', '').strip()
        feature_name = gap_row.get('Вимога', '').strip()
        section = gap_row.get('Функціонал /Блок', '').strip()
        importance = gap_row.get('Важливість', '').strip()

        ba_hours = gap_row.get('Оцінка БА (год)', '0')
        dev_hours = gap_row.get('Оцінка Розробників (год)', '0')

        try:
            ba_hours_float = float(ba_hours.replace(',', '.')) if ba_hours else 0
        except:
            ba_hours_float = 0

        try:
            dev_hours_float = float(dev_hours.replace(',', '.')) if dev_hours else 0
        except:
            dev_hours_float = 0

        total_hours = ba_hours_float + dev_hours_float

        start_date = sprint_info['start_date']
        end_date = sprint_info['end_date']
        sprint_num = sprint_info['sprint_num']

        # Determine status based on importance
        status = ''
        if importance == 'Критично':
            status = 'Заплановано'

        if not start_date or not end_date:
            # No dates available
            if coverage in ['Розробка', 'Кастомізація']:
                activities = [
                    {
                        'Розділ': section,
                        'Деталізація': feature_name,
                        'Тип робіт': 'Моделювання',
                        'Статус': status,
                        'Облік часу (план)': round(total_hours * 0.1, 1),
                        'Коментарі': f'Planned in Sprint {sprint_num}'
                    },
                    {
                        'Розділ': section,
                        'Деталізація': feature_name,
                        'Тип робіт': 'Розробка',
                        'Статус': status,
                        'Облік часу (план)': round(total_hours * 0.6, 1),
                        'Коментарі': f'Planned in Sprint {sprint_num}'
                    },
                    {
                        'Розділ': section,
                        'Деталізація': feature_name,
                        'Тип робіт': 'Налаштування',
                        'Статус': status,
                        'Облік часу (план)': round(total_hours * 0.2, 1),
                        'Коментарі': f'Planned in Sprint {sprint_num}'
                    },
                    {
                        'Розділ': section,
                        'Деталізація': feature_name,
                        'Тип робіт': 'Навчання',
                        'Статус': status,
                        'Облік часу (план)': round(total_hours * 0.1, 1),
                        'Коментарі': f'Planned in Sprint {sprint_num}'
                    }
                ]
            else:
                activities = [
                    {
                        'Розділ': section,
                        'Деталізація': feature_name,
                        'Тип робіт': 'Налаштування',
                        'Статус': status,
                        'Облік часу (план)': round(total_hours * 0.8, 1),
                        'Коментарі': f'Planned in Sprint {sprint_num}'
                    },
                    {
                        'Розділ': section,
                        'Деталізація': feature_name,
                        'Тип робіт': 'Навчання',
                        'Статус': status,
                        'Облік часу (план)': round(total_hours * 0.2, 1),
                        'Коментарі': f'Planned in Sprint {sprint_num}'
                    }
                ]
        else:
            # Calculate dates
            if coverage in ['Розробка', 'Кастомізація']:
                modeling_start, modeling_end = self.calculate_activity_dates(
                    start_date, end_date, 0.1, 0
                )
                dev_start, dev_end = self.calculate_activity_dates(
                    start_date, end_date, 0.6, 0.1
                )
                config_start, config_end = self.calculate_activity_dates(
                    start_date, end_date, 0.2, 0.7
                )
                training_start, training_end = self.calculate_activity_dates(
                    start_date, end_date, 0.1, 0.9
                )

                activities = [
                    {
                        'Розділ': section,
                        'Деталізація': feature_name,
                        'Тип робіт': 'Моделювання',
                        'Статус': status,
                        'Дата початку план': modeling_start.strftime('%d.%m.%Y'),
                        'Дата закінчення план': modeling_end.strftime('%d.%m.%Y'),
                        'Облік часу (план)': round(total_hours * 0.1, 1),
                        'Коментарі': f'Planned in Sprint {sprint_num}'
                    },
                    {
                        'Розділ': section,
                        'Деталізація': feature_name,
                        'Тип робіт': 'Розробка',
                        'Статус': status,
                        'Дата початку план': dev_start.strftime('%d.%m.%Y'),
                        'Дата закінчення план': dev_end.strftime('%d.%m.%Y'),
                        'Облік часу (план)': round(total_hours * 0.6, 1),
                        'Коментарі': f'Planned in Sprint {sprint_num}'
                    },
                    {
                        'Розділ': section,
                        'Деталізація': feature_name,
                        'Тип робіт': 'Налаштування',
                        'Статус': status,
                        'Дата початку план': config_start.strftime('%d.%m.%Y'),
                        'Дата закінчення план': config_end.strftime('%d.%m.%Y'),
                        'Облік часу (план)': round(total_hours * 0.2, 1),
                        'Коментарі': f'Planned in Sprint {sprint_num}'
                    },
                    {
                        'Розділ': section,
                        'Деталізація': feature_name,
                        'Тип робіт': 'Навчання',
                        'Статус': status,
                        'Дата початку план': training_start.strftime('%d.%m.%Y'),
                        'Дата закінчення план': training_end.strftime('%d.%m.%Y'),
                        'Облік часу (план)': round(total_hours * 0.1, 1),
                        'Коментарі': f'Planned in Sprint {sprint_num}'
                    }
                ]
            else:
                config_start, config_end = self.calculate_activity_dates(
                    start_date, end_date, 0.8, 0
                )
                training_start, training_end = self.calculate_activity_dates(
                    start_date, end_date, 0.2, 0.8
                )

                activities = [
                    {
                        'Розділ': section,
                        'Деталізація': feature_name,
                        'Тип робіт': 'Налаштування',
                        'Статус': status,
                        'Дата початку план': config_start.strftime('%d.%m.%Y'),
                        'Дата закінчення план': config_end.strftime('%d.%m.%Y'),
                        'Облік часу (план)': round(total_hours * 0.8, 1),
                        'Коментарі': f'Planned in Sprint {sprint_num}'
                    },
                    {
                        'Розділ': section,
                        'Деталізація': feature_name,
                        'Тип робіт': 'Навчання',
                        'Статус': status,
                        'Дата початку план': training_start.strftime('%d.%m.%Y'),
                        'Дата закінчення план': training_end.strftime('%d.%m.%Y'),
                        'Облік часу (план)': round(total_hours * 0.2, 1),
                        'Коментарі': f'Planned in Sprint {sprint_num}'
                    }
                ]

        return activities

    def consolidate(self):
        """Main consolidation logic"""
        print("\nConsolidating GAP Analysis with Sprint Plans...")

        matched_count = 0
        unmatched_count = 0

        for gap_row in self.gap_data:
            feature = gap_row.get('Вимога', '').strip()

            if not feature:
                continue

            # Try to find matching sprint task
            match_result = self.find_best_match(feature)

            if match_result:
                sprint_task, sprint_info, score = match_result

                # Record match
                self.match_report.append({
                    'GAP Feature': feature,
                    'Sprint Task': sprint_task,
                    'Match Score': f'{score:.2f}',
                    'Sprint': sprint_info['sprint_num']
                })

                # Explode activities
                activities = self.explode_activities(gap_row, sprint_info)
                self.output_rows.extend(activities)
                matched_count += 1
            else:
                # No match - add to backlog
                section = gap_row.get('Функціонал /Блок', '').strip()
                ba_hours = gap_row.get('Оцінка БА (год)', '0')
                dev_hours = gap_row.get('Оцінка Розробників (год)', '0')

                try:
                    ba_hours_float = float(ba_hours.replace(',', '.')) if ba_hours else 0
                except:
                    ba_hours_float = 0

                try:
                    dev_hours_float = float(dev_hours.replace(',', '.')) if dev_hours else 0
                except:
                    dev_hours_float = 0

                total_hours = ba_hours_float + dev_hours_float

                self.output_rows.append({
                    'Розділ': section,
                    'Деталізація': feature,
                    'Тип робіт': 'Backlog',
                    'Облік часу (план)': total_hours,
                    'Коментарі': 'Not assigned to any sprint - BACKLOG'
                })
                unmatched_count += 1

        print(f"  ✓ Matched: {matched_count}")
        print(f"  ✓ Unmatched (Backlog): {unmatched_count}")
        print(f"  ✓ Total output rows: {len(self.output_rows)}")

    def write_output(self, output_file: str = 'Final_Integrated_Plan.csv'):
        """Write consolidated plan to CSV"""
        print(f"\nWriting output to: {output_file}")

        fieldnames = [
            'Розділ',
            'Деталізація',
            'Тип робіт',
            'Статус',
            'Учасники від замовника',
            'Учасники від виконавця',
            'Днів на виконання (робочих)',
            'Дата початку план',
            'Дата закінчення план',
            'Дата початку факт',
            'Дата закінчення факт',
            'Облік часу (план)',
            'Облік часу (факт)',
            'Коментарі'
        ]

        try:
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for row in self.output_rows:
                    output_row = {field: row.get(field, '') for field in fieldnames}
                    writer.writerow(output_row)

            print(f"  ✓ Successfully written {len(self.output_rows)} rows")
        except Exception as e:
            print(f"  ✗ Error writing output: {e}")

    def write_match_report(self, report_file: str = 'Match_Report.csv'):
        """Write matching report"""
        print(f"\nWriting match report to: {report_file}")

        try:
            with open(report_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['GAP Feature', 'Sprint Task', 'Match Score', 'Sprint'])
                writer.writeheader()
                writer.writerows(self.match_report)

            print(f"  ✓ Successfully written {len(self.match_report)} matches")
        except Exception as e:
            print(f"  ✗ Error writing report: {e}")


def main():
    """Main execution function"""
    print("="*70)
    print("PROJECT DOCUMENTATION CONSOLIDATION v2")
    print("="*70)

    consolidator = ProjectPlanConsolidator()

    # Step 1: Read Sprint files
    consolidator.read_sprint_files()

    # Step 2: Read GAP Analysis
    gap_file = 'Gap Termi Community - today - GAP з модулем Appointments (1).csv'
    consolidator.read_gap_analysis(gap_file)

    # Step 3: Consolidate
    consolidator.consolidate()

    # Step 4: Write output
    consolidator.write_output()

    # Step 5: Write match report
    consolidator.write_match_report()

    print("\n" + "="*70)
    print("CONSOLIDATION COMPLETE")
    print("="*70)
    print("\nGenerated files:")
    print("  1. Final_Integrated_Plan.csv - Main consolidated project plan")
    print("  2. Match_Report.csv - Detailed matching report")


if __name__ == '__main__':
    main()
