import json
import ollama
from pathlib import Path

OPENAPI_FILE = "openapi.json"
OUTPUT_FILE = Path("tests/generated/openapi_stubs_ollama.py")

def generate_tests():
    with open(OPENAPI_FILE, "r") as f:
        spec = json.load(f)

    # ✅ Style prompt
    prompt = f"""
You are an expert FastAPI QA engineer writing pytest API test cases using the requests library.

Given the following OpenAPI spec:
{json.dumps(spec)[:5000]}

Generate a Python test file that matches *exactly* this structure and style:

- File name: openapi_stubs_ollama.py
- Import only requests
- Define BASE_URL = "http://127.0.0.1:8000/api"
- Group tests into clear sections with comments:
    # --- LOGIN TESTS ---
    # --- PROTECTED ENDPOINT TESTS ---
    # --- MODERATE ENDPOINT TESTS ---
- Each test function:
    - Starts with "test_"
    - Includes a short docstring (Positive/Negative test: ...)
    - Uses descriptive variable names (url, payload, headers)
    - Uses requests.post() or requests.get() depending on endpoint
    - Uses assert response.status_code == expected_code
    - Includes assert messages like response.text
- Include these tests:
    1. test_login_valid
    2. test_login_invalid_input
    3. test_login_missing_fields
    4. test_login_wrong_password
    5. test_login_missing_username
    6. test_login_missing_password
    7. test_protected_with_valid_token
    8. test_protected_with_invalid_token
    9. test_protected_missing_auth_header_ollama
    10. test_protected_expired_token
    11. test_moderate_with_valid_text
    12. test_moderate_with_empty_text
    13. test_moderate_invalid_payload_ollama
- Use consistent indentation, spacing, and sectioning.

Output only the final Python code — no explanations, comments, or markdown formatting.
"""

    response = ollama.chat(model="stable-code:3b", messages=[
        {"role": "user", "content": prompt}
    ])

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(response["message"]["content"])

    print(f"✅ Generated Ollama-style tests saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_tests()