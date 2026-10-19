from ai.learning_planner import generate_roadmap
from ai.skill_extractor import extract_skills

def test_unverified_courses_never_recommended():
    sample=[{'id':'c1','title':'Unverified','url':'https://example.invalid', 'verified':False,'skill_ids':['skill_sql']}]
    result=generate_roadmap('role_data_analyst',['skill_sql'],'moderate',sample)
    assert not result['steps']
    assert result['uncovered_skills']==['skill_sql']

def test_extractor_only_finds_explicit_matches():
    skills=[{'id':'skill_python','name':'Python'},{'id':'skill_sql','name':'SQL'}]
    result=extract_skills('The advert asks for Python.',skills)
    assert [x['skill_id'] for x in result]==['skill_python']
