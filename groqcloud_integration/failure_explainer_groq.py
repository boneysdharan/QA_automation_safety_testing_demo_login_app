# Failure explainer for groqcloud
import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
import datetime

load_dotenv()
# Settig groqcloud with api and url
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
ARTIFACTS_DIR = Path("artifacts") / "failure_explanations"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def explain_failure(log_text: str, model: str = "llama-3.1-8b-instant") -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    prompt = (
        "You are a concise test-failure analyzer. Given the failing test log, "
        "produce a short JSON with fields: 'likely_cause' and 'quick_fix'. "
        "Be direct and give a one-line code example if applicable.\n\nLog:\n" + log_text
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a test failure explainer."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
    }
    resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    out = resp.json()
    # try a few extraction patterns
    content = None
    if "choices" in out and out["choices"]:
        choice = out["choices"][0]
        if "message" in choice:
            content = choice["message"].get("content")
        else:
            content = choice.get("text")
    if not content:
        content = json.dumps(out)
    # Save to artifacts with timestamp
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = ARTIFACTS_DIR / f"groq_explanation_{ts}.json"
    try:
        # if content is JSON-like, attempt parse, else wrap it
        parsed = json.loads(content)
    except Exception:
        parsed = {"raw_explanation": content}
    data = {"log": log_text, "explanation": parsed}
    filename.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return filename.as_posix()
