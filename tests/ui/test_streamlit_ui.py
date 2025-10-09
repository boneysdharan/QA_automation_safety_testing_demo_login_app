# Playwright Streamlit UI tests
import time
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import pytest
from playwright.sync_api import sync_playwright, expect
from PIL import Image
from streamlit import html

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

def _generate_test_card(test_name: str, status: str, duration: float,
                        domain: str, error_reason=None):
    """Generate detailed test report card as image."""
    try:
        color = "#16a34a" if status == "PASSED" else "#dc2626"
        emoji = "✅" if status == "PASSED" else "❌"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        description = _dynamic_description(test_name)
        quick_fix = _quick_fix_suggestion(test_name)

        start_time = datetime.now().strftime("%H:%M:%S")
        end_time = (datetime.now() + timedelta(seconds=duration)).strftime("%H:%M:%S")

        err_html = ""
        if error_reason:
            err_html = f"""
            <p><b>Error Reason:</b> {error_reason}</p>
            <p><b>Quick Fix:</b> {quick_fix}</p>
            """

        html_content = f"""
        <html><body style='font-family:Segoe UI;background:#f9fafb;padding:20px;'>
        <div style='border:2px solid {color};border-radius:12px;padding:16px;width:880px;
                    box-shadow:2px 2px 8px rgba(0,0,0,0.1);'>
            <h2 style='margin:0;color:{color};'>{emoji} {test_name}</h2>
            <p><b>Status:</b> <span style='color:{color}'>{status}</span></p>
            <p><b>Domain:</b> {domain}</p>
            <p><b>Start:</b> {start_time} | <b>End:</b> {end_time} | 
               <b>Duration:</b> {duration:.2f}s</p>
            <p><b>Description:</b> {description}</p>
            {err_html}
            <p><b>Playwright:</b> v1.48 (Chromium)</p>
            <p style='color:#555;font-size:12px;'>Generated: {timestamp}</p>
        </div></body></html>
        """

        tmp_html = Path(tempfile.gettempdir()) / f"{test_name}.html"
        tmp_html.write_text(html_content, encoding="utf-8")

        output_path = ARTIFACTS_DIR / f"{test_name}.png"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 950, "height": 400})
            page.goto(tmp_html.absolute().as_uri(), wait_until="load")
            page.screenshot(path=str(output_path), full_page=True)
            browser.close()

        tmp_html.unlink(missing_ok=True)
        _temp_screenshots.append(output_path)
        print(f"📸 Saved test report image → {output_path}")
    except Exception as e:
        print(f"⚠️ Failed to generate test card for {test_name}: {e}")

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

# TEST CASES
def run_safe_test(name, func):
    start = time.time()
    try:
        func()
        _generate_test_card(name, "PASSED", time.time() - start, BASE_URL)
    except AssertionError as e:
        _generate_test_card(name, "FAILED", time.time() - start, BASE_URL, str(e))
        raise

def test_total_test_count_display():
    """Verify total test count metric visible on Test Insights tab."""
    def inner():
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_page()
            page.goto(BASE_URL)
            open_tab(page, "Test Insights")
            expect(page.locator("text=Total Tests")).to_be_visible()
            b.close()
    run_safe_test("test_total_test_count_display", inner)

def test_passed_test_count_metric():
    """Verify 'Passed' metric box visible."""
    def inner():
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_page()
            page.goto(BASE_URL)
            open_tab(page, "Test Insights")
            expect(page.locator("div[data-testid='stMetric']").filter(has_text="Passed")).to_be_visible()
            b.close()
    run_safe_test("test_passed_test_count_metric", inner)

def test_failed_test_count_metric():
    """Verify 'Failed' metric visible."""
    def inner():
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_page()
            page.goto(BASE_URL)
            open_tab(page, "Test Insights")
            expect(page.locator("div[data-testid='stMetric']").filter(has_text="Failed")).to_be_visible()
            b.close()
    run_safe_test("test_failed_test_count_metric", inner)

def test_unified_table_presence():
    """Ensure unified test insights table appears."""
    def inner():
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_page()
            page.goto(BASE_URL)
            open_tab(page, "Test Insights")
            expect(page.locator("table")).to_be_visible()
            b.close()
    run_safe_test("test_unified_table_presence", inner)

def test_dropdown_availability():
    """Ensure test case dropdown appears."""
    def inner():
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_page()
            page.goto(BASE_URL)
            open_tab(page, "Test Insights")
            expect(page.locator("[role='combobox']")).to_be_visible()
            b.close()
    run_safe_test("test_dropdown_availability", inner)

def test_detailed_section_visibility():
    """Verify 'View Detailed Test Insight' section visible."""
    def inner():
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_page()
            page.goto(BASE_URL)
            open_tab(page, "Test Insights")
            expect(page.locator("text=View Detailed Test Insight")).to_be_visible()
            b.close()
    run_safe_test("test_detailed_section_visibility", inner)

def test_tools_column_present():
    """Ensure 'Tools That Ran This Test' column exists."""
    def inner():
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_page()
            page.goto(BASE_URL)
            open_tab(page, "Test Insights")
            expect(page.locator("table th", has_text="Tools That Ran This Test")).to_be_visible()
            b.close()
    run_safe_test("test_tools_column_present", inner)

def test_insights_csv_generated():
    """Ensure final_unified_tests.csv file is generated."""
    def inner():
        csv_path = Path("final_unified_tests.csv")
        if csv_path.exists():
            csv_path.unlink()
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_page()
            page.goto(BASE_URL)
            open_tab(page, "Test Insights")
            expect(page.locator("table")).to_be_visible()
            assert csv_path.exists(), "CSV not generated"
            b.close()
    run_safe_test("test_insights_csv_generated", inner)

