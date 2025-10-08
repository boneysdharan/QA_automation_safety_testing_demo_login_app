# Gives ollama+groq analysis
import os
import pytest
import requests
import ollama
from pathlib import Path
from datetime import datetime

# Setup
ARTIFACTS = Path("artifacts/failure_reports")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

# Groq Configuration
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_KEY = os.environ.get("GROQ_API_KEY")

GROQ_HEADERS = {
    "Authorization": f"Bearer {GROQ_KEY}" if GROQ_KEY else "",
    "Content-Type": "application/json",
}

# Ollama Configuration
OLLAMA_MODEL = "b3"

# Helper Functions
def categorize_test(test_name: str) -> str:
    """
    Tag tests by layer/source.
    """
    name = test_name.lower()
    if "postman" in name:
        return "API (Postman Collection)"
    elif "openapi" in name or "generated" in name:
        return "API (OpenAPI Stub)"
    elif "ui" in name:
        return "Frontend (UI)"
    elif "groq" in name:
        return "Cloud AI Tests"
    elif "ollama" in name:
        return "Local AI Tests"
    else:
        return "Uncategorized"

def analyze_with_groq(failure_message: str) -> str:
    if not GROQ_KEY:
        return "❌ Missing GROQ_API_KEY in environment."

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a test failure analyst. Explain the likely cause and suggest a quick fix."},
            {"role": "user", "content": f"The following pytest test failed:\n{failure_message}"}
        ],
        "temperature": 0.2,
    }

    try:
        resp = requests.post(GROQ_API_URL, headers=GROQ_HEADERS, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"❌ Groq error: {e}"

def analyze_with_ollama(failure_message: str) -> str:
    try:
        resp = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "You are a test failure analyst. Explain the likely cause and suggest a quick fix."},
                {"role": "user", "content": f"The following pytest test failed:\n{failure_message}"}
            ],
        )
        return resp["message"]["content"].strip()
    except Exception as e:
        return f"❌ Ollama error: {e}"

def save_failure_report(test_name: str, layer: str, groq_result: str, ollama_result: str, error_message: str):
    """
    Save structured failure report for each test case.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = (
    test_name.replace("::", "__")
    .replace(":", "_")
    .replace("/", "_")
    .replace("\\", "_")
    )
    filename = ARTIFACTS / f"{safe_name}_{timestamp}.md"
    content = f"""
# 🧪 Failure Report: {test_name}
**Layer:** {layer}  
**Timestamp:** {timestamp}
## ❌ Error Message
## ☁️ Groq Analysis (Cloud)
{groq_result}

## 💻 Ollama Analysis (Local)
{ollama_result}

"""
    filename.write_text(content.strip(), encoding="utf-8")

# Pytest Hook
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        test_name = item.nodeid
        layer = categorize_test(test_name)
        msg = f"Test {test_name} failed:\n{report.longreprtext}"

        print(f"\n🔍 Analyzing failure for: {test_name}")
        print(f"   Layer: {layer}")

        # Run both analyzers
        groq_explanation = analyze_with_groq(msg)
        ollama_explanation = analyze_with_ollama(msg)

        # Display in terminal
        print("\n--- Groq (Cloud) ---")
        print(groq_explanation)
        print("\n--- Ollama (Local) ---")
        print(ollama_explanation)
        print("\n============================\n")

        # Save structured report
        save_failure_report(test_name, layer, groq_explanation, ollama_explanation, msg)