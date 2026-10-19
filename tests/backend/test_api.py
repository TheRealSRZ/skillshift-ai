from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_and_catalog():
    assert client.get('/api/health').status_code == 200
    result = client.get('/api/catalog').json()
    assert len(result['skills']) > 0

def test_analyze_and_scenarios():
    data={'profile':{'education':'student','skills':['skill_python','skill_sql'],'interests':[]},'scenario':'moderate'}
    response=client.post('/api/analyze',json=data)
    assert response.status_code==200
    assert response.json()['matches']
    scenarios=client.post('/api/scenarios',json=data).json()
    assert 'rapid' in scenarios

def test_unknown_skill_rejected():
    r=client.post('/api/analyze',json={'profile':{'skills':['not_a_real_skill']}})
    assert r.status_code==422