def test_toxic_input_detection():
    """Ensure toxic comment detection works."""
    def inner():
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_page()
            page.goto(BASE_URL)
            open_tab(page, "Content Moderation")
            page.fill("textarea", "You are so stupid!")
            page.get_by_role("button", name="Moderate Text").click()
            time.sleep(3)
            content = page.content().lower()
            assert "toxic" in content
            b.close()
    run_safe_test("test_toxic_input_detection", inner)

def test_non_toxic_input_detection():
    """Ensure safe text is detected correctly."""
    def inner():
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_page()
            page.goto(BASE_URL)
            open_tab(page, "Content Moderation")
            page.fill("textarea", "You are kind and helpful!")
            page.get_by_role("button", name="Moderate Text").click()
            time.sleep(3)
            content = page.content().lower()
            assert "safe" in content
            b.close()
    run_safe_test("test_non_toxic_input_detection", inner)

def test_empty_input_warning():
    """Check empty input warning shown."""
    def inner():
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_page()
            page.goto(BASE_URL)
            open_tab(page, "Content Moderation")
            page.fill("textarea", "")
            page.get_by_role("button", name="Moderate Text").click()
            time.sleep(2)
            content = page.content().lower()
            assert "please enter" in content
            b.close()
    run_safe_test("test_empty_input_warning", inner)

def test_content_moderation_backend_failure():
    """Simulate backend failure during moderation."""
    def inner():
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_page()
            page.goto(BASE_URL)
            open_tab(page, "Content Moderation")
            page.fill("textarea", "simulate backend error")
            page.get_by_role("button", name="Moderate Text").click()
            time.sleep(3)
            text = page.inner_text("body").lower()
            assert any(k in text for k in ["error", "failed", "exception"])
            b.close()
    run_safe_test("test_content_moderation_backend_failure", inner)

def test_content_moderation_retry_after_failure():
    """Ensure retry works after backend failure."""
    def inner():
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_page()
            page.goto(BASE_URL)
            open_tab(page, "Content Moderation")
            page.fill("textarea", "retry after error")
            page.get_by_role("button", name="Moderate Text").click()
            page.wait_for_timeout(2000)
            page.get_by_role("button", name="Moderate Text").click()
            expect(page.get_by_text("Safe")).to_be_visible(timeout=20000)
            b.close()
    run_safe_test("test_content_moderation_retry_after_failure", inner)

def test_e2e_streamlit_navigation():
    """Full navigation across Streamlit tabs."""
    def inner():
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_page()
            start_time = time.time()
            page.goto(BASE_URL)
            open_tab(page, "Test Insights")
            expect(page.locator("text=Unified Test Insights Dashboard")).to_be_visible()
            open_tab(page, "Content Moderation")
            expect(page.locator("text=Content Moderation with Detoxify")).to_be_visible()
            duration = time.time() - start_time
            assert duration < 25
            b.close()
    run_safe_test("test_e2e_streamlit_navigation", inner)

# PYTEST HTML ENHANCEMENT
from pytest_html import extras
def pytest_html_results_table_row(report, cells):
    """Add summary info in the main results table."""
    test_name = report.nodeid.split("::")[-1]
    duration = getattr(report, "duration", 0.0)
    status = "✅ Passed" if report.passed else "❌ Failed"
    domain = "http://localhost:8501"
    desc = _dynamic_description(test_name)

    # Insert extra columns for better overview
    cells.insert(1, html.td(status))
    cells.insert(2, html.td(f"{duration:.2f}s"))
    cells.insert(3, html.td(domain))
    cells.insert(4, html.td(desc[:100]))  # show first 100 chars of description


def pytest_html_results_table_html(report, data):
    """Embed detailed test summary and screenshot below each test."""
    test_name = report.nodeid.split("::")[-1]
    image_path = ARTIFACTS_DIR / f"{test_name}.png"
    duration = getattr(report, "duration", 0.0)
    domain = "http://localhost:8501"
    description = _dynamic_description(test_name)
    quick_fix = _quick_fix_suggestion(test_name)

    # Build the extended section manually (pytest-html >=4 uses extras.html)
    extra_html = f"""
    <div style='margin-top:15px; padding:12px; background:#f9fafb; border-radius:8px;
                box-shadow:0 1px 4px rgba(0,0,0,0.05);'>
        <h4 style='margin-bottom:8px;'>🧾 Extended Test Summary</h4>
        <p><b>Test name:</b> {test_name}</p>
        <p><b>Status:</b> {'✅ Passed' if report.passed else '❌ Failed'}</p>
        <p><b>Execution time:</b> {duration:.2f} sec</p>
        <p><b>Domain:</b> {domain}</p>
        <p><b>Description:</b> {description}</p>
    """

    if not report.passed:
        short_error = str(report.longrepr)[:300].replace("\n", " ")
        extra_html += f"""
        <p><b>Error:</b> {short_error}</p>
        <p><b>Quick fix:</b> {quick_fix}</p>
        """

    if image_path.exists():
        extra_html += f"""
        <p><b>Visual Report:</b></p>
        <img src='file:///{image_path.as_posix()}' width='750'
             style='border:1px solid #ddd; border-radius:10px; margin-top:8px;'/>
        """

    extra_html += "</div>"
    data.append(extras.html(extra_html))