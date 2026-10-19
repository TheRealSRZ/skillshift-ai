from backend.matching import match_roles
from backend.store import load_json

def test_scores_change_with_skill_presence():
    careers = load_json('careers.json')
    trends = load_json('trends.json')
    zero = match_roles([], careers, trends, 'moderate')
    some = match_roles(['skill_python','skill_sql'], careers, trends, 'moderate')
    assert max(m['readiness_score'] for m in zero['matches']) == 0
    assert max(m['readiness_score'] for m in some['matches']) > 0

def test_scenario_can_change_weights():
    careers = load_json('careers.json')
    trend = load_json('trends.json')
    moderate = match_roles(['skill_networking'], careers, trend, 'moderate')
    rapid = match_roles(['skill_networking'], careers, trend, 'rapid')
    mod = next(x for x in moderate['matches'] if x['role_id']=='role_cloud_engineer')
    rap = next(x for x in rapid['matches'] if x['role_id']=='role_cloud_engineer')
    assert mod['readiness_score'] != rap['readiness_score']
