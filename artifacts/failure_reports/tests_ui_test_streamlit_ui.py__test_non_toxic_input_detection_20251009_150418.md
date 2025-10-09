# 🧪 Failure Report: tests/ui/test_streamlit_ui.py::test_non_toxic_input_detection
**Layer:** Frontend (UI)  
**Timestamp:** 20251009_150418
## ❌ Error Message
## ☁️ Groq Analysis (Cloud)
The test failure is due to the expected text 'safe' not being found in the content of the page after moderation. The content of the page is a large HTML string, and the expected text is not present in it.

The likely cause of this issue is that the moderation test is not correctly implemented or is not working as expected. The test is expecting the text 'safe' to be present in the content of the page after moderation, but it's not.

To fix this issue, we need to investigate why the moderation test is not working correctly. Here are a few possible quick fixes:

1. **Check the moderation test implementation**: Review the implementation of the moderation test to ensure it's correctly implemented and working as expected. Check if the test is correctly filling the text area, clicking the "Moderate Text" button, and checking the content of the page.

2. **Check the expected text**: Verify that the expected text 'safe' is correct and matches the actual output of the moderation test. If the expected text is incorrect, update it to match the actual output.

3. **Check the content of the page**: Review the content of the page after moderation to see if the expected text 'safe' is present in it. If it's not present, investigate why the moderation test is not working correctly.

4. **Add a debug print statement**: Add a debug print statement to print the content of the page after moderation to see if the expected text 'safe' is present in it. This will help us understand why the test is failing.

Here's an example of how you can add a debug print statement:
```python
def run_moderation_test(input_text, expect_text):
    ...
    content = page.content().lower()
    print("Content of the page after moderation:")
    print(content)
    assert expect_text.lower() in content, f"Expected '{expect_text}' not found"
```
This will print the content of the page after moderation, which will help us understand why the test is failing.

5. **Use a more robust assertion**: Instead of using the `assert` statement, use a more robust assertion library like `pytest-assertions` to handle the assertion. This will provide more information about the failure and make it easier to debug.

Here's an example of how you can use `pytest-assertions`:
```python
import pytest

def run_moderation_test(input_text, expect_text):
    ...
    content = page.content().lower()
    assert expect_text.lower() in content, f"Expected '{expect_text}' not found"
```
By using `pytest-assertions`, you'll get more information about the failure, which will make it easier to debug.

## 💻 Ollama Analysis (Local)
❌ Ollama error: Failed to connect to Ollama. Please check that Ollama is downloaded, running and accessible. https://ollama.com/download