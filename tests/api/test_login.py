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
