"""Member 3: deterministic safe starter fallback; connect vetted RunPod later."""

def generate_roadmap(target_role: str, missing_skills: list[str],
                     scenario: str, verified_courses: list[dict], *, use_ai=False):
    # This starter intentionally does not invoke RunPod yet.
    if use_ai:
        raise NotImplementedError('Member 3 to add structured, validated RunPod integration')
    missing = set(missing_skills)
    covered = set()
    steps = []
    for course in verified_courses:
        if not course.get('verified') or not course.get('url'):
            continue
        matched = missing.intersection(course.get('skill_ids', [])) - covered
        if not matched:
            continue
        covered.update(matched)
        steps.append({'step':len(steps)+1, 'course_id':course['id'],
                      'title':course['title'],'url':course['url'],
                      'estimated_hours':course.get('estimated_hours'),
                      'reason':'Covers missing skills: ' + ', '.join(sorted(matched))})
    return {'target_role':target_role,'scenario':scenario,
            'generation_mode':'deterministic_fallback', 'steps':steps,
            'uncovered_skills':sorted(missing-covered),
            'note':'Starter dataset has no verified courses. Member 4 must validate real resources.'
                   if not steps and missing else 'Times are course estimates, not guarantees.'}
