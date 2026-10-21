"""Combine independently generated O*NET skill and task evidence, without rescoring careers.

Run from SkillShift repository root:
    python data_pipeline/build_onet_combined_evidence.py
Prerequisites:
    python data_pipeline/build_onet_skill_importance.py
    python data_pipeline/build_onet_task_evidence.py
"""
from __future__ import annotations
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
PROCESSED = DATA / 'processed'
INPUT_SKILLS = PROCESSED / 'onet_skill_importance_evidence.json'
INPUT_TASKS = PROCESSED / 'onet_task_skill_evidence.json'
OUTPUT = PROCESSED / 'onet_combined_skill_evidence.json'


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def index_entries(rows, source):
    indexed = {}
    for entry in rows:
        key = (entry['career_id'], entry['skill_id'])
        if key in indexed:
            raise ValueError(f'Duplicate {source} career-skill key: {key}')
        indexed[key] = entry
    return indexed


def main():
    careers = [c for c in read_json(DATA / 'careers.json')
               if c.get('evidence_status') != 'synthetic_demo']
    direct_doc = read_json(INPUT_SKILLS)
    task_doc = read_json(INPUT_TASKS)
    direct = index_entries(direct_doc['career_skill_evidence'], 'direct')
    tasks = index_entries(task_doc['career_skill_evidence'], 'task')
    expected = {(c['id'], skill) for c in careers for skill in c['required_skills']}
    if set(direct) != expected or set(tasks) != expected:
        raise ValueError('Both evidence inputs must cover exactly the current curated career-skill combinations. Regenerate stale outputs first.')
    out = []
    for career in careers:
        for skill_id, team_weight in career['required_skills'].items():
            key = (career['id'], skill_id)
            d, t = direct[key], tasks[key]
            for field, value in [('onet_code', d['onet_code']), ('masco_code', str(career['masco_code'])), ('current_team_weight', team_weight)]:
                if d[field] != value or t[field] != value:
                    raise ValueError(f'Source disagreement for {key}: {field}')
            has_direct = d['evidence_type'] == 'direct_onet_importance'
            task_links = t['tasks']
            proposed = d['proposed_weight_1_to_4'] if has_direct else None
            if has_direct and (not isinstance(proposed, int) or not 1 <= proposed <= 4):
                raise ValueError(f'Invalid directly supported proposal for {key}')
            if not has_direct and proposed is not None:
                raise ValueError(f'Undocumented proposal for {key}')
            if t['proposed_weight_1_to_4'] is not None:
                raise ValueError(f'Task-derived weight is not permitted for {key}')
            if has_direct:
                category = 'direct_rating_plus_tasks' if task_links else 'direct_rating_only'
            elif task_links:
                category = 'task_support_partial' if t['evidence_type'] == 'partial_task_relevance' else 'task_support'
            else:
                category = 'team_estimate_only'
            out.append({
                'career_id': career['id'], 'skill_id': skill_id,
                'masco_code': str(career['masco_code']), 'onet_code': d['onet_code'],
                'mapping_note': d.get('mapping_note'),
                'current_team_weight_1_to_4': team_weight,
                'recommended_backend_weight_1_to_4': team_weight,
                'proposed_direct_rating_weight_1_to_4': proposed,
                'evidence_category': category,
                'direct_skill_evidence': {
                    'status': d['evidence_type'],
                    'onet_element_id': d['onet_element_id'],
                    'onet_element_name': d['onet_element_name'],
                    'importance_1_to_5': d['onet_importance_1_to_5'],
                    'rating_date': d['onet_rating_date'],
                    'conversion': 'min(4, floor(IM)) for unsuppressed directly equivalent Skills IM; project-defined, not official' if has_direct else None,
                    'notes': d['notes'],
                },
                'task_evidence': {
                    'status': t['evidence_type'],
                    'task_count': len(task_links),
                    'tasks': task_links,
                    'notes': t['note'],
                },
                'explanation': (
                    'A direct O*NET general-skill importance rating supports a proposed 1–4 weight; the current team weight is unchanged. Related tasks only support relevance.'
                    if has_direct else
                    'Related O*NET tasks support occupational relevance, but do not establish a numerical skill importance rating. Keep the current team-estimated weight.'
                    if task_links else
                    'No direct rating or sufficiently specific linked task in these extracts. Keep the current team-estimated weight; this does not mean the skill is unimportant.'
                ),
            })
    counts = dict(sorted(Counter(row['evidence_category'] for row in out).items()))
    doc = {
        'dataset_id': 'onet_combined_skill_evidence_v1',
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'input_datasets': [str(INPUT_SKILLS.relative_to(ROOT)), str(INPUT_TASKS.relative_to(ROOT))],
        'source_geography': 'United States (O*NET-SOC representative occupations; not official MASCO-to-O*NET crosswalk)',
        'scoring_policy': {
            'current_backend_weight': 'Always the unmodified careers.json required_skills value (1–4).',
            'direct_general_skill_rating': 'For directly equivalent and unsuppressed O*NET Skills IM only, a proposed project conversion min(4, floor(IM)); not automatically adopted.',
            'related_occupation_tasks': 'Task IM is task importance, NOT skill importance; no numerical skill-score derivation.',
            'missing_evidence': 'Retain team weight; null is unknown, not zero.',
            'not_ai_risk': 'Neither skill nor task importance measures AI exposure or replacement probability.',
        },
        'coverage': {'curated_careers': len(careers), 'career_skill_pairs': len(out),
                     'direct_general_skill_ratings': sum(x['proposed_direct_rating_weight_1_to_4'] is not None for x in out),
                     'task_linked_pairs': sum(x['task_evidence']['task_count'] > 0 for x in out),
                     'evidence_categories': counts},
        'warnings': [
            'Source rating dates vary; preserve dates per rating/task and do not imply all evidence was measured this year.',
            'All task-to-skill links are human-reviewed interpretations, including partial links; not official crosswalks.',
            'The US Registered Nurses occupational tasks do not define Malaysian legal nursing scope.',
            'Software-specific technologies and other unmatched concepts must not receive invented O*NET general-skill ratings.',
            'This evidence output changes no career weights, matching logic, forecasts, or scenario multipliers.',
        ],
        'career_skill_evidence': out,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    print(f'PASS: {len(out)} career-skill evidence records -> {OUTPUT}')
    print(f"Direct Skills IM: {doc['coverage']['direct_general_skill_ratings']}; task-linked: {doc['coverage']['task_linked_pairs']}; team weights unchanged")
    print(f'Evidence categories: {counts}')

if __name__ == '__main__':
    main()
