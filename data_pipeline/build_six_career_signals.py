"""Build six-career coverage from the existing validated three-career DOSM pilot.

Run from the repository root:
    python data_pipeline/build_six_career_signals.py

Requires the existing build_career_signals.py in the same data_pipeline folder.
Does NOT overwrite market_signals_pilot.json, trends.json, or source data.
Missing values are explicitly null; this never invents statistics.
"""
import argparse
import json
from datetime import date
from pathlib import Path

from build_career_signals import build as build_pilot

TARGET_CAREER_IDS = (
    'role_software_developer',
    'role_accountant_auditor',
    'role_marketing_professional',
    'role_data_professional',
    'role_electrical_engineer',
    'role_nursing_professional',
)


def build_six(careers_path, input_path):
    careers = json.loads(careers_path.read_text(encoding='utf-8-sig'))
    if not isinstance(careers, list):
        raise ValueError('careers.json must contain a list of careers')
    by_id = {c['id']: c for c in careers}
    if len(by_id) != len(careers):
        raise ValueError('Duplicate career IDs in careers.json')
    absent = set(TARGET_CAREER_IDS) - set(by_id)
    if absent:
        raise ValueError(f'Missing expected careers: {sorted(absent)}')

    # Reuse the existing source-ID, source-URL, MASCO and quarter checks.
    pilot = build_pilot(careers_path, input_path)
    observed = {s['career_id']: s for s in pilot['career_signals']}
    unknown = set(observed) - set(TARGET_CAREER_IDS)
    if unknown:
        raise ValueError(f'Unexpected career IDs in occupation CSV: {sorted(unknown)}')

    signals = []
    for career_id in TARGET_CAREER_IDS:
        career = by_id[career_id]
        if career_id in observed:
            entry = dict(observed[career_id])
            entry['data_status'] = 'observed_comparison_available'
            entry['availability_note'] = 'Two comparable DOSM occupation-title observations provided.'
        else:
            entry = {
                'career_id': career_id,
                'career_title': career['title'],
                'masco_code': str(career['masco_code']),
                'occupation_title_in_source': None,
                'geography': 'Malaysia',
                'metric': 'online_job_offerings_occupation',
                'previous_period': '2026-Q1',
                'previous_job_offerings': None,
                'latest_period': '2026-Q2',
                'latest_job_offerings': None,
                'absolute_change': None,
                'percent_change': None,
                'direction': None,
                'evidence_level': None,
                'source_ids': [],
                'source_urls': [],
                'can_directly_adjust_career_scores': False,
                'ai_impact_measure': False,
                'data_status': 'insufficient_data',
                'availability_note': 'No comparable occupation-specific Q1/Q2 2026 observation in the input dataset; no growth rate computed.',
                'note': 'Not evidence of zero demand, zero growth, or AI impact. Other occupation or speciality evidence may exist but is not used as an equivalent series.',
            }
        signals.append(entry)

    return {
        'snapshot_id': 'dosm_six_career_coverage_2026_q2',
        'status': 'mixed_observed_and_unavailable_occupation_comparisons',
        'generated_date': date.today().isoformat(),
        'geography': 'Malaysia',
        'periods': ['2026-Q1', '2026-Q2'],
        'career_specific': True,
        'skill_specific': False,
        'ai_impact_measure': False,
        'can_directly_adjust_career_scores': False,
        'data_policy': 'Only career-specific observations from the validated input CSV are measured; unavailable values are null, not synthetic or estimated.',
        'method': pilot['method'],
        'observed_count': len(observed),
        'insufficient_data_count': len(signals) - len(observed),
        'limitations': pilot['limitations'] + [
            'Missing observations mean insufficient comparable input data, not absence of job openings.',
            'Output is evidence-only and requires a separately reviewed backend integration policy.',
        ],
        'career_signals': signals,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--careers', type=Path, default=Path('data/careers.json'))
    parser.add_argument('--input', type=Path, default=Path('data/dosm_career_offerings_2026_q1_q2.csv'))
    parser.add_argument('--output', type=Path, default=Path('data/processed/market_signals_six_careers.json'))
    args = parser.parse_args()
    for path in (args.careers, args.input):
        if not path.is_file():
            parser.error(f'Input file missing: {path}')
    protected = (args.careers, args.input,
                 Path('data/processed/market_signals_pilot.json'),
                 Path('data/trends.json'))
    if any(args.output.resolve() == p.resolve() for p in protected):
        parser.error('Output path would overwrite a protected input, pilot, or trends.json')
    result = build_six(args.careers, args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Created {args.output}: {len(result["career_signals"])} careers')
    print(f'Observed: {result["observed_count"]}; insufficient data: {result["insufficient_data_count"]}')
    for entry in result['career_signals']:
        val = entry['percent_change']
        print(f'  {entry["career_id"]}: {val:+.2f}%' if val is not None else
              f'  {entry["career_id"]}: insufficient_data (null)')
    print('Evidence only; no synthetic data or score multipliers generated.')


if __name__ == '__main__':
    main()
