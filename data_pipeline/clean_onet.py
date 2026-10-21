"""Extract O*NET occupation skills and tasks for SkillShift AI.

Run from repository root: python data_pipeline/clean_onet.py
Requires: pandas, openpyxl. O*NET data is US-based, not Malaysian.
"""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data' / 'external' / 'onet'
OUTPUT = ROOT / 'data' / 'processed'
MAPPING_PATH = ROOT / 'data' / 'onet_career_mapping.json'

FILES = {
    'occupations': 'Occupation Data.xlsx',
    'essential': 'Essential Skills.xlsx',
    'transferable': 'Transferable Skills.xlsx',
    'statements': 'Task Statements.xlsx',
    'ratings': 'Task Ratings.xlsx',
}


def main():
    if not MAPPING_PATH.exists():
        raise SystemExit(f'Missing mapping config: {MAPPING_PATH}')
    mappings = json.loads(MAPPING_PATH.read_text(encoding='utf-8'))
    if not isinstance(mappings, list) or len(mappings) != 6:
        raise SystemExit('Expected exactly six entries in onet_career_mapping.json')
    ids = [x['career_id'] for x in mappings]
    if len(ids) != len(set(ids)):
        raise SystemExit('Duplicate career_id in mapping config')

    missing = [str(INPUT / name) for name in FILES.values() if not (INPUT / name).is_file()]
    if missing:
        raise SystemExit('Missing source files:\n' + '\n'.join(missing))

    occupations = pd.read_excel(INPUT / FILES['occupations'], dtype={'O*NET-SOC Code': str})
    known_codes = set(occupations['O*NET-SOC Code'].dropna())
    accepted = {}
    for mapping in mappings:
        career_id = mapping['career_id']
        code = mapping.get('onet_code')
        if not code or mapping.get('mapping_status') != 'verified':
            print(f'SKIP {career_id}: no verified O*NET mapping')
            continue
        if code not in known_codes:
            raise SystemExit(f'Unknown O*NET code {code!r} for {career_id}')
        accepted[code] = career_id
        name = occupations.loc[occupations['O*NET-SOC Code'] == code, 'Title'].iloc[0]
        print(f'MAP {career_id}: {code} — {name}')
    if not accepted:
        raise SystemExit('No verified O*NET codes to extract')

    def source_frame(filename):
        frame = pd.read_excel(INPUT / filename, dtype={'O*NET-SOC Code': str})
        frame = frame.loc[frame['O*NET-SOC Code'].isin(accepted)].copy()
        frame.insert(0, 'career_id', frame['O*NET-SOC Code'].map(accepted))
        return frame

    essential = source_frame(FILES['essential'])
    transferable = source_frame(FILES['transferable'])
    essential.insert(1, 'skill_group', 'essential')
    transferable.insert(1, 'skill_group', 'transferable')
    skills = pd.concat([essential, transferable], ignore_index=True)
    # Keep both IM (importance) and LV (level) as their own measurements.
    skills = skills.loc[skills['Scale ID'].isin(['IM', 'LV'])].copy()

    statements = source_frame(FILES['statements'])
    ratings = source_frame(FILES['ratings'])
    # Preserve ALL reported task-rating scales and categories; do not merge
    # different scales or treat frequency-category distributions as importance.
    join_cols = ['O*NET-SOC Code', 'Task ID']
    ratings = ratings.drop(columns=['career_id', 'Title', 'Task'], errors='ignore')
    tasks = statements.merge(ratings, on=join_cols, how='left', validate='one_to_many', suffixes=('', '_rating'))

    OUTPUT.mkdir(parents=True, exist_ok=True)
    skills_path = OUTPUT / 'onet_occupation_skills.csv'
    tasks_path = OUTPUT / 'onet_occupation_tasks.csv'
    skills.to_csv(skills_path, index=False, encoding='utf-8-sig')
    tasks.to_csv(tasks_path, index=False, encoding='utf-8-sig')
    print(f'PASS: {len(skills):,} skill measurements -> {skills_path}')
    print(f'PASS: {len(tasks):,} task/rating rows -> {tasks_path}')
    print('NOTE: O*NET importance ratings are US occupation evidence, NOT Malaysian AI-risk scores.')


if __name__ == '__main__':
    main()
