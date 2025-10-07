import requests

BASE_URL = "http://127.0.0.1:8000/api"

# LOGIN TESTS
def test_login_valid():
    """Positive test: Valid credentials should return a token"""
    url = f"{BASE_URL}/login"
    payload = {"username": "admin", "password": "password123"}
    response = requests.post(url, json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "token" in data
    assert data.get("token") == "fake-jwt-token"

def test_login_invalid_input():
    """Negative test: Empty username/password should return 400"""
    url = f"{BASE_URL}/login"
    payload = {"username": "", "password": ""}
    response = requests.post(url, json=payload)
    assert response.status_code == 400, response.text

def test_login_missing_fields():
    """Negative test: Missing one required field"""
    url = f"{BASE_URL}/login"
    payload = {"username": "admin"}  # Missing password
    response = requests.post(url, json=payload)
    assert response.status_code == 400, response.text

def test_login_wrong_password():
    """Negative test: Wrong password should return 401"""
    url = f"{BASE_URL}/login"
    payload = {"username": "admin", "password": "wrong"}
    response = requests.post(url, json=payload)
    assert response.status_code == 401, response.text

def test_login_missing_username():
    """Negative test: Missing username field"""
    url = f"{BASE_URL}/login"
    payload = {"password": "admin123"}  # username missing
    response = requests.post(url, json=payload)
    assert response.status_code == 400, response.text

def test_login_missing_password():
    """Negative test: Missing password field"""
    url = f"{BASE_URL}/login"
    payload = {"username": "admin"}  # password missing
    response = requests.post(url, json=payload)
    assert response.status_code == 400, response.text

# PROTECTED ENDPOINT TESTS
def test_protected_with_valid_token():
    """Positive test: Protected route with valid token"""
    url = f"{BASE_URL}/protected"
    headers = {"Authorization": "Bearer fake-jwt-token"}
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "You have access to protected data"

def test_protected_with_invalid_token():
    """Negative test: Protected route with invalid token"""
    url = f"{BASE_URL}/protected"
    headers = {"Authorization": "Bearer invalid-token"}
    response = requests.get(url, headers=headers)
    assert response.status_code == 401, response.text

def test_protected_missing_auth_header_ollama():
    """Negative test: Missing Authorization header"""
    response = requests.get(f"{BASE_URL}/protected")
    assert response.status_code == 401
    assert any(
        keyword in response.text.lower()
        for keyword in ["token", "unauthorized", "authorization header missing"]
    )

def test_protected_expired_token():
    """Negative test: Expired token should return 401"""
    url = f"{BASE_URL}/protected"
    headers = {"Authorization": "Bearer expired-token"}
    response = requests.get(url, headers=headers)
    assert response.status_code == 401, response.text

# MODERATE ENDPOINT TESTS
def test_moderate_with_valid_text():
    """Positive test: Valid text payload should be processed successfully"""
    response = requests.post(f"{BASE_URL}/moderate", json={"text": "Hello, world!"})
    assert response.status_code == 200, response.text

def test_moderate_with_empty_text():
    """Negative test: Empty text should return 400"""
    response = requests.post(f"{BASE_URL}/moderate", json={"text": ""})
    assert response.status_code == 400, response.text

def test_moderate_invalid_payload_ollama():
    """Negative test: Invalid payload key"""
    response = requests.post(f"{BASE_URL}/moderate", json={"wrong_key": "data"})
    assert response.status_code == 400
    assert "invalid" in response.text.lower() or "missing" in response.text.lower()