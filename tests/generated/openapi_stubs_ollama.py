import requests

BASE_URL = "http://127.0.0.1:8000/api"

def test_login_valid():
    """Valid credentials should return a token"""
    url = f"{BASE_URL}/login"
    payload = {"username": "admin", "password": "password123"}
    response = requests.post(url, json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("token") == "fake-jwt-token"

def test_login_invalid_input():
    """Missing credentials should return 400"""
    url = f"{BASE_URL}/login"
    payload = {"username": "", "password": ""}
    response = requests.post(url, json=payload)
    assert response.status_code == 400, response.text

def test_login_wrong_password():
    """Wrong password should return 401"""
    url = f"{BASE_URL}/login"
    payload = {"username": "admin", "password": "wrong"}
    response = requests.post(url, json=payload)
    assert response.status_code == 401, response.text

def test_protected_with_valid_token():
    """Protected route with valid token"""
    url = f"{BASE_URL}/protected"
    headers = {"Authorization": "Bearer fake-jwt-token"}
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "You have access to protected data"

def test_protected_with_invalid_token():
    """Protected route with invalid token"""
    url = f"{BASE_URL}/protected"
    headers = {"Authorization": "Bearer invalid-token"}
    response = requests.get(url, headers=headers)
    assert response.status_code == 401, response.text
