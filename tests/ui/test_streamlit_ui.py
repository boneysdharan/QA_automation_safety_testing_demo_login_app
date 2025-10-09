# Playwright Streamlit UI Tests
import time
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import pytest
from playwright.sync_api import sync_playwright, expect
from PIL import Image
from streamlit import html
from pytest_html import extras

BASE_URL = "http://localhost:8501"
ARTIFACTS_DIR = Path(r"D:\BONEYS\WEB\WORK\task_1\artifacts\playwright_streamlit_ui_tests")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
_temp_screenshots = []

# Helper Functions
def _dynamic_description(name: str):
    """Generate description text automatically."""
    if callable(globals().get(name)) and globals()[name].__doc__:
        return globals()[name].__doc__.strip()
    n = name.replace("test_", "").replace("_", " ").capitalize()
    return f"Automatically validates {n} behavior."

def _quick_fix_suggestion(name: str):
    fixes = {
        "insight": "Check the CSV generation logic and UI render timing.",
        "moderation": "Validate backend API response and front-end state updates.",
        "dropdown": "Ensure dropdown selector rendering and data binding.",
        "metric": "Confirm Streamlit metric containers are loaded correctly.",
        "table": "Ensure unified table renders and is visible in UI.",
        "navigation": "Check sidebar routing and tab handling logic.",
    }
    for k, msg in fixes.items():
        if k in name.lower():
            return msg
    return "Re-run this test in debug mode for more detailed diagnostics."

import nest_asyncio
import asyncio
from playwright.async_api import async_playwright

def _generate_test_card(test_name: str, status: str, duration: float, domain: str, error_reason=None):
    """Generate detailed HTML-based image card asynchronously (safe for nested loops)."""
    async def _async_generate():
        try:
            color = "#16a34a" if status == "PASSED" else "#dc2626"
            emoji = "✅" if status == "PASSED" else "❌"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            description = _dynamic_description(test_name)
            quick_fix = _quick_fix_suggestion(test_name)
            err_html = ""
            if error_reason:
                err_html = f"<p><b>Error Reason:</b> {error_reason}</p><p><b>Quick Fix:</b> {quick_fix}</p>"

            html_content = f"""
            <html><body style='font-family:Segoe UI;background:#f9fafb;padding:20px;'>
            <div style='border:2px solid {color};border-radius:12px;padding:16px;width:880px;
                        box-shadow:2px 2px 8px rgba(0,0,0,0.1);'>
                <h2 style='margin:0;color:{color};'>{emoji} {test_name}</h2>
                <p><b>Status:</b> <span style='color:{color}'>{status}</span></p>
                <p><b>Domain:</b> {domain}</p>
                <p><b>Duration:</b> {duration:.2f}s</p>
                <p><b>Description:</b> {description}</p>
                {err_html}
                <p><b>Generated:</b> {timestamp}</p>
            </div></body></html>
            """

            tmp_html = Path(tempfile.gettempdir()) / f"{test_name}.html"
            tmp_html.write_text(html_content, encoding="utf-8")

            output_path = ARTIFACTS_DIR / f"{test_name}.png"
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                await page.goto(tmp_html.absolute().as_uri(), wait_until="load")
                await page.screenshot(path=str(output_path), full_page=True)
                await context.close()
                await browser.close()

            tmp_html.unlink(missing_ok=True)
            _temp_screenshots.append(output_path)
            print(f"📸 Saved test report image → {output_path}")

        except Exception as e:
            print(f"⚠️ Failed to generate test card for {test_name}: {e}")

    try:
        asyncio.run(_async_generate())
    except RuntimeError:
        nest_asyncio.apply()
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(_async_generate())
        except RuntimeError:
            # Handle already running loop cleanly
            asyncio.ensure_future(_async_generate())

def wait_for_sidebar(page):
    selectors = [
        "section[data-testid='stSidebar']",
        "div[data-testid='stSidebar']",
        "aside",
    ]
    for sel in selectors:
        try:
            page.wait_for_selector(sel, timeout=10000)
            return sel
        except:
            continue
    raise Exception("Sidebar not found.")

def open_tab(page, tab_name):
    sel = wait_for_sidebar(page)
    assert sel is not None
    page.locator(f"label:has-text('{tab_name}')").click()

