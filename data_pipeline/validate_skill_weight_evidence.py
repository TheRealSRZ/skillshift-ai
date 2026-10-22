"""Validate SkillShift AI's career-skill weighting evidence against project data.

Run from the project root: python data_pipeline/validate_skill_weight_evidence.py
No third-party dependencies; does not modify project files.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'


def read(name):
    with (DATA / name).open(encoding='utf-8') as file:
        return json.load(file)


def main():
    careers = {x['id']: x for x in read('careers.json')}
    skills = {x['id']: x for x in read('skills.json')}
    sources = {x['id']: x for x in read('sources.json')}
    evidence = read('skill_weight_evidence.json')
    errors = []
    seen = set()
    records = evidence.get('assignments', [])
    career_ids = set(evidence['scope']['careers_reviewed'])
    expected_pairs = {(cid, sid) for cid in career_ids for sid in careers[cid]['required_skills']}

    for n, row in enumerate(records, 1):
        cid, sid = row.get('career_id'), row.get('skill_id')
        key = (cid, sid)
        if key in seen:
            errors.append(f'Entry {n}: duplicate pair {key}')
        seen.add(key)
        if cid not in careers or sid not in skills:
            errors.append(f'Entry {n}: unknown career/skill {key}')
            continue
        actual = careers[cid]['required_skills'].get(sid)
        if actual != row.get('weight'):
            errors.append(f'Entry {n}: evidence weight {row.get("weight")} differs from careers.json {actual}: {key}')
        if not isinstance(row.get('justification'), str) or not row['justification'].strip():
            errors.append(f'Entry {n}: missing weight justification')
        if row.get('weight_provenance') != 'team_defined_judgement_not_official_source_score':
            errors.append(f'Entry {n}: missing team-defined weight provenance')
        if not row.get('evidence'):
            errors.append(f'Entry {n}: no occupational evidence references')
        for ref in row.get('evidence', []):
            source = sources.get(ref.get('source_id'))
            if source is None:
                errors.append(f'Entry {n}: unknown source {ref.get("source_id")}')
                continue
            if ref.get('source_url') != source.get('url'):
                errors.append(f'Entry {n}: source URL mismatch {ref.get("source_id")}')
            claim_id = ref.get('claim_id')
            if claim_id and claim_id not in {c.get('claim_id') for c in source.get('supported_claims', [])}:
                errors.append(f'Entry {n}: invalid claim_id {claim_id}')
    if seen != expected_pairs:
        errors.append(f'Assignment coverage differs: missing={sorted(expected_pairs-seen)} extra={sorted(seen-expected_pairs)}')
    if len(records) != 36 or len(career_ids) != 6:
        errors.append(f'Expected six careers and 36 assignments, got {len(career_ids)} and {len(records)}')
    if errors:
        print('FAIL: skill-weight evidence validation')
        for error in errors:
            print(' -', error)
        raise SystemExit(1)
    print(f'PASS: {len(records)} career-skill weights match careers.json')
    print(f'PASS: all references resolve against {len(sources)} registered sources and supported claim IDs')
    print('PASS: skill IDs and justification/provenance fields are consistent')
    print('NOTE: This validates internal consistency, not independent factual correctness of cited source claims or backend readiness results.')


if __name__ == '__main__':
    main()
