# Playwright testing
import time
from playwright.sync_api import sync_playwright
import requests

def get_message(page, timeout=10.0):
    """Poll #login-result for up to `timeout` seconds. If empty, return full body text as fallback."""
    locator = page.locator("#login-result")
    end = time.time() + timeout
    while time.time() < end:
        try:
            # If the element exists, inner_text() returns "" when empty.
            if locator.count() > 0:
                txt = locator.inner_text().strip()
                if txt:
                    return txt
        except Exception:
            pass
        time.sleep(0.25)
    # fallback: return body text (helps when Streamlit renders the message elsewhere)
    try:
        return page.inner_text("body").strip()
    except Exception:
        return ""

def test_login_success():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8501")

        # use an input-specific locator to avoid the "show password" button collision
        page.locator("input[aria-label='Username']").fill("admin")
        page.locator("input[aria-label='Password']").fill("password123")
        page.get_by_role("button", name="Login").click()

        msg = get_message(page, timeout=10)
        assert "Welcome, admin" in msg
        browser.close()

def test_login_failure_wrong_credentials():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8501")

        page.locator("input[aria-label='Username']").fill("wrong")
        page.locator("input[aria-label='Password']").fill("bad")
        page.get_by_role("button", name="Login").click()

        msg = get_message(page, timeout=10)
        assert "Invalid credentials" in msg
        browser.close()

def test_login_failure_blank_username():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8501")

        # leave username blank
        page.locator("input[aria-label='Password']").fill("password123")
        page.get_by_role("button", name="Login").click()

        msg = get_message(page, timeout=10)
        assert "Username is required" in msg or "Username and password required" in msg or "Invalid credentials" in msg
        browser.close()

def test_login_failure_blank_password():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8501")

        # leave password blank
        page.locator("input[aria-label='Username']").fill("admin")
        page.get_by_role("button", name="Login").click()

        msg = get_message(page, timeout=10)
        assert "Password is required" in msg or "Username and password required" in msg or "Invalid credentials" in msg
        browser.close()

def test_protected_route_invalid_token():
    # direct API check (unrelated to Streamlit UI)
    resp = requests.get("http://127.0.0.1:8000/api/protected", headers={"Authorization": "Bearer invalid-token"})
    assert resp.status_code == 401
