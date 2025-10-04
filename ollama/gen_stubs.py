import json
import ollama
from pathlib import Path

OPENAPI_FILE = "openapi.json"
OUTPUT_FILE = Path("tests/generated/openapi_stubs_test.py")

def generate_tests():
    with open(OPENAPI_FILE, "r") as f:
        spec = json.load(f)

    prompt = f"""
    You are a helpful assistant that writes pytest tests.

    Given this OpenAPI spec:
    {json.dumps(spec)[:5000]}

    Generate pytest tests for each endpoint:
    - One happy path test
    - Two negative tests (invalid input, missing field)
    - Use requests library for calls
    - Output only Python code, no explanations
    """

    response = ollama.chat(model="stable-code:3b", messages=[
        {"role": "user", "content": prompt}
    ])

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(response["message"]["content"])

    print(f"✅ Generated test stubs saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_tests()
