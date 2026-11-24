from fastapi.testclient import TestClient
from app.main import app

def test_health_check():
    with TestClient(app) as client:
        assert client.get("/api/v1/health").json()["status"] == "healthy"

def test_login_and_submit_scan():
    with TestClient(app) as client:
        login = client.post("/api/v1/auth/login", json={"email": "developer@bugsentinel.local", "password": "ChangeMe123!"})
        assert login.status_code == 200
        result = client.post("/api/v1/scans", headers={"Authorization": f"Bearer {login.json()['access_token']}"}, json={"repository_name": "test-repo", "files": [{"filename": "x.py", "content": "print('hello')"}]})
        assert result.status_code == 200
        assert result.json()["overall_risk_level"] == "low"
