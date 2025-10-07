# Samle to conduct tests on toxic detection
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_moderate_clean_text():
    response = client.post("/api/moderate", json={"text": "Hello friend, how are you?"})
    assert response.status_code == 200
    data = response.json()
    assert "toxicity" in data
    assert data["toxicity"] == "non-toxic"  # ✅ check label instead of numeric

def test_moderate_toxic_text():
    response = client.post("/api/moderate", json={"text": "You are stupid and ugly"})
    assert response.status_code == 200
    data = response.json()
    assert "toxicity" in data
    assert data["toxicity"] == "toxic"  # ✅ check label instead of numeric

def test_moderate_empty_text():
    response = client.post("/api/moderate", json={"text": ""})
    assert response.status_code == 400

def test_moderate_special_characters():
    response = client.post("/api/moderate", json={"text": "@#$%^&*()!!!"})
    assert response.status_code == 200
    data = response.json()
    assert "toxicity" in data

def test_moderate_long_text():
    long_text = "good " * 500
    response = client.post("/api/moderate", json={"text": long_text})
    assert response.status_code == 200
    assert "toxicity" in response.json()

def test_moderate_numeric_text():
    """Edge: numeric-only input"""
    response = client.post("/api/moderate", json={"text": "123456"})
    assert response.status_code == 200
    data = response.json()
    assert "toxicity" in data

def test_moderate_html_tags():
    """Edge: HTML injection"""
    response = client.post("/api/moderate", json={"text": "<script>alert('xss')</script>"})
    assert response.status_code == 200
    assert "toxicity" in response.json()


