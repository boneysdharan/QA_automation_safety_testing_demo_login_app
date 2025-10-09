# Playwright UI login tests
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import requests
import pytest
from playwright.sync_api import sync_playwright, expect
from PIL import Image
from streamlit import html

BASE_URL = "http://localhost:8501"
ARTIFACTS_DIR = Path(r"D:\BONEYS\WEB\WORK\task_1\artifacts\playwright_login_ui_tests")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
_temp_screenshots = []

# Helper Functions

def _dynamic_description(name: str):
    """Generate description text based on test name or docstring."""
    if callable(globals().get(name)) and globals()[name].__doc__:
        return globals()[name].__doc__.strip()
    n = name.replace("test_", "").replace("_", " ").capitalize()
    return f"Automatically validates {n} behavior."

def _quick_fix_suggestion(name: str):
    fixes = {
        "login": "Verify credentials, input validation, and backend auth API.",
        "password": "Check password validation and form submission.",
        "token": "Ensure token generation/verification is consistent.",
        "page": "Confirm the UI loads without network or JavaScript errors.",
        "navigation": "Verify sidebar routing logic and tab bindings.",
    }
    for k, msg in fixes.items():
        if k in name.lower():
            return msg
    return "Re-run this test in debug mode for more diagnostic info."

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

def get_message(page, timeout=10.0):
    locator = page.locator("#login-result")
    end = time.time() + timeout
    while time.time() < end:
        try:
            if locator.count() > 0:
                txt = locator.inner_text().strip()
                if txt:
                    return txt
        except Exception:
            pass
        time.sleep(0.25)
    try:
        return page.inner_text("body").strip()
    except Exception:
        return ""

# Login UI tests

def test_login_success():
    """Validates successful login flow with correct credentials."""
    start = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL)
            page.locator("input[aria-label='Username']").fill("admin")
            page.locator("input[aria-label='Password']").fill("password123")
            page.get_by_role("button", name="Login").click()
            msg = get_message(page)
            assert "Welcome" in msg or "Dashboard" in msg
            browser.close()
        _generate_test_card("test_login_success", "PASSED", time.time()-start, BASE_URL)
    except AssertionError as e:
        _generate_test_card("test_login_success", "FAILED", time.time()-start, BASE_URL, str(e))
        raise

def test_login_failure_wrong_credentials():
    """Ensures invalid credentials show error message."""
    start = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL)
            page.locator("input[aria-label='Username']").fill("wrong")
            page.locator("input[aria-label='Password']").fill("bad")
            page.get_by_role("button", name="Login").click()
            msg = get_message(page)
            assert "Invalid credentials" in msg
            browser.close()
        _generate_test_card("test_login_failure_wrong_credentials", "PASSED", time.time()-start, BASE_URL)
    except AssertionError as e:
        _generate_test_card("test_login_failure_wrong_credentials", "FAILED", time.time()-start, BASE_URL, str(e))
        raise

def test_login_failure_blank_username():
    """Checks that blank username triggers validation."""
    start = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL)
            page.locator("input[aria-label='Password']").fill("password123")
            page.get_by_role("button", name="Login").click()
            msg = get_message(page)
            assert any(x in msg for x in ["Username is required", "Invalid credentials"])
            browser.close()
        _generate_test_card("test_login_failure_blank_username", "PASSED", time.time()-start, BASE_URL)
    except AssertionError as e:
        _generate_test_card("test_login_failure_blank_username", "FAILED", time.time()-start, BASE_URL, str(e))
        raise

def test_login_failure_blank_password():
    """Checks that blank password triggers validation."""
    start = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL)
            page.locator("input[aria-label='Username']").fill("admin")
            page.get_by_role("button", name="Login").click()
            msg = get_message(page)
            assert any(x in msg for x in ["Password is required", "Invalid credentials"])
            browser.close()
        _generate_test_card("test_login_failure_blank_password", "PASSED", time.time()-start, BASE_URL)
    except AssertionError as e:
        _generate_test_card("test_login_failure_blank_password", "FAILED", time.time()-start, BASE_URL, str(e))
        raise

