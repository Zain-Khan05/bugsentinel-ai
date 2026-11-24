from fastapi.testclient import TestClient
from uuid import uuid4
from app.main import app

def test_health_check():
    with TestClient(app) as client:
        assert client.get("/api/v1/health").json()["status"] == "healthy"

def test_login_and_submit_scan():
    with TestClient(app) as client:
        login = client.post("/api/v1/auth/login", json={"email": "developer@example.com", "password": "ChangeMe123!"})
        assert login.status_code == 200
        result = client.post("/api/v1/scans", headers={"Authorization": f"Bearer {login.json()['access_token']}"}, json={"repository_name": "test-repo", "files": [{"filename": "x.py", "content": "print('hello')"}]})
        assert result.status_code == 200
        assert result.json()["overall_risk_level"] == "low"


def test_register_duplicate_and_current_user():
    with TestClient(app) as client:
        email = f"new.user.{uuid4().hex}@example.com"
        registration = client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123"})
        assert registration.status_code == 201
        token = registration.json()["access_token"]
        profile = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert profile.status_code == 200
        assert profile.json() == {"email": email, "role": "developer"}
        duplicate = client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123"})
        assert duplicate.status_code == 409


def test_registration_requires_a_strong_password():
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/register", json={"email": "weak@example.com", "password": "weakpassword"})
        assert response.status_code == 422
