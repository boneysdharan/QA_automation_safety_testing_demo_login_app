# Unified AI-Enhanced Pytest Hook for UI Tests (Groq + Ollama + HTML Embedding + Optimized Playwright)
import os
import pytest
import requests
import ollama
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from pytest_html import extras
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright

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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = test_name.replace("::", "__").replace(":", "_").replace("/", "_").replace("\\", "_")
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

# PLAYWRIGHT FIXTURES
@pytest.fixture(scope="session")
def browser():
    """Single shared Chromium browser across all tests."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page_with_video(browser, request):
    """Creates a fresh context per test, reusing global browser."""
    test_name = request.node.name
    context = browser.new_context(
        record_video_dir=None,  # Disable video by default for speed
        viewport={"width": 1366, "height": 768},
    )
    page = context.new_page()
    yield page
    context.close()

# CACHED HTML → PNG TEST CARD GENERATOR
class TestCardGenerator:
    """Single async Playwright context to render HTML→PNG efficiently."""

    def __init__(self):
        self.browser = None
        self.context = None
        self.template_cache = {}
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    async def _init_browser(self):
        if self.browser is None:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(viewport={"width": 800, "height": 600})

    async def _generate_card_async(self, html_snippet: str, output_path: Path):
        await self._init_browser()
        if html_snippet in self.template_cache:
            shutil.copy(self.template_cache[html_snippet], output_path)
            return

        page = await self.context.new_page()
        tmp_html = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        tmp_html.write(html_snippet.encode("utf-8"))
        tmp_html.close()

        await page.goto(f"file:///{tmp_html.name}")
        await page.wait_for_timeout(400)
        await page.screenshot(path=str(output_path))
        self.template_cache[html_snippet] = str(output_path)
        await page.close()

    def generate_card(self, html_snippet: str, output_path: Path):
        self.loop.run_until_complete(self._generate_card_async(html_snippet, output_path))

    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()


card_generator = TestCardGenerator()

def _generate_test_card(title: str, result: str, color: str) -> Path:
    """Generate or reuse a cached test card PNG."""
    html_template = f"""
    <html><head><style>
    body {{
        background-color: {color};
        color: white;
        font-family: Arial, sans-serif;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100vh;
    }}
    h1 {{ font-size: 24px; text-align: center; }}
    </style></head>
    <body><h1>{title}: {result}</h1></body></html>
    """
    output_path = Path(tempfile.gettempdir()) / f"{title.replace(' ', '_')}.png"
    card_generator.generate_card(html_template, output_path)
    return output_path


def pytest_sessionfinish(session, exitstatus):
    """Ensure async Playwright browser is closed."""
    try:
        asyncio.get_event_loop().run_until_complete(card_generator.close())
    except RuntimeError:
        pass

# PYTEST HOOKS
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

def pytest_html_results_table_html(report, data):
    """Enhance HTML report with AI + test summary."""
    if report.when != "call":
        return

    test_name = report.nodeid.split("::")[-1]
    duration = getattr(report, "duration", 0.0)
    status = "✅ Passed" if report.passed else "❌ Failed"
    domain = "http://localhost:8501"

    extra_html = f"""
    <div style='margin-top:15px;padding:12px;background:#f9fafb;
                border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,0.05);'>
        <h4>🧾 Extended Test Summary</h4>
        <p><b>Test name:</b> {test_name}</p>
        <p><b>Status:</b> {status}</p>
        <p><b>Execution time:</b> {duration:.2f}s</p>
        <p><b>Domain:</b> {domain}</p>
    """

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

    if hasattr(report, "extras"):
        report.extras.append(extras.html(extra_html))
    else:
        data.append(extras.html(extra_html))