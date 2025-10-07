import os
import requests
from pathlib import Path
import importlib.util
import sys

# Constants
API_URL = "https://api.groq.com/openai/v1/chat/completions"
OUTPUT_FILE = Path("tests/generated/openapi_stubs_groq.py")
MODEL = "llama-3.1-8b-instant"

# Load USERS from api.py
spec = importlib.util.spec_from_file_location("api", "api.py")
api = importlib.util.module_from_spec(spec)
sys.modules["api"] = api
spec.loader.exec_module(api)

# Grab valid credentials
if hasattr(api, "USERS") and isinstance(api.USERS, dict) and api.USERS:
    VALID_USERNAME, VALID_PASSWORD = next(iter(api.USERS.items()))
else:
    VALID_USERNAME, VALID_PASSWORD = "admin", "password123"

# API Key
API_KEY = os.environ.get("GROQ_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ Missing GROQ_API_KEY. Please set it in your environment.")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# Prompt for Groq
PROMPT_TEMPLATE = f"""
You are a professional Python QA engineer. 
Generate a pytest file for FastAPI endpoints EXACTLY in the following style and format.

Requirements:
- Import FastAPI app using: from api import app
- Use: from fastapi.testclient import TestClient
- Instantiate client = TestClient(app)
- Define constants:
    VALID_USER = {{"username": "{VALID_USERNAME}", "password": "{VALID_PASSWORD}"}}
    INVALID_USER = {{"username": "{VALID_USERNAME}", "password": "wrong_password"}}
- Group tests under clear comments:
    # --- LOGIN TESTS ---
    # --- PROTECTED ROUTES ---
    # --- MODERATE ENDPOINT ---
- Each test name and body MUST exactly match these:

from api import app
from fastapi.testclient import TestClient

client = TestClient(app)

VALID_USER = {{"username": "{VALID_USERNAME}", "password": "{VALID_PASSWORD}"}}
INVALID_USER = {{"username": "{VALID_USERNAME}", "password": "wrong_password"}}

# --- LOGIN TESTS ---
def test_login_success():
    response = client.post("/api/login", json=VALID_USER)
    assert response.status_code == 200
    assert "token" in response.json()

def test_login_invalid_input():
    \"\"\"Empty username/password should return 400\"\"\"
    response = client.post("/api/login", json={{"username": "", "password": ""}})
    assert response.status_code == 400

def test_login_missing_fields():
    response = client.post("/api/login", json={{"username": "admin"}})
    assert response.status_code == 400

def test_login_wrong_password():
    response = client.post("/api/login", json=INVALID_USER)
    assert response.status_code == 401

def test_login_missing_username():
    response = client.post("/api/login", json={{"password": "admin123"}})
    assert response.status_code == 400

def test_login_missing_password():
    response = client.post("/api/login", json={{"username": "admin"}})
    assert response.status_code == 400

# --- PROTECTED ROUTES ---
def test_protected_with_valid_token():
    login_response = client.post("/api/login", json=VALID_USER)
    token = login_response.json()["token"]
    headers = {{"Authorization": f"Bearer {{token}}"}}
    response = client.get("/api/protected", headers=headers)
    assert response.status_code == 200

def test_protected_with_invalid_token():
    headers = {{"Authorization": "Bearer invalid_token"}}
    response = client.get("/api/protected", headers=headers)
    assert response.status_code == 401

def test_protected_missing_auth_header():
    response = client.get("/api/protected")
    assert response.status_code == 401
    assert any(
        keyword in response.text.lower()
        for keyword in ["token", "unauthorized", "authorization header missing"]
    )

def test_protected_expired_token():
    headers = {{"Authorization": "Bearer expired_token"}}
    response = client.get("/api/protected", headers=headers)
    assert response.status_code == 401

# --- MODERATE ENDPOINT ---
def test_moderate_with_valid_text():
    response = client.post("/api/moderate", json={{"text": "Hello, World!"}})
    assert response.status_code == 200

def test_moderate_with_empty_text():
    response = client.post("/api/moderate", json={{"text": ""}})
    assert response.status_code == 400

def test_moderate_invalid_payload():
    response = client.post("/api/moderate", json={{"wrong_key": "data"}})
    assert response.status_code == 400

Output only this Python code, without markdown, commentary, or extra text.
"""

def call_groq(prompt: str) -> str:
    """Send prompt to Groq API and return text output."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You output clean pytest code, no formatting or markdown."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
    }

    resp = requests.post(API_URL, headers=HEADERS, json=payload)
    if resp.status_code != 200:
        print(f"❌ Groq API error: {resp.status_code} {resp.text}")
        resp.raise_for_status()

    return resp.json()["choices"][0]["message"]["content"]

def clean_output(text: str) -> str:
    """Strip unwanted markdown fences if Groq adds them."""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1]
            if text.strip().startswith("python"):
                text = text[len("python"):].lstrip()
    return text.strip()

def generate_tests():
    print("🚀 Generating Groq-style test file...")
    raw_text = call_groq(PROMPT_TEMPLATE)
    cleaned = clean_output(raw_text)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(cleaned, encoding="utf-8")
    print(f"✅ Tests saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_tests()