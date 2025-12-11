# Project Documentation Consolidation Tool

## Overview

This tool consolidates project documentation by merging GAP Analysis (scope/requirements) with Sprint Plans (schedule) to create a comprehensive Project Implementation Plan.

## Purpose

The tool solves the problem of having scope and schedule in separate files by:
1. Using Sprint Plans as the master timeline
2. Enriching timeline data with detailed requirements from GAP Analysis
3. "Exploding" each feature into its implementation lifecycle activities
4. Formatting everything according to the Project Plan template

## Files

### Input Files
- **GAP_Analysis.csv**: Contains detailed requirements, estimates (BA/Dev hours), coverage type, and importance markers
- **Sprint_Plan.csv** (multiple files): Master schedule containing tasks assigned to specific sprints with start/end dates

### Output Files
- **Final_Integrated_Plan.csv**: Main consolidated project plan in the required template format
- **Match_Report.csv**: Detailed report showing which GAP features were matched to which Sprint tasks

### Scripts
- **consolidate_project_plan.py**: Original version (basic fuzzy matching)
- **consolidate_project_plan_v2.py**: Improved version with enhanced keyword matching and reporting ✅ **RECOMMENDED**

## How It Works

### 1. Sprint Mapping (Index the Schedule)
The script reads all Sprint files and creates a lookup dictionary:
- **Key**: Task Name
- **Value**: {Sprint Number, Start Date, End Date, Hours, Group}

### 2. GAP Processing (Process the Scope)
Iterates through GAP Analysis and finds matches:
- **Matched**: Uses Sprint dates from the map
- **Not matched**: Flagged as "Backlog"

### 3. Activity Explosion (Critical Feature) 🚀

For every matched feature, the script generates multiple activity rows based on coverage type:

#### For "Розробка" / "Кастомізація" → 4 Activities:
1. **Моделювання** (Modeling): 10% of sprint duration, at the start
2. **Розробка** (Development): 60% of sprint duration, middle
3. **Налаштування** (Configuration): 20% of sprint duration, after dev
4. **Навчання** (Training): 10% of sprint duration, at the end

#### For "Стандартний функціонал" → 2 Activities:
1. **Налаштування** (Configuration): 80% of sprint duration
2. **Навчання** (Training): 20% of sprint duration

### 4. Data Enrichment
- **Hours**: Taken from GAP (BA hours + Dev hours)
- **Section & Details**: Taken from GAP (Розділ, Деталізація)
- **Status**: Set based on importance (Критично → Заплановано)
- **Comments**: "Planned in Sprint [X]"

## Matching Logic

The script uses enhanced fuzzy matching with:
- **Direct string matching** (score: 1.0)
- **Containment matching** (score: 0.95)
- **Keyword extraction** with stop-word filtering
- **Jaccard similarity** for keyword overlap
- **Sequence matching** as fallback

**Default threshold**: 0.5 (50% similarity)

## Usage

### Basic Usage
```bash
python3 consolidate_project_plan_v2.py
```

### Expected Output
```
======================================================================
PROJECT DOCUMENTATION CONSOLIDATION v2
======================================================================
Reading sprint files...
  Processing: 1 Спринт - 0 Спринт.csv
  Processing: 2 Спринт - 0 Спринт.csv
  ...
  Total tasks mapped: 58

Reading GAP Analysis: Gap Termi Community - today - GAP з модулем Appointments (1).csv
  Total GAP entries: 240

Consolidating GAP Analysis with Sprint Plans...
  ✓ Matched: 14
  ✓ Unmatched (Backlog): 128
  ✓ Total output rows: 180

Writing output to: Final_Integrated_Plan.csv
  ✓ Successfully written 180 rows

Writing match report to: Match_Report.csv
  ✓ Successfully written 14 matches

======================================================================
CONSOLIDATION COMPLETE
======================================================================
```

## Output Format

The **Final_Integrated_Plan.csv** follows the template structure:

| Column | Description |
|--------|-------------|
| Розділ | Section from GAP Analysis |
| Деталізація | Feature name from GAP Analysis |
| Тип робіт | Activity type (Моделювання, Розробка, Налаштування, Навчання, Backlog) |
| Статус | Status (Заплановано for critical items) |
| Учасники від замовника | Customer participants (empty) |
| Учасники від виконавця | Executor participants (empty) |
| Днів на виконання (робочих) | Work days (empty) |
| Дата початку план | Planned start date |
| Дата закінчення план | Planned end date |
| Дата початку факт | Actual start date (empty) |
| Дата закінчення факт | Actual end date (empty) |
| Облік часу (план) | Planned hours (from GAP) |
| Облік часу (факт) | Actual hours (empty) |
| Коментарі | Comments (Sprint assignment) |

## Example Output

### Matched Item (Development)
```csv
Розділ,Деталізація,Тип робіт,Статус,Дата початку план,Дата закінчення план,Облік часу (план),Коментарі
Інтеграція з АСКД,Розробити технічну документацію та реалізувати двосторонню інтеграцію з сервером СКД S-Meatronics.,Моделювання,Заплановано,26.08.2025,27.08.2025,1.4,Planned in Sprint 2
Інтеграція з АСКД,Розробити технічну документацію та реалізувати двосторонню інтеграцію з сервером СКД S-Meatronics.,Розробка,Заплановано,27.08.2025,03.09.2025,8.4,Planned in Sprint 2
Інтеграція з АСКД,Розробити технічну документацію та реалізувати двосторонню інтеграцію з сервером СКД S-Meatronics.,Налаштування,Заплановано,03.09.2025,05.09.2025,2.8,Planned in Sprint 2
Інтеграція з АСКД,Розробити технічну документацію та реалізувати двосторонню інтеграцію з сервером СКД S-Meatronics.,Навчання,Заплановано,05.09.2025,08.09.2025,1.4,Planned in Sprint 2
```

### Unmatched Item (Backlog)
```csv
Розділ,Деталізація,Тип робіт,Облік часу (план),Коментарі
Серверні роботи,Розгорнути тестове середовище Odoo,Backlog,1.5,Not assigned to any sprint - BACKLOG
```

## Customization

### Adjust Matching Threshold
Edit line ~93 in `consolidate_project_plan_v2.py`:
```python
def find_best_match(self, task_name: str, threshold: float = 0.5):
```
- **Lower threshold** (e.g., 0.3): More matches, but lower quality
- **Higher threshold** (e.g., 0.7): Fewer matches, but higher quality

### Adjust Activity Distribution
Edit the percentage values in the `explode_activities` method:
```python
# Current distribution for Development:
modeling: 10%  → round(total_hours * 0.1, 1)
development: 60%  → round(total_hours * 0.6, 1)
configuration: 20%  → round(total_hours * 0.2, 1)
training: 10%  → round(total_hours * 0.1, 1)
```

### Change File Names
Edit line ~628:
```python
gap_file = 'Gap Termi Community - today - GAP з модулем Appointments (1).csv'
```

## Statistics

From the current run:
- **Sprint Tasks**: 58 tasks mapped from 5 sprint files
- **GAP Entries**: 240 requirements analyzed
- **Match Rate**: 14 matches (5.8%)
- **Output Activities**: 180 total rows (42 sprint-assigned, 138 backlog)
- **Best Match**: 96% similarity (АСКД integration documentation)

## Requirements

- Python 3.6+
- Standard library only (no external dependencies)

## Troubleshooting

### Low Match Rate
If too few items are matching:
1. Review the **Match_Report.csv** to see which items matched
2. Lower the matching threshold in the script
3. Check if task names in Sprint files align with GAP requirement names
4. Consider manually editing Sprint task names to better match GAP features

### Incorrect Dates
If dates look wrong:
1. Check that Sprint files have the correct date format (dd.mm.yyyy)
2. Verify that the "Всього" row in Sprint files contains valid dates
3. Check the `parse_date` method supports your date format

### Missing Hours
If hours are missing:
1. Verify GAP file has "Оцінка БА (год)" and "Оцінка Розробників (год)" columns
2. Check for comma vs. period decimal separators (script handles both)

## License

Internal tool for project management.

## Author

Created for Termi Community Project - December 2025
