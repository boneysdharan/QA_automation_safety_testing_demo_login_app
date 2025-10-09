# Playwright Streamlit UI Tests
import time
from datetime import datetime
from pathlib import Path
import tempfile
import pytest
from playwright.sync_api import sync_playwright, expect
import asyncio, nest_asyncio
from playwright.async_api import async_playwright
from streamlit import html
from pytest_html import extras
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning, message="coroutine .* was never awaited")

BASE_URL = "http://localhost:8501"
ARTIFACTS_DIR = Path(r"D:\BONEYS\WEB\WORK\task_1\artifacts\playwright_streamlit_ui_tests")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR = ARTIFACTS_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR = ARTIFACTS_DIR / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
_temp_screenshots = []

# Helper Functions
def _dynamic_description(name: str):
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

# Video Save Helper
def _save_test_video(context, test_name: str):
    """Rename Playwright's recorded video to match test name."""
    try:
        # Close context to finalize the video
        context.close()
        time.sleep(1)
        for f in VIDEOS_DIR.glob("*.webm"):
            if f.name != f"{test_name}.webm" and f.stat().st_mtime > time.time() - 30:
                new_path = VIDEOS_DIR / f"{test_name}.webm"
                f.rename(new_path)
                print(f"🎥 Saved video for {test_name} → {new_path}")
                return
        print(f"⚠️ No video found for {test_name}.")
    except Exception as e:
        print(f"⚠️ Could not rename video for {test_name}: {e}")

# Test Card Generator
def _generate_test_card(test_name: str, status: str, duration: float, domain: str, error_reason=None):
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
            output_path = IMAGES_DIR / f"{test_name}.png"

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
        loop.run_until_complete(_async_generate())

# Sidebar Navigation
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

# Shared Browser Fixture
@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

# Helper Wrapper
def run_safe_test(name, func, browser):
    start = time.time()
    # Each test gets its own context so video files are isolated
    context = browser.new_context(
        record_video_dir=str(VIDEOS_DIR),
        record_video_size={"width": 1366, "height": 768},
        viewport={"width": 1366, "height": 768},
    )
    page = context.new_page()

    try:
        func(page)
        _generate_test_card(name, "PASSED", time.time() - start, BASE_URL)
    except AssertionError as e:
        _generate_test_card(name, "FAILED", time.time() - start, BASE_URL, str(e))
        raise
    finally:
        _save_test_video(context, name)

# Test Cases

# Test Insights Tab
def test_total_test_count_display(browser):
    """Verify total test count metric visible on Test Insights tab."""
    def inner(page):
        page.goto(BASE_URL)
        open_tab(page, "Test Insights")
        expect(page.locator("text=Total Tests")).to_be_visible()
    run_safe_test("test_total_test_count_display", inner, browser)

def test_passed_test_count_metric(browser):
    """Verify 'Passed' metric box visible."""
    def inner(page):
        page.goto(BASE_URL)
        open_tab(page, "Test Insights")
        expect(page.locator("div[data-testid='stMetric']").filter(has_text="Passed")).to_be_visible()
    run_safe_test("test_passed_test_count_metric", inner, browser)

def test_failed_test_count_metric(browser):
    """Verify 'Failed' metric visible."""
    def inner(page):
        page.goto(BASE_URL)
        open_tab(page, "Test Insights")
        expect(page.locator("div[data-testid='stMetric']").filter(has_text="Failed")).to_be_visible()
    run_safe_test("test_failed_test_count_metric", inner, browser)

def test_unified_table_presence(browser):
    """Ensure unified test insights table appears."""
    def inner(page):
        page.goto(BASE_URL)
        open_tab(page, "Test Insights")
        expect(page.locator("table")).to_be_visible()
    run_safe_test("test_unified_table_presence", inner, browser)

def test_dropdown_availability(browser):
    """Ensure test case dropdown appears."""
    def inner(page):
        page.goto(BASE_URL)
        open_tab(page, "Test Insights")
        expect(page.locator("[role='combobox']")).to_be_visible()
    run_safe_test("test_dropdown_availability", inner, browser)

def test_detailed_section_visibility(browser):
    """Verify 'View Detailed Test Insight' section visible."""
    def inner(page):
        page.goto(BASE_URL)
        open_tab(page, "Test Insights")
        expect(page.locator("text=View Detailed Test Insight")).to_be_visible()
    run_safe_test("test_detailed_section_visibility", inner, browser)

