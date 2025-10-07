"""
Failure Explainer for Groq Cloud

Analyzes pytest failure logs and produces concise JSON reports
with 'likely_cause' and 'quick_fix' suggestions using Groq API.
"""

import os
import json
import requests
import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

ARTIFACTS_DIR = Path("artifacts") / "failure_explanations"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Main function
def explain_failure(log_text: str, model: str = MODEL) -> str:
    """
    Analyze a pytest failure log using Groq Cloud API
    and save a structured explanation (JSON) to artifacts/.

    Args:
        log_text (str): The raw pytest failure log text.
        model (str): The Groq model to use. Defaults to llama-3.1-8b-instant.

    Returns:
        str: Path to the saved JSON explanation file.
    """
    if not GROQ_API_KEY:
        raise RuntimeError("❌ GROQ_API_KEY not set in environment")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    prompt = (
        "You are a precise test-failure analyzer. Given a failing pytest log, "
        "output a minimal JSON object with fields: "
        "'likely_cause' and 'quick_fix'. "
        "Be specific, concise, and include a one-line code suggestion if relevant.\n\n"
        f"--- LOG START ---\n{log_text}\n--- LOG END ---"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You analyze pytest failures and return JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
    }

    try:
        resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        response_json = resp.json()
    except Exception as e:
        raise RuntimeError(f"❌ Groq API request failed: {e}")

    # Extract model output
    content = None
    try:
        content = response_json["choices"][0]["message"].get("content")
    except (KeyError, IndexError, AttributeError):
        content = response_json.get("text") or json.dumps(response_json)

    if not content:
        content = "No response from Groq API."

    # Attempt to parse as JSON
    try:
        parsed = json.loads(content)
    except Exception:
        parsed = {"raw_explanation": content.strip()}

    # Save in artifact folder
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = ARTIFACTS_DIR / f"groq_failure_explainer_{ts}.json"

    artifact = {
        "timestamp": ts,
        "model": model,
        "log_excerpt": log_text.strip()[:1000],  # store only first 1000 chars of log
        "explanation": parsed,
    }

    filename.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

    print(f"✅ Explanation saved to: {filename}")
    return filename.as_posix()

# Example direct run
if __name__ == "__main__":
    sample_log = "FAILED test_login_valid - AssertionError: expected 200 but got 401"
    explain_failure(sample_log)