# Generate reason for failure of test + quick fix
import os
import pytest
import requests
import ollama
from pathlib import Path

# Setup
ARTIFACTS = Path("artifacts")
ARTIFACTS.mkdir(exist_ok=True)

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


# Failure Analysis Helpers
def analyze_with_groq(failure_message: str) -> str:
    if not GROQ_KEY:
        return "❌ Missing GROQ_API_KEY in environment."

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a test failure analyst. Explain likely cause and quick fix."},
            {"role": "user", "content": f"The following pytest test failed:\n{failure_message}"}
        ],
        "temperature": 0.2,
    }

    try:
        resp = requests.post(GROQ_API_URL, headers=GROQ_HEADERS, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"❌ Groq error: {e}"


def analyze_with_ollama(failure_message: str) -> str:
    try:
        resp = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "You are a test failure analyst. Explain likely cause and quick fix."},
                {"role": "user", "content": f"The following pytest test failed:\n{failure_message}"}
            ],
        )
        return resp["message"]["content"].strip()
    except Exception as e:
        return f"❌ Ollama error: {e}"


# Pytest Hook
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        msg = f"Test {item.name} failed:\n{report.longreprtext}"

        # Run both analyzers
        groq_explanation = analyze_with_groq(msg)
        ollama_explanation = analyze_with_ollama(msg)

        # Save separately
        (ARTIFACTS / "groq_failure_explanation.md").write_text(groq_explanation, encoding="utf-8")
        (ARTIFACTS / "ollama_failure_explanation.md").write_text(ollama_explanation, encoding="utf-8")

        # Save combined view
        combined = f"""
# Failure Analysis for {item.name}

## Groq (cloud)
{groq_explanation}

---

## Ollama (local)
{ollama_explanation}
"""
        (ARTIFACTS / "failure_explanation_combined.md").write_text(combined.strip(), encoding="utf-8")