import time
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://localhost:8501"

def wait_for_sidebar(page):
    """Wait for Streamlit sidebar across multiple possible DOM structures."""
    selectors = [
        "section[data-testid='stSidebar']",
        "div[data-testid='stSidebar']",
        "aside",
    ]
    for selector in selectors:
        try:
            page.wait_for_selector(selector, timeout=10000)
            return selector
        except:
            continue
    raise Exception("Sidebar not found — Streamlit may still be loading")

def test_streamlit_test_insights():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL)
        page.wait_for_load_state("domcontentloaded")

        sidebar_selector = wait_for_sidebar(page)
        print(f"✅ Sidebar detected using selector: {sidebar_selector}")

        # Navigate to Test Insights
        page.locator("label:has-text('Test Insights')").click()
        page.wait_for_selector("text=Unified Test Insights Dashboard", timeout=15000)

        # Screenshot proof
        page.screenshot(path="artifacts/streamlit-test-insights.png")

        # ✅ Check metrics (use non-strict filters)
        metric_block = page.locator("div[data-testid='stMetric']")
        expect(metric_block.filter(has_text="Total Tests")).to_have_count(1)
        expect(metric_block.filter(has_text="Passed")).to_have_count(1)

        print("✅ Metric section validated successfully")

        browser.close()

def test_streamlit_content_moderation():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL)
        page.wait_for_load_state("domcontentloaded")

        sidebar_selector = wait_for_sidebar(page)
        print(f"✅ Sidebar detected using selector: {sidebar_selector}")

        # Navigate to Content Moderation
        page.locator("label:has-text('Content Moderation')").click()
        page.wait_for_selector("text=Content Moderation with Detoxify", timeout=15000)

        # Enter text and click button
        page.fill("textarea", "This is a bad comment")
        page.get_by_role("button", name="Moderate Text").click()

        # Wait for moderation result
        page.wait_for_selector("div[data-testid='stAlert']", timeout=10000)

        # ✅ Assert that alert is visible (either toxic or safe)
        alert_box = page.locator("div[data-testid='stAlert']")
        expect(alert_box).to_be_visible()

        # Screenshot evidence
        page.screenshot(path="artifacts/streamlit-content-moderation.png")

        print("✅ Moderation result alert displayed successfully")
        browser.close()