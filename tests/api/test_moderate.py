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
