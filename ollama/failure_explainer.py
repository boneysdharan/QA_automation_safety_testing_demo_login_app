import subprocess
import pytest
from datetime import datetime

LOG_FILE = "detailed_test_log.log"
OLLAMA_MODEL = "b3"   # your local Ollama model

def analyze_failure_with_ollama(error_message: str) -> str:
    """
    Send the error message to Ollama for AI-powered analysis.
    """
    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=f"Test failed with error:\n{error_message}\n\nExplain the likely cause and suggest a quick fix:",
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        return f"⚠️ Ollama analysis failed: {e}"

def categorize_test(test_name: str) -> str:
    """
    Determine if test is UI (frontend) or API (backend).
    """
    if "ui" in test_name.lower():
        return "Frontend (UI)"
    elif "api" in test_name.lower() or "moderate" in test_name.lower():
        return "Backend (API)"
    elif "generated" in test_name.lower():
        return "Backend (API, OpenAPI Stub)"
    elif "postman" in test_name.lower():
        return "Backend (API, Postman)"
    else:
        return "Unknown Layer"

def log_test(test_name: str, outcome: str, error_message: str = None, analysis: str = None, description: str = None):
    """
    Append detailed test info to log file.
    """
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n=== Test Report ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===\n")
        f.write(f"Test: {test_name}\n")
        f.write(f"Layer: {categorize_test(test_name)}\n")
        if description:
            f.write(f"Purpose: {description}\n")
        f.write(f"Outcome: {outcome}\n")
        if error_message:
            f.write(f"Error: {error_message}\n")
        if analysis:
            f.write(f"Ollama Analysis:\n{analysis}\n")
        f.write("=" * 70 + "\n")

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook runs after each test phase (setup, call, teardown).
    Captures outcome and adds detailed logs.
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":  # actual test execution, not setup/teardown
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
