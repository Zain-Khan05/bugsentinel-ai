from fastapi.testclient import TestClient
from uuid import uuid4
from app.main import app


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_developer(client: TestClient) -> tuple[str, str]:
    email = f"developer.{uuid4().hex}@example.com"
    response = client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123"})
    assert response.status_code == 201
    return email, response.json()["access_token"]

def test_health_check():
    with TestClient(app) as client:
        assert client.get("/api/v1/health").json()["status"] == "healthy"

def test_login_and_submit_scan():
    with TestClient(app) as client:
        login = client.post("/api/v1/auth/login", json={"email": "developer@example.com", "password": "ChangeMe123!"})
        assert login.status_code == 200
        result = client.post("/api/v1/scans", headers=authorization(login.json()["access_token"]), json={"repository_name": "test-repo", "files": [{"filename": "x.py", "content": "print('hello')"}]})
        assert result.status_code == 200
        assert result.json()["overall_risk_level"] == "low"


def test_scan_rejects_unsupported_file_extensions():
    with TestClient(app) as client:
        _, token = register_developer(client)
        response = client.post(
            "/api/v1/scans",
            headers=authorization(token),
            json={"repository_name": "unsupported-file", "files": [{"filename": "notes.txt", "content": "not source code"}]},
        )
        assert response.status_code == 422
        assert "Only .py, .js, .jsx, .ts, .tsx, and .java" in response.text


def test_register_duplicate_and_current_user():
    with TestClient(app) as client:
        email, token = register_developer(client)
        profile = client.get("/api/v1/auth/me", headers=authorization(token))
        assert profile.status_code == 200
        assert profile.json() == {"email": email, "role": "developer"}
        duplicate = client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123"})
        assert duplicate.status_code == 409


def test_registration_requires_a_strong_password():
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/register", json={"email": "weak@example.com", "password": "weakpassword"})
        assert response.status_code == 422


def test_change_password_requires_current_password_and_updates_password():
    with TestClient(app) as client:
        email, _ = register_developer(client)
        original = "SecurePassword123"
        login = client.post("/api/v1/auth/login", json={"email": email, "password": original})
        token = login.json()["access_token"]
        wrong_current = client.post("/api/v1/auth/change-password", headers=authorization(token), json={"current_password": "WrongPassword123", "password": "NewSecurePassword123"})
        assert wrong_current.status_code == 401
        changed = client.post("/api/v1/auth/change-password", headers=authorization(token), json={"current_password": original, "password": "NewSecurePassword123"})
        assert changed.status_code == 200
        assert client.post("/api/v1/auth/login", json={"email": email, "password": "NewSecurePassword123"}).status_code == 200


def test_google_oauth_requires_configuration(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    with TestClient(app) as client:
        response = client.get("/api/v1/auth/google/login", follow_redirects=False)
        assert response.status_code == 503


def test_google_oauth_redirects_when_configured(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")
    with TestClient(app) as client:
        response = client.get("/api/v1/auth/google/login", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"].startswith("https://accounts.google.com/o/oauth2/v2/auth?")


def test_protected_routes_reject_missing_and_invalid_jwts():
    with TestClient(app) as client:
        assert client.get("/api/v1/scans").status_code == 401
        assert client.get("/api/v1/scans", headers=authorization("not-a-valid-jwt")).status_code == 401


def test_api_security_headers_and_untrusted_host_rejection():
    with TestClient(app) as client:
        health = client.get("/api/v1/health")
        assert health.headers["x-content-type-options"] == "nosniff"
        assert health.headers["x-frame-options"] == "DENY"
        assert health.headers["permissions-policy"] == "camera=(), geolocation=(), microphone=()"
        rejected = client.get("/api/v1/health", headers={"host": "untrusted.example"})
        assert rejected.status_code == 400


def test_scan_history_is_isolated_between_developers():
    with TestClient(app) as client:
        _, first_token = register_developer(client)
        _, second_token = register_developer(client)
        scan = client.post("/api/v1/scans", headers=authorization(first_token), json={"repository_name": "private-repository", "files": [{"filename": "private.py", "content": "print('private')"}]})
        assert scan.status_code == 200
        scan_id = scan.json()["id"]
        saved_scan = client.get(f"/api/v1/scans/{scan_id}", headers=authorization(first_token))
        assert saved_scan.status_code == 200
        assert saved_scan.json()["source_files"] == [{"filename": "private.py", "content": "print('private')"}]
        assert client.get(f"/api/v1/scans/{scan_id}", headers=authorization(second_token)).status_code == 404
        history = client.get("/api/v1/scans", headers=authorization(second_token))
        assert history.status_code == 200
        assert scan_id not in {item["id"] for item in history.json()}


def test_admin_audit_requires_admin_role():
    with TestClient(app) as client:
        _, developer_token = register_developer(client)
        assert client.get("/api/v1/admin/audit", headers=authorization(developer_token)).status_code == 403
        admin = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "ChangeMe123!"})
        audit = client.get("/api/v1/admin/audit", headers=authorization(admin.json()["access_token"]))
        assert audit.status_code == 200
        assert audit.json()["requested_by"] == "admin@example.com"