def test_tools_column_present(browser):
    """Ensure 'Tools That Ran This Test' column exists."""
    def inner(page):
        page.goto(BASE_URL)
        open_tab(page, "Test Insights")
        expect(page.locator("table th", has_text="Tools That Ran This Test")).to_be_visible()
    run_safe_test("test_tools_column_present", inner, browser)

def test_insights_csv_generated(browser):
    """Ensure final_unified_tests.csv file is generated."""
    def inner(page):
        csv_path = Path("final_unified_tests.csv")
        if csv_path.exists():
            csv_path.unlink()
        page.goto(BASE_URL)
        open_tab(page, "Test Insights")
        expect(page.locator("table")).to_be_visible()
        assert csv_path.exists(), "CSV not generated"
    run_safe_test("test_insights_csv_generated", inner, browser)

# Content Moderation Tab
def test_toxic_input_detection(browser):
    """Ensure toxic comment detection works."""
    def inner(page):
        page.goto(BASE_URL)
        open_tab(page, "Content Moderation")
        page.fill("textarea", "You are so stupid!")
        page.get_by_role("button", name="Moderate Text").click()
        page.wait_for_selector("text=toxic", timeout=15000)
    run_safe_test("test_toxic_input_detection", inner, browser)

def test_non_toxic_input_detection(browser):
    """Ensure safe text is detected correctly."""
    def inner(page):
        page.goto(BASE_URL)
        open_tab(page, "Content Moderation")
        page.fill("textarea", "You are kind and helpful!")
        page.get_by_role("button", name="Moderate Text").click()
        page.wait_for_selector("text=safe", timeout=15000)
    run_safe_test("test_non_toxic_input_detection", inner, browser)

def test_empty_input_warning(browser):
    """Check empty input warning shown."""
    def inner(page):
        page.goto(BASE_URL)
        open_tab(page, "Content Moderation")
        page.fill("textarea", "")
        page.get_by_role("button", name="Moderate Text").click()
        page.wait_for_timeout(2000)
        content = page.content().lower()
        assert "please enter" in content
    run_safe_test("test_empty_input_warning", inner, browser)

def test_content_moderation_backend_failure(browser):
    """Simulate backend failure during moderation."""
    def inner(page):
        page.goto(BASE_URL)
        open_tab(page, "Content Moderation")
        page.fill("textarea", "simulate backend error")
        page.get_by_role("button", name="Moderate Text").click()
        page.wait_for_timeout(3000)
        content = page.content().lower()
        assert any(k in content for k in ["error", "failed", "exception", "try again"])
    run_safe_test("test_content_moderation_backend_failure", inner, browser)

def test_content_moderation_retry_after_failure(browser):
    """Ensure retry works after backend failure."""
    def inner(page):
        page.goto(BASE_URL)
        open_tab(page, "Content Moderation")
        page.fill("textarea", "retry after error")
        page.get_by_role("button", name="Moderate Text").click()
        page.wait_for_timeout(3000)
        page.get_by_role("button", name="Moderate Text").click()
        expect(page.get_by_text("Safe")).to_be_visible(timeout=20000)
    run_safe_test("test_content_moderation_retry_after_failure", inner, browser)

# E2E Navigation
def test_e2e_streamlit_navigation(browser):
    """Full navigation across Streamlit tabs."""
    def inner(page):
        page.goto(BASE_URL)
        open_tab(page, "Test Insights")
        expect(page.locator("text=Unified Test Insights Dashboard")).to_be_visible()
        open_tab(page, "Content Moderation")
        expect(page.locator("text=Content Moderation with Detoxify")).to_be_visible()
    run_safe_test("test_e2e_streamlit_navigation", inner, browser)

# Pytest HTML Enhancements
def pytest_html_results_table_row(report, cells):
    test_name = report.nodeid.split("::")[-1]
    duration = getattr(report, "duration", 0.0)
    status = "✅ Passed" if report.passed else "❌ Failed"
    desc = _dynamic_description(test_name)
    cells.insert(1, html.td(status))
    cells.insert(2, html.td(f"{duration:.2f}s"))
    cells.insert(3, html.td(BASE_URL))
    cells.insert(4, html.td(desc[:100]))

def pytest_html_results_table_html(report, data):
    test_name = report.nodeid.split("::")[-1]
    image_path = IMAGES_DIR / f"{test_name}.png"
    video_path = VIDEOS_DIR / f"{test_name}.webm"
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
    if video_path.exists():
        extra_html += f"<p><b>🎥 Test Video:</b></p><video width='750' controls style='border-radius:10px;'><source src='file:///{video_path.as_posix()}' type='video/webm'></video>"
    extra_html += "</div>"
    data.append(extras.html(extra_html))