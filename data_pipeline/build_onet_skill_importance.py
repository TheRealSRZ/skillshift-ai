"""Build traceable O*NET skill-importance evidence without modifying careers.json.

Run from repository root:
    python data_pipeline/build_onet_skill_importance.py

Direct crosswalks only. No automatic task-text similarity or fabricated ratings.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAREERS = ROOT / 'data' / 'careers.json'
MAPPINGS = ROOT / 'data' / 'onet_career_mapping.json'
SKILL_CSV = ROOT / 'data' / 'processed' / 'onet_occupation_skills.csv'
TASK_CSV = ROOT / 'data' / 'processed' / 'onet_occupation_tasks.csv'
OUTPUT = ROOT / 'data' / 'processed' / 'onet_skill_importance_evidence.json'

# Explicit and literal equivalent only. Expand after separately reviewing each concept.
DIRECT_SKILL_CROSSWALK = {
    'skill_critical_thinking': 'Critical Thinking',
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def read_csv(path: Path):
    with path.open(newline='', encoding='utf-8-sig') as handle:
        return list(csv.DictReader(handle))


def proposed_weight(importance: float) -> int:
    """Project-defined conversion: [1,2)->1, [2,3)->2, [3,4)->3, [4,5]->4."""
    if not (1 <= importance <= 5):
        raise ValueError(f'O*NET importance out of range: {importance}')
    return min(4, int(importance))


def main():
    careers = read_json(CAREERS)
    mappings = read_json(MAPPINGS)
    skills = read_csv(SKILL_CSV)
    tasks = read_csv(TASK_CSV)
    mapping_by_career = {'role_' + m['career_id']: m for m in mappings}
    rated = {}
    for row in skills:
        if row['Scale ID'] != 'IM':
            continue  # LV is skill proficiency level, not importance
        key = (row['O*NET-SOC Code'], row['Element Name'])
        if key in rated:
            raise ValueError(f'Duplicate O*NET importance rating: {key}')
        rated[key] = row
    task_counts = {}
    for row in tasks:
        if row['Scale ID'] != 'IM':
            continue  # FT category rows and RT are not independent tasks or skill ratings
        code = row['O*NET-SOC Code']
        task_counts[code] = task_counts.get(code, 0) + 1

    output = []
    for career in careers:
        if career.get('evidence_status') == 'synthetic_demo':
            continue
        career_id = career['id']
        if career_id not in mapping_by_career:
            raise ValueError(f'Missing mapping for {career_id}')
        mapping = mapping_by_career[career_id]
        code = mapping['onet_code']
        if not code:
            raise ValueError(f'No O*NET code for {career_id}')
        for skill_id, current_weight in career['required_skills'].items():
            entry = {
                'career_id': career_id,
                'masco_code': career.get('masco_code'),
                'onet_code': code,
                'mapping_note': mapping.get('mapping_note', ''),
                'skill_id': skill_id,
                'current_team_weight': current_weight,
                'evidence_type': 'team_estimate_pending_manual_review',
                'onet_element_name': None,
                'onet_element_id': None,
                'onet_importance_1_to_5': None,
                'onet_rating_date': None,
                'proposed_weight_1_to_4': None,
                'difference_from_current': None,
                'notes': 'No direct O*NET general-skill importance equivalent has been verified. Existing team weight remains unchanged; task and technology evidence need separate review.'
            }
            element = DIRECT_SKILL_CROSSWALK.get(skill_id)
            if element is not None:
                row = rated.get((code, element))
                if row is None:
                    entry['notes'] = 'Direct skill crosswalk exists, but the O*NET IM rating was not found.'
                elif row['Recommend Suppress'].strip().upper() == 'Y' or row['Not Relevant'].strip().upper() == 'Y':
                    entry['evidence_type'] = 'suppressed_or_not_relevant'
                    entry['notes'] = 'Direct rating was suppressed or marked not relevant; it must not be converted.'
                else:
                    importance = float(row['Data Value'])
                    weight = proposed_weight(importance)
                    entry.update({
                        'evidence_type': 'direct_onet_importance',
                        'onet_element_name': row['Element Name'],
                        'onet_element_id': row['Element ID'],
                        'onet_importance_1_to_5': importance,
                        'onet_rating_date': row['Date'],
                        'proposed_weight_1_to_4': weight,
                        'difference_from_current': weight - current_weight,
                        'notes': 'Direct O*NET general-skill importance. Proposed weight uses project-defined thresholds; US-based evidence, not a Malaysian measurement. No automatic change to careers.json.'
                    })
            output.append(entry)
    if len(output) != 36:
        raise ValueError(f'Expected 36 career-skill mappings, got {len(output)}; review script assumptions')
    result = {
        'dataset_id': 'onet_skill_importance_evidence_v1',
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'source': 'O*NET database; data/processed/onet_occupation_skills.csv',
        'geography': 'United States (representative O*NET occupations mapped to Malaysian MASCO groups)',
        'weight_method': 'Team-defined: importance [1,2)->1, [2,3)->2, [3,4)->3, [4,5]->4; only unsuppressed IM ratings of directly matched O*NET skills',
        'warnings': [
            'SkillShift 1-4 values are project conversions, not official O*NET scores.',
            'O*NET LV ratings are not importance; task IM values are task importance, not general skill importance.',
            'Technology examples such as Python and SQL do not have automatic importance ratings.',
            'No career weights are changed by this script; an evidence review and backend agreement are required.',
            'US occupational data are not Malaysian employer demand or AI replacement probabilities.'
        ],
        'task_importance_row_counts_by_onet_code': task_counts,
        'career_skill_evidence': output
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    direct = [x for x in output if x['evidence_type'] == 'direct_onet_importance']
    print(f'PASS: {len(output)} career-skill entries -> {OUTPUT}')
    print(f'Direct O*NET IM ratings: {len(direct)}; unchanged team estimates: {len(output)-len(direct)}')
    for row in direct:
        print(f"  {row['career_id']}: {row['skill_id']} IM={row['onet_importance_1_to_5']} => proposed {row['proposed_weight_1_to_4']} (current {row['current_team_weight']})")
    print('NOTE: This is review evidence only. careers.json is unchanged.')


if __name__ == '__main__':
    main()
