import uuid
import httpx
from fastapi.testclient import TestClient

from backend.main import app
from backend.routes import account

client = TestClient(app)

def test_delete_requires_bearer():
    assert client.delete('/api/account/me').status_code == 401

def test_delete_requires_server_config(monkeypatch):
    monkeypatch.delenv('SUPABASE_URL', raising=False)
    monkeypatch.delenv('SUPABASE_PUBLISHABLE_KEY', raising=False)
    monkeypatch.delenv('SUPABASE_SERVICE_ROLE_KEY', raising=False)
    response = client.delete('/api/account/me', headers={'Authorization':'Bearer abc'})
    assert response.status_code == 503

def install_mock(monkeypatch, handler):
    base_client = httpx.Client
    monkeypatch.setattr(account.httpx, 'Client', lambda *a, **kw:
                        base_client(transport=httpx.MockTransport(handler)))

def test_deletion_uses_verified_identity_not_request_body(monkeypatch):
    user_id = str(uuid.uuid4())
    monkeypatch.setenv('SUPABASE_URL', 'https://test-proj.supabase.co')
    monkeypatch.setenv('SUPABASE_PUBLISHABLE_KEY', 'public-demo')
    monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY', 'private-demo')
    calls = []
    def handler(req):
        calls.append((req.method, str(req.url)))
        if req.url.path.endswith('/auth/v1/user'):
            assert req.headers['authorization'] == 'Bearer example-user-token'
            return httpx.Response(200, json={'id': user_id})
        assert req.url.path.endswith('/auth/v1/admin/users/' + user_id)
        assert req.headers['authorization'] == 'Bearer private-demo'
        return httpx.Response(204)
    install_mock(monkeypatch,handler)
    result = client.request('DELETE','/api/account/me',
            headers={'Authorization':'Bearer example-user-token'}, json={'id':str(uuid.uuid4())})
    assert result.status_code == 200
    assert result.json() == {'deleted':True}
    assert len(calls) == 2

def test_invalid_token_cannot_delete(monkeypatch):
    monkeypatch.setenv('SUPABASE_URL', 'https://test-proj.supabase.co')
    monkeypatch.setenv('SUPABASE_PUBLISHABLE_KEY', 'public-demo')
    monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY', 'private-demo')
    def handler(req):
        assert req.url.path.endswith('/auth/v1/user')
        return httpx.Response(401)
    install_mock(monkeypatch,handler)
    result = client.delete('/api/account/me', headers={'Authorization':'Bearer invalid'})
    assert result.status_code == 401
    assert 'invalid' not in result.text.lower() or 'invalid or expired' in result.text.lower()

def test_failed_admin_delete_not_claimed(monkeypatch):
    monkeypatch.setenv('SUPABASE_URL', 'https://test-proj.supabase.co')
    monkeypatch.setenv('SUPABASE_PUBLISHABLE_KEY', 'public-demo')
    monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY', 'private-demo')
    def handler(req):
        if req.url.path.endswith('/auth/v1/user'):
            return httpx.Response(200, json={'id':str(uuid.uuid4())})
        return httpx.Response(403, text='secret details that must not be exposed')
    install_mock(monkeypatch,handler)
    result = client.delete('/api/account/me', headers={'Authorization':'Bearer valid-token'})
    assert result.status_code == 502
    assert 'secret details' not in result.text

def test_malformed_supabase_host_is_rejected(monkeypatch):
    monkeypatch.setenv('SUPABASE_URL', 'https://project.supabase.co.attacker.example')
    monkeypatch.setenv('SUPABASE_PUBLISHABLE_KEY', 'test')
    monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY', 'test')
    assert client.delete('/api/account/me', headers={'Authorization':'Bearer valid-token'}).status_code == 503
