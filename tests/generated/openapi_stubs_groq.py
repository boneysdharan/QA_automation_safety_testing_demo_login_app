from api import app
from fastapi.testclient import TestClient

client = TestClient(app)

VALID_USER = {"username": "admin", "password": "password123"}
INVALID_USER = {"username": "admin", "password": "wrong_password"}

def test_login_success():
    response = client.post("/api/login", json=VALID_USER)
    assert response.status_code == 200
    assert "token" in response.json()

def test_login_missing_fields():
    response = client.post("/api/login", json={"username": "admin"})
    assert response.status_code == 400

def test_login_wrong_password():
    response = client.post("/api/login", json=INVALID_USER)
    assert response.status_code == 401

def test_protected_with_valid_token():
    login_response = client.post("/api/login", json=VALID_USER)
    token = login_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/protected", headers=headers)
    assert response.status_code == 200

def test_protected_with_invalid_token():
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/protected", headers=headers)
    assert response.status_code == 401

def test_moderate_with_valid_text():
    response = client.post("/api/moderate", json={"text": "Hello, World!"})
    assert response.status_code == 200

def test_moderate_with_empty_text():
    response = client.post("/api/moderate", json={"text": ""})
    assert response.status_code == 400