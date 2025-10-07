# sample to conduct login tests
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_login_success():
    resp = requests.post(f"{BASE_URL}/api/login", json={"username": "admin", "password": "password123"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

def test_login_invalid_password():
    resp = requests.post(f"{BASE_URL}/api/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401

def test_login_unknown_user():
    resp = requests.post(f"{BASE_URL}/api/login", json={"username": "ghost", "password": "test"})
    assert resp.status_code == 401

def test_login_empty_body():
    """Negative test: empty body"""
    resp = requests.post(f"{BASE_URL}/api/login", json={})
    assert resp.status_code == 400
    assert "Username" in resp.text or "Password" in resp.text

def test_login_sql_injection():
    """Negative test: SQL injection attempt"""
    payload = {"username": "admin' OR '1'='1", "password": "password123"}
    resp = requests.post(f"{BASE_URL}/api/login", json=payload)
    assert resp.status_code in [400, 401]

def test_login_case_insensitive():
    """Positive test: ensure username is case-sensitive (should fail login if case differs)"""
    payload = {"username": "Admin", "password": "password123"}
    resp = requests.post(f"{BASE_URL}/api/login", json=payload)
    assert resp.status_code == 401

def test_login_extra_fields():
    """Negative test: extra unknown fields"""
    resp = requests.post(f"{BASE_URL}/api/login", json={"username": "admin", "password": "password123", "extra": "data"})
    assert resp.status_code in [200, 400]

def test_login_content_type_missing():
    """Negative test: no content-type header"""
    resp = requests.post(f"{BASE_URL}/api/login", data='{"username": "admin", "password": "password123"}')
    assert resp.status_code in [400, 415]