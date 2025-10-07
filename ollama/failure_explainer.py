"""
Failure Explainer for Ollama (Local AI Model)

Captures pytest failures, analyzes them using a local Ollama model,
and logs detailed diagnostics into timestamped log files.
"""
import os
import subprocess
import pytest
from datetime import datetime
from pathlib import Path

# Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "b3")  # Default local model
ARTIFACTS_DIR = Path("artifacts") / "failure_logs"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Create a new log file per session
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = ARTIFACTS_DIR / f"ollama_failure_log_{TIMESTAMP}.log"

# Core Analysis Function
def analyze_failure_with_ollama(error_message: str) -> str:
    """
    Sends the error message to Ollama for AI-powered analysis.
    Returns concise feedback with cause and quick fix suggestions.
    """
    prompt = (
        "You are a software QA assistant. Analyze the following test failure log "
        "and provide a short, structured summary:\n\n"
        f"1️⃣ Likely Cause:\n"
        f"2️⃣ Quick Fix:\n\n"
        f"--- LOG ---\n{error_message}\n--- END LOG ---"
    )

    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=prompt,
            text=True,
            capture_output=True,
            check=True,
            timeout=60
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "⚠️ Ollama analysis timed out after 60s."
    except Exception as e:
        return f"⚠️ Ollama analysis failed: {e}"

# Categorization Helper
def categorize_test(test_name: str) -> str:
    """
    Classify test based on its name or path.
    """
    name = test_name.lower()
    if "ui" in name:
        return "Frontend (UI)"
    elif "api" in name or "moderate" in name:
        return "Backend (API)"
    elif "generated" in name:
        return "Backend (OpenAPI Stub)"
    elif "postman" in name:
        return "Backend (API, Postman)"
    else:
        return "General / Unknown Layer"

# Logging Helper
def log_test(test_name: str, outcome: str, error_message: str = None,
             analysis: str = None, description: str = None):
    """
    Append test results and AI analysis into a structured log file.
    """
    log_entry = [
        f"\n=== 🧪 Test Report ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===",
        f"Test: {test_name}",
        f"Layer: {categorize_test(test_name)}",
        f"Purpose: {description or 'No description provided'}",
        f"Outcome: {outcome}",
    ]

    if error_message:
        log_entry.append(f"Error:\n{error_message}")

    if analysis:
        log_entry.append(f"🤖 Ollama Analysis:\n{analysis}")

    log_entry.append("=" * 80 + "\n")

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n".join(log_entry))

# Pytest Hook Integration
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Pytest hook that executes after each test phase.
    Captures results, error messages, and AI-driven explanations.
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":  # actual test execution
        test_name = report.nodeid
        description = item.function.__doc__ or "No description provided"

        if report.failed:
            error_message = str(report.longrepr)
            print("\n=== 🤖 Ollama Failure Analysis ===")
            analysis = analyze_failure_with_ollama(error_message)
            print(analysis)
            log_test(test_name, "FAILED", error_message, analysis, description)

        elif report.passed:
            log_test(test_name, "PASSED", description=description)

        elif report.skipped:
            log_test(test_name, "SKIPPED", description=description)

# Optional direct run
if __name__ == "__main__":
    # Quick local test of the analyzer
    fake_error = "AssertionError: Expected 200 but got 401 at test_login_valid"
    print(analyze_failure_with_ollama(fake_error))