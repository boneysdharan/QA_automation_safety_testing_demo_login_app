# Unified AI-Enhanced Pytest Hook for UI Tests (Groq + Ollama + HTML Embedding)
import os
import pytest
import requests
import ollama
from pathlib import Path
from datetime import datetime
from pytest_html import extras

# CONFIGURATION
ARTIFACTS = Path("artifacts/failure_reports")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_KEY = os.environ.get("GROQ_API_KEY")

GROQ_HEADERS = {
    "Authorization": f"Bearer {GROQ_KEY}" if GROQ_KEY else "",
    "Content-Type": "application/json",
}
OLLAMA_MODEL = "b3"

# HELPER FUNCTIONS
def categorize_test(test_name: str) -> str:
    """Identify which system layer a test belongs to."""
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
    """Analyze test failure using Groq Cloud AI."""
    if not GROQ_KEY:
        return "❌ Missing GROQ_API_KEY in environment."

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a test failure analyst. Explain the likely cause and suggest a quick fix."
            },
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
    """Analyze test failure using Ollama (local)."""
    try:
        resp = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a test failure analyst. Explain the likely cause and suggest a quick fix."
                },
                {"role": "user", "content": f"The following pytest test failed:\n{failure_message}"}
            ],
        )
        return resp["message"]["content"].strip()
    except Exception as e:
        return f"❌ Ollama error: {e}"

def save_failure_report(test_name: str, layer: str, groq_result: str, ollama_result: str, error_message: str):
    """Save a structured markdown report for failed tests."""
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
    return filename

# MAIN PYTEST HOOK

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to analyze failed tests automatically with AI."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        test_name = item.nodeid
        layer = categorize_test(test_name)
        msg = f"Test {test_name} failed:\n{report.longreprtext}"

        print(f"\n🔍 Analyzing failure for: {test_name}")
        print(f"   Layer: {layer}")

        groq_explanation = analyze_with_groq(msg)
        ollama_explanation = analyze_with_ollama(msg)

        print("\n--- Groq (Cloud) ---")
        print(groq_explanation)
        print("\n--- Ollama (Local) ---")
        print(ollama_explanation)
        print("\n============================\n")

        report.failure_report_path = save_failure_report(
            test_name, layer, groq_explanation, ollama_explanation, msg
        )

# HTML REPORT ENHANCEMENT

def pytest_html_results_table_html(report, data):
    """Enhance HTML report: show extra failure details and AI analysis."""
    if report.when != "call":
        return

    test_name = report.nodeid.split("::")[-1]
    duration = getattr(report, "duration", 0.0)
    status = "✅ Passed" if report.passed else "❌ Failed"
    domain = "http://localhost:8501"

    # Start HTML section
    extra_html = f"""
    <div style='margin-top:15px;padding:12px;background:#f9fafb;
                border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,0.05);'>
        <h4>🧾 Extended Test Summary</h4>
        <p><b>Test name:</b> {test_name}</p>
        <p><b>Status:</b> {status}</p>
        <p><b>Execution time:</b> {duration:.2f}s</p>
        <p><b>Domain:</b> {domain}</p>
    """

    # Include AI failure analysis (if applicable)
    if hasattr(report, "failure_report_path") and Path(report.failure_report_path).exists():
        content = Path(report.failure_report_path).read_text(encoding="utf-8")
        extra_html += f"""
        <details style='margin-top:10px;'>
            <summary><b>🧠 AI Failure Analysis (Groq + Ollama)</b></summary>
            <pre style='background:#f3f4f6;padding:10px;border-radius:6px;
                        white-space:pre-wrap;font-size:13px;'>{content}</pre>
        </details>
        """

    extra_html += "</div>"

    # Compatibility fix for pytest-html >=4
    if hasattr(report, "extras"):
        report.extras.append(extras.html(extra_html))
    else:
        data.append(extras.html(extra_html))