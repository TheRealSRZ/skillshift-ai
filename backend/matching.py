from backend.scenarios import SCENARIO_MULTIPLIERS, SCENARIO_DISCLAIMER

def match_roles(skills: list[str], careers: list[dict], trend: dict, scenario: str):
    user = set(skills)
    trend_weights = trend.get('multipliers', {})
    scenario_weights = SCENARIO_MULTIPLIERS[scenario]
    results = []
    for role in careers:
        numerator = 0.0
        denominator = 0.0
        contributions = []
        for sid, base_weight in role['required_skills'].items():
            adjusted_weight = (float(base_weight)
                               * float(trend_weights.get(sid, 1.0))
                               * float(scenario_weights.get(sid, 1.0)))
            denominator += adjusted_weight
            has_skill = sid in user
            if has_skill:
                numerator += adjusted_weight
            contributions.append({'skill_id': sid, 'matched': has_skill,
                                  'effective_weight': round(adjusted_weight, 3)})
        score = round(100 * numerator / denominator, 1) if denominator else 0.0
        results.append({
            'role_id': role['id'], 'title': role['title'],
            'readiness_score': score,
            'matched_skills': [c['skill_id'] for c in contributions if c['matched']],
            'missing_skills': [c['skill_id'] for c in contributions if not c['matched']],
            'breakdown': contributions, 'sdgs': role.get('sdgs', []),
        })
    results.sort(key=lambda r: (-r['readiness_score'], r['role_id']))
    return {
        'scenario': scenario,
        'trend_snapshot_id': trend.get('snapshot_id'),
        'data_label': trend.get('label'),
        'scenario_disclaimer': SCENARIO_DISCLAIMER,
        'matches': results,
    }