# Shared Browser technique
@pytest.fixture(scope="module")
def browser_context():
    """Launch a shared browser once for all tests."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        yield context
        context.close()
        browser.close()

# Helper Wrapper
def run_safe_test(name, func, browser_context):
    start = time.time()
    try:
        func(browser_context)
        _generate_test_card(name, "PASSED", time.time() - start, BASE_URL)
    except AssertionError as e:
        _generate_test_card(name, "FAILED", time.time() - start, BASE_URL, str(e))
        raise

# Tests
def test_total_test_count_display(browser_context):
    """Verify total test count metric visible on Test Insights tab."""
    def inner(ctx):
        page = ctx.new_page()
        page.goto(BASE_URL)
        open_tab(page, "Test Insights")
        expect(page.locator("text=Total Tests")).to_be_visible()
        page.close()
    run_safe_test("test_total_test_count_display", inner, browser_context)

def test_passed_test_count_metric(browser_context):
    """Verify 'Passed' metric box visible."""
    def inner(ctx):
        page = ctx.new_page()
        page.goto(BASE_URL)
        open_tab(page, "Test Insights")
        expect(page.locator("div[data-testid='stMetric']").filter(has_text="Passed")).to_be_visible()
        page.close()
    run_safe_test("test_passed_test_count_metric", inner, browser_context)

def test_failed_test_count_metric(browser_context):
    """Verify 'Failed' metric visible."""
    def inner(ctx):
        page = ctx.new_page()
        page.goto(BASE_URL)
        open_tab(page, "Test Insights")
        expect(page.locator("div[data-testid='stMetric']").filter(has_text="Failed")).to_be_visible()
        page.close()
    run_safe_test("test_failed_test_count_metric", inner, browser_context)

def test_unified_table_presence(browser_context):
    """Ensure unified test insights table appears."""
    def inner(ctx):
        page = ctx.new_page()
        page.goto(BASE_URL)
        open_tab(page, "Test Insights")
        expect(page.locator("table")).to_be_visible()
        page.close()
    run_safe_test("test_unified_table_presence", inner, browser_context)

def test_dropdown_availability(browser_context):
    """Ensure test case dropdown appears."""
    def inner(ctx):
        page = ctx.new_page()
        page.goto(BASE_URL)
        open_tab(page, "Test Insights")
        expect(page.locator("[role='combobox']")).to_be_visible()
        page.close()
    run_safe_test("test_dropdown_availability", inner, browser_context)

def test_detailed_section_visibility(browser_context):
    """Verify 'View Detailed Test Insight' section visible."""
    def inner(ctx):
        page = ctx.new_page()
        page.goto(BASE_URL)
        open_tab(page, "Test Insights")
        expect(page.locator("text=View Detailed Test Insight")).to_be_visible()
        page.close()
    run_safe_test("test_detailed_section_visibility", inner, browser_context)

def test_tools_column_present(browser_context):
    """Ensure 'Tools That Ran This Test' column exists."""
    def inner(ctx):
        page = ctx.new_page()
        page.goto(BASE_URL)
        open_tab(page, "Test Insights")
        expect(page.locator("table th", has_text="Tools That Ran This Test")).to_be_visible()
        page.close()
    run_safe_test("test_tools_column_present", inner, browser_context)

def test_insights_csv_generated(browser_context):
    """Ensure final_unified_tests.csv file is generated."""
    def inner(ctx):
        csv_path = Path("final_unified_tests.csv")
        if csv_path.exists():
            csv_path.unlink()
        page = ctx.new_page()
        page.goto(BASE_URL)
        open_tab(page, "Test Insights")
        expect(page.locator("table")).to_be_visible()
        assert csv_path.exists(), "CSV not generated"
        page.close()
    run_safe_test("test_insights_csv_generated", inner, browser_context)

def test_toxic_input_detection(browser_context):
    """Ensure toxic comment detection works."""
    def inner(ctx):
        page = ctx.new_page()
        page.goto(BASE_URL)
        open_tab(page, "Content Moderation")
        page.fill("textarea", "You are so stupid!")
        page.get_by_role("button", name="Moderate Text").click()
        time.sleep(3)
        content = page.content().lower()
        assert "toxic" in content
        page.close()
    run_safe_test("test_toxic_input_detection", inner, browser_context)

def test_non_toxic_input_detection(browser_context):
    """Ensure safe text is detected correctly."""
    def inner(ctx):
        page = ctx.new_page()
        page.goto(BASE_URL)
        open_tab(page, "Content Moderation")
        page.fill("textarea", "You are kind and helpful!")
        page.get_by_role("button", name="Moderate Text").click()
        # Wait until the "safe" text appears instead of sleeping
        page.wait_for_selector("text=safe", timeout=15000)
        content = page.content().lower()
        assert "safe" in content
        page.close()
    run_safe_test("test_non_toxic_input_detection", inner, browser_context)

def test_empty_input_warning(browser_context):
    """Check empty input warning shown."""
    def inner(ctx):
        page = ctx.new_page()
        page.goto(BASE_URL)
        open_tab(page, "Content Moderation")
        page.fill("textarea", "")
        page.get_by_role("button", name="Moderate Text").click()
        time.sleep(2)
        content = page.content().lower()
        assert "please enter" in content
        page.close()
    run_safe_test("test_empty_input_warning", inner, browser_context)

def test_content_moderation_backend_failure(browser_context):
    """Simulate backend failure during moderation."""
    def inner(ctx):
        page = ctx.new_page()
        page.goto(BASE_URL)
        open_tab(page, "Content Moderation")
        page.fill("textarea", "simulate backend error")
        page.get_by_role("button", name="Moderate Text").click()
        # Wait up to 30s for any possible failure message to appear
        try:
            page.wait_for_selector("text=error, text=failed, text=exception, text=try again, text=something went wrong", timeout=30000)
        except:
            pass  # fallback to full page scan
        text = page.inner_text("body").lower()
        # Broaden detection to catch various failure patterns
        failure_indicators = ["error", "failed", "exception", "try again", "something went wrong"]
        assert any(k in text for k in failure_indicators), f"No failure message found in: {text[:300]}"
        page.close()

    run_safe_test("test_content_moderation_backend_failure", inner, browser_context)

def test_content_moderation_retry_after_failure(browser_context):
    """Ensure retry works after backend failure."""
    def inner(ctx):
        page = ctx.new_page()
        page.goto(BASE_URL)
        open_tab(page, "Content Moderation")
        page.fill("textarea", "retry after error")
        page.get_by_role("button", name="Moderate Text").click()
        page.wait_for_timeout(2000)
        page.get_by_role("button", name="Moderate Text").click()
        expect(page.get_by_text("Safe")).to_be_visible(timeout=20000)
        page.close()
    run_safe_test("test_content_moderation_retry_after_failure", inner, browser_context)

def test_e2e_streamlit_navigation(browser_context):
    """Full navigation across Streamlit tabs."""
    def inner(ctx):
        page = ctx.new_page()
        start_time = time.time()
        page.goto(BASE_URL)
        open_tab(page, "Test Insights")
        expect(page.locator("text=Unified Test Insights Dashboard")).to_be_visible()
        open_tab(page, "Content Moderation")
        expect(page.locator("text=Content Moderation with Detoxify")).to_be_visible()
        assert (time.time() - start_time) < 25
        page.close()
    run_safe_test("test_e2e_streamlit_navigation", inner, browser_context)

#PYTEST HTML ENHANCEMENTS
def pytest_html_results_table_row(report, cells):
    test_name = report.nodeid.split("::")[-1]
    duration = getattr(report, "duration", 0.0)
    status = "✅ Passed" if report.passed else "❌ Failed"
    domain = BASE_URL
    desc = _dynamic_description(test_name)
    cells.insert(1, html.td(status))
    cells.insert(2, html.td(f"{duration:.2f}s"))
    cells.insert(3, html.td(domain))
    cells.insert(4, html.td(desc[:100]))

def pytest_html_results_table_html(report, data):
    test_name = report.nodeid.split("::")[-1]
    image_path = ARTIFACTS_DIR / f"{test_name}.png"
    duration = getattr(report, "duration", 0.0)
    description = _dynamic_description(test_name)
    quick_fix = _quick_fix_suggestion(test_name)
    extra_html = f"""
    <div style='margin-top:15px;padding:12px;background:#f9fafb;border-radius:8px;
                box-shadow:0 1px 4px rgba(0,0,0,0.05);'>
        <h4>🧾 Extended Test Summary</h4>
        <p><b>Test name:</b> {test_name}</p>
        <p><b>Status:</b> {'✅ Passed' if report.passed else '❌ Failed'}</p>
        <p><b>Execution time:</b> {duration:.2f} sec</p>
        <p><b>Domain:</b> {BASE_URL}</p>
        <p><b>Description:</b> {description}</p>
    """
    if not report.passed:
        short_error = str(report.longrepr)[:300].replace("\n", " ")
        extra_html += f"<p><b>Error:</b> {short_error}</p><p><b>Quick fix:</b> {quick_fix}</p>"
    if image_path.exists():
        extra_html += f"<p><b>Visual Report:</b></p><img src='file:///{image_path.as_posix()}' width='750' style='border:1px solid #ddd;border-radius:10px;'/>"
    extra_html += "</div>"
    data.append(extras.html(extra_html))

import warnings #completely harmless only nuisance
warnings.filterwarnings("ignore", category=RuntimeWarning, message="coroutine .* was never awaited")