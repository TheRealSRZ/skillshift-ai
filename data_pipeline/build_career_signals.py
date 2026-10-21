"""Build an evidence-only pilot snapshot of DOSM occupation-specific job offerings.

Run from repository root:
python data_pipeline/build_career_signals.py --careers data/careers.json

Input:  data/dosm_career_offerings_2026_q1_q2.csv
Output: data/processed/market_signals_pilot.json

This pilot does not modify existing importer or recommendation scores.
"""
import argparse
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

FIELDS = {'career_id', 'occupation_title', 'masco_code', 'period', 'job_offerings', 'source_id', 'source_url'}
PERIODS = ('2026-Q1', '2026-Q2')


def build(careers_path, input_path):
    careers = json.loads(careers_path.read_text(encoding='utf-8-sig'))
    by_id = {c['id']: c for c in careers}
    grouped = defaultdict(dict)
    with input_path.open(encoding='utf-8-sig', newline='') as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames or not FIELDS.issubset(reader.fieldnames):
            raise ValueError('Missing required CSV columns')
        for row in reader:
            career_id, period = row['career_id'], row['period']
            if career_id not in by_id:
                raise ValueError(f'Unknown career ID: {career_id}')
            if period not in PERIODS or period in grouped[career_id]:
                raise ValueError(f'Unexpected or duplicate quarter for {career_id}: {period}')
            if str(by_id[career_id].get('masco_code')) != row['masco_code']:
                raise ValueError(f'MASCO mismatch for {career_id}')
            expected_sources = {
                '2026-Q1': (
                    'src_dosm_jmi_q1_2026',
                    'https://www.dosm.gov.my/portal-main/release-content/'
                    'big-data-analytics-job-market-insights-q12026'
                ),
                '2026-Q2': (
                    'src_dosm_jmi_q2_2026',
                    'https://www.dosm.gov.my/portal-main/release-content/'
                    'big-data-analytics-job-market-insights-q22026'
                )
            }
            expected_id, expected_url = expected_sources[period]

            if row['source_id'] != expected_id or row['source_url'] != expected_url:
                raise ValueError(
                    f'Source mismatch for {career_id} in {period}'
                )
            if not row['job_offerings'].isdigit() or not row['source_url'].startswith('https://www.dosm.gov.my/'):
                raise ValueError(f'Invalid count or source for {career_id}')
            grouped[career_id][period] = row
    result = []
    for career_id, records in sorted(grouped.items()):
        if set(records) != set(PERIODS):
            raise ValueError(f'Two quarters required for {career_id}')
        old, new = (int(records[p]['job_offerings']) for p in PERIODS)
        delta = new - old
        result.append({
            'career_id': career_id,
            'career_title': by_id[career_id]['title'],
            'masco_code': str(by_id[career_id]['masco_code']),
            'occupation_title_in_source': records['2026-Q2']['occupation_title'],
            'geography': 'Malaysia',
            'metric': 'online_job_offerings_occupation',
            'previous_period': PERIODS[0],
            'previous_job_offerings': old,
            'latest_period': PERIODS[1],
            'latest_job_offerings': new,
            'absolute_change': delta,
            'percent_change': round(100 * delta / old, 2) if old else None,
            'direction': 'increase' if delta > 0 else 'decrease' if delta < 0 else 'unchanged',
            'evidence_level': 'reported_occupation_title',
            'source_ids': [records[p]['source_id'] for p in PERIODS],
            'source_urls': [records[p]['source_url'] for p in PERIODS],
            'can_directly_adjust_career_scores': False,
            'ai_impact_measure': False,
            'note': 'Observed quarterly online advertisements; not unique vacancies, a forecast, or AI-caused change. Career title/MASCO mapping follows the project careers file.'
        })
    return {
        'snapshot_id': 'dosm_career_pilot_2026_q2',
        'status': 'observed_occupation_qoq_comparison',
        'generated_date': date.today().isoformat(),
        'career_specific': True,
        'skill_specific': False,
        'can_directly_adjust_career_scores': False,
        'method': '(Q2 count - Q1 count) / Q1 count * 100',
        'limitations': ['Online job offerings are not unique vacancies or employment totals.',
                        'Two quarterly points cannot establish a lasting trend.',
                        'No causal attribution to AI is supported.',
                        'No career recommendation multiplier is produced.'],
        'career_signals': result,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--careers', type=Path, default=Path('data/careers.json'))
    parser.add_argument('--input', type=Path, default=Path('data/dosm_career_offerings_2026_q1_q2.csv'))
    parser.add_argument('--output', type=Path, default=Path('data/processed/market_signals_pilot.json'))
    args = parser.parse_args()
    for path in (args.careers, args.input):
        if not path.is_file():
            parser.error(f'Input file missing: {path}')
    result = build(args.careers, args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Created {args.output}: {len(result["career_signals"])} occupation comparisons')
    for entry in result['career_signals']:
        print(f'  {entry["career_id"]}: {entry["percent_change"]:+.2f}%')
    print('Evidence-only pilot; no recommendation multipliers applied.')


if __name__ == '__main__':
    main()
