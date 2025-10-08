import time
from playwright.sync_api import sync_playwright, expect
import pytest

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

#TEST INSIGHTS PAGE TESTS
def open_test_insights(page):
    """Navigate to the 'Test Insights' tab."""
    sidebar_selector = wait_for_sidebar(page)
    assert sidebar_selector is not None, "Sidebar not found"
    page.locator("label:has-text('Test Insights')").click()
    page.wait_for_selector("text=Unified Test Insights Dashboard", timeout=15000)

def test_total_test_count_display():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL)
        open_test_insights(page)
        expect(page.locator("text=Total Tests")).to_be_visible()
        browser.close()

def test_passed_test_count_metric():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL)
        open_test_insights(page)

        # Wait for any metric container and filter by text
        metric_block = page.locator("div[data-testid='stMetric']").filter(has_text="Passed")
        expect(metric_block).to_be_visible(timeout=10000)

        browser.close()

def test_failed_test_count_metric():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL)
        open_test_insights(page)

        # Wait for any metric container and filter by text
        metric_block = page.locator("div[data-testid='stMetric']").filter(has_text="Failed")
        expect(metric_block).to_be_visible(timeout=10000)

        browser.close()

def test_unified_table_presence():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL)
        open_test_insights(page)
        expect(page.locator("table")).to_be_visible()
        browser.close()

def test_dropdown_availability():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL)
        open_test_insights(page)
        expect(page.locator("[role='combobox']")).to_be_visible()
        browser.close()

def test_detailed_section_visibility():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL)
        open_test_insights(page)
        expect(page.locator("text=View Detailed Test Insight")).to_be_visible()
        browser.close()

def test_tools_column_present():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL)
        open_test_insights(page)
        header_cell = page.locator("table th", has_text="Tools That Ran This Test")
        expect(header_cell).to_be_visible(timeout=10000)
        browser.close()

# CONTENT MODERATION TESTS
def open_content_moderation(page):
    """Navigate to the 'Content Moderation' tab."""
    sidebar_selector = wait_for_sidebar(page)
    assert sidebar_selector is not None, "Sidebar not found"
    page.locator("label:has-text('Content Moderation')").click()
    page.wait_for_selector("text=Content Moderation with Detoxify", timeout=15000)

def run_moderation_test(input_text, expect_text):
    """Helper function to test moderation results."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL)
        open_content_moderation(page)

        page.fill("textarea", input_text)
        page.get_by_role("button", name="Moderate Text").click()
        time.sleep(3)

        content = page.content().lower()
        assert expect_text.lower() in content, f"Expected '{expect_text}' not found"
        browser.close()

def test_toxic_input_detection():
    run_moderation_test("You are so stupid!", "toxic")

def test_non_toxic_input_detection():
    run_moderation_test("You are kind and helpful!", "safe")

def test_empty_input_warning():
    run_moderation_test("", "please enter")