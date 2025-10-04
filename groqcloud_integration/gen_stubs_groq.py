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

# Grab the first valid user
if hasattr(api, "USERS") and isinstance(api.USERS, dict) and api.USERS:
    VALID_USERNAME, VALID_PASSWORD = next(iter(api.USERS.items()))
else:
    VALID_USERNAME, VALID_PASSWORD = "admin", "password123"  # fallback

# Get API key
API_KEY = os.environ.get("GROQ_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ Missing GROQ_API_KEY. Please set it in your environment.")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

PROMPT_TEMPLATE = f"""
Generate pytest test stubs for the FastAPI app defined in api.py.

Rules:
- Import the FastAPI app with: `from api import app`
- Use: `from fastapi.testclient import TestClient`
- Create a single TestClient instance: `client = TestClient(app)`
- Define constants:
  VALID_USER = {{"username": "{VALID_USERNAME}", "password": "{VALID_PASSWORD}"}}
  INVALID_USER = {{"username": "{VALID_USERNAME}", "password": "wrong_password"}}
- Write tests for:
  * /api/login → success, missing fields, wrong password
  * /api/protected → with valid and invalid tokens
  * /api/moderate → with valid text and empty text
- Make sure assertions match the API:
  * login success → 200 + token in response
  * missing fields → 400
  * wrong password → 401
  * empty text → 400
- Do NOT include Markdown formatting or triple backticks.
- The output must be directly runnable as a Python test file.
"""


def call_groq(prompt: str) -> str:
    """Send prompt to Groq API and return text output."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a test generator that outputs valid pytest code only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    resp = requests.post(API_URL, headers=HEADERS, json=payload)

    if resp.status_code != 200:
        print(f"❌ Error from Groq API:\n{resp.status_code} {resp.text}")
        resp.raise_for_status()

    resp_json = resp.json()
    return resp_json["choices"][0]["message"]["content"]


def clean_output(text: str) -> str:
    """Remove ``` fences if present."""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1]
            if text.strip().startswith("python"):
                text = text[len("python"):].lstrip()
    return text.strip()


def generate_tests():
    print("Calling Groq API to generate tests (this may take a few seconds)...")
    raw_text = call_groq(PROMPT_TEMPLATE)
    cleaned_text = clean_output(raw_text)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(cleaned_text, encoding="utf-8")

    print(f"✅ Generated test stubs saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_tests()
