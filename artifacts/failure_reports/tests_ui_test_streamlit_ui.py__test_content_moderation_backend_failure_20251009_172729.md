# 🧪 Failure Report: tests/ui/test_streamlit_ui.py::test_content_moderation_backend_failure
**Layer:** Frontend (UI)  
**Timestamp:** 20251009_172729

## ❌ Error Message

## ☁️ Groq Analysis (Cloud)
**Likely Cause:**

The test `test_content_moderation_backend_failure` is failing because the expected text "error", "failed", or "exception" is not found in the page's inner text after simulating a backend failure during moderation. This could be due to several reasons:

1. **Backend failure not triggered**: The simulated backend error might not be triggering the expected error message on the page.
2. **Error message not displayed**: The error message might not be displayed on the page, or it might be displayed in a different way than expected.
3. **Page content not updated**: The page content might not be updated after simulating the backend failure, resulting in the expected text not being present.

**Quick Fix:**

To troubleshoot this issue, you can try the following:

1. **Print the page content**: Add a print statement to display the page content after simulating the backend failure:
   ```python
print(page.inner_text("body").lower())
```
   This will help you understand what text is actually present on the page.

2. **Check the error message**: Verify that the expected error message is being displayed on the page. You can do this by inspecting the page's content or by adding additional assertions to check for the presence of specific error messages.

3. **Update the assertion**: If the expected text is not present, update the assertion to check for the actual text that is present on the page.

Here's an updated version of the test with the print statement:
```python
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
            print(text)  # Print the page content
            assert any(k in text for k in ["error", "failed", "exception"])
            b.close()
    run_safe_test("test_content_moderation_backend_failure", inner)
```
By adding the print statement, you can inspect the page content and understand what's going on.

## 💻 Ollama Analysis (Local)
❌ Ollama error: model 'b3' not found (status code: 404)