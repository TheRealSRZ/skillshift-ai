from backend.store import load_json
from data_pipeline.validate_sources import validate_source_record

def test_unique_skill_ids_and_role_references():
    skills = load_json('skills.json')
    roles = load_json('careers.json')
    skill_ids = {s['id'] for s in skills}
    assert len(skill_ids) == len(skills)
    assert all(set(role['required_skills']).issubset(skill_ids) for role in roles)

def test_synthetic_labels_not_misrepresented():
    trends = load_json('trends.json')
    assert trends['region']=='synthetic_demo'
    assert all(validate_source_record(s) for s in load_json('sources.json'))