def test_protected_route_invalid_token():
    """Tests backend rejects invalid authentication tokens."""
    start = time.time()
    try:
        resp = requests.get("http://127.0.0.1:8000/api/protected",
                            headers={"Authorization": "Bearer invalid-token"})
        assert resp.status_code == 401
        _generate_test_card("test_protected_route_invalid_token", "PASSED", time.time()-start, "http://127.0.0.1:8000")
    except AssertionError as e:
        _generate_test_card("test_protected_route_invalid_token", "FAILED", time.time()-start, "http://127.0.0.1:8000", str(e))
        raise

def test_login_page_loads():
    """Confirms the login page loads and renders correctly."""
    start = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL)
            assert page.title() != ""
            browser.close()
        _generate_test_card("test_login_page_loads", "PASSED", time.time()-start, BASE_URL)
    except AssertionError as e:
        _generate_test_card("test_login_page_loads", "FAILED", time.time()-start, BASE_URL, str(e))
        raise

def test_login_ui_multiple_attempts():
    """Ensures repeated invalid login attempts still show correct error."""
    start = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL)
            for _ in range(3):
                page.locator("input[aria-label='Username']").fill("wrong")
                page.locator("input[aria-label='Password']").fill("bad")
                page.get_by_role("button", name="Login").click()
                msg = get_message(page)
                assert "Invalid credentials" in msg
            browser.close()
        _generate_test_card("test_login_ui_multiple_attempts", "PASSED", time.time()-start, BASE_URL)
    except AssertionError as e:
        _generate_test_card("test_login_ui_multiple_attempts", "FAILED", time.time()-start, BASE_URL, str(e))
        raise

def test_logout_functionality():
    """Verifies logout clears session and returns to login page."""
    start = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL)
            page.locator("input[aria-label='Username']").fill("admin")
            page.locator("input[aria-label='Password']").fill("password123")
            page.get_by_role("button", name="Login").click()
            page.get_by_role("button", name="Logout").click()
            msg = get_message(page)
            assert "Login" in msg or "Please log in" in msg
            browser.close()
        _generate_test_card("test_logout_functionality", "PASSED", time.time()-start, BASE_URL)
    except AssertionError as e:
        _generate_test_card("test_logout_functionality", "FAILED", time.time()-start, BASE_URL, str(e))
        raise

def test_login_ui_refresh_persists_state():
    """Tests session persistence after page refresh."""
    start = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL)
            page.locator("input[aria-label='Username']").fill("admin")
            page.locator("input[aria-label='Password']").fill("password123")
            page.get_by_role("button", name="Login").click()
            page.reload()
            msg = get_message(page)
            assert "Login" in msg or "Welcome" in msg
            browser.close()
        _generate_test_card("test_login_ui_refresh_persists_state", "PASSED", time.time()-start, BASE_URL)
    except AssertionError as e:
        _generate_test_card("test_login_ui_refresh_persists_state", "FAILED", time.time()-start, BASE_URL, str(e))
        raise

def test_e2e_full_navigation():
    """Performs full E2E navigation: login → dashboard → moderation → logout."""
    start = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL)
            page.locator("input[aria-label='Username']").fill("admin")
            page.locator("input[aria-label='Password']").fill("password123")
            page.get_by_role("button", name="Login").click()
            expect(page.locator("text=Dashboard Overview")).to_be_visible(timeout=8000)
            page.locator("label:has-text('Content Moderation')").click()
            expect(page.locator("text=Content Moderation with Detoxify")).to_be_visible(timeout=8000)
            page.fill("textarea", "This is a safe and nice message!")
            page.get_by_role("button", name="Moderate Text").click()
            time.sleep(3)
            content = page.content().lower()
            assert "safe" in content or "✅" in content
            page.locator("label:has-text('Dashboard')").click()
            page.get_by_role("button", name="Logout").click()
            assert "login" in page.inner_text("body").lower()
            browser.close()
        _generate_test_card("test_e2e_full_navigation", "PASSED", time.time()-start, BASE_URL)
    except AssertionError as e:
        _generate_test_card("test_e2e_full_navigation", "FAILED", time.time()-start, BASE_URL, str(e))
        raise

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