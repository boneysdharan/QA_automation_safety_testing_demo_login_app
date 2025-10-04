Task 1 – Automated API & UI Testing with LLM Failure Analysis

This project demonstrates a full testing workflow for a FastAPI application, including API, UI, and AI-assisted failure analysis.

We combined Postman/Newman, Playwright, pytest, and LLMs (Groq & Ollama) to create a robust testing scenario.

🚀 Features Implemented
✅ API Testing with Postman/Newman

What it does:
Automates testing of REST API endpoints like /api/login, /api/protected, and /api/moderate. Covers both happy path and negative scenarios.

Where it’s useful:

Validates that API endpoints behave as expected before deployment.

Ensures consistent API responses for frontend/mobile clients.

Detects regressions quickly when backend logic changes.

In this project:

Login → tested for success, invalid credentials, missing fields.

Protected route → tested with valid/invalid tokens.

Moderate endpoint → tested clean text vs. toxic text.

Reports saved in artifacts/newman-report.html and newman-report.json.

✅ UI Testing with Playwright

What it does:
Simulates user interactions (typing username/password, clicking login) in a real browser environment.

Where it’s useful:

Detects issues that unit tests can’t catch (e.g., frontend form validation, button clicks).

Helps QA teams ensure end-to-end user experience is smooth.

In this project:

Built test_ui_login.py to test a simple login flow.

Generated artifacts/playwright-report.html with detailed pass/fail results.

✅ LLM-Generated Test Stubs (Groq + Ollama)

What it does:
Uses LLMs to automatically generate pytest test files from the OpenAPI spec.

Where it’s useful:

Speeds up test creation for large APIs.

Reduces manual effort in writing boilerplate tests.

Helps junior developers generate test coverage quickly.

In this project:

Groq (cloud model) → tests/generated/openapi_stubs_groq.py

Ollama (local model) → tests/generated/openapi_stubs_ollama.py

Both generated valid runnable test files, saved reports in artifacts/.

✅ LLM-Assisted Failure Analysis

What it does:
When a pytest test fails, the failure trace is automatically sent to Groq and Ollama for natural-language analysis. Explanations are saved in artifacts/.

Where it’s useful:

Debugging complex tests faster.

Teams without deep expertise can quickly understand why a test failed.

Reduces time spent interpreting long stack traces.

In this project:

Groq output → groq_failure_explanation.md

Ollama output → ollama_failure_explanation.md

Combined view → failure_explanation_combined.md

✅ Moderation Endpoint (/moderate)

What it does:
Provides a small content safety service using a pre-trained toxicity detection model (Detoxify).

Where it’s useful:

Prevents unsafe or toxic content in chat, social apps, or forums.

A common feature in content moderation systems.

In this project:

Added /api/moderate to flag unsafe text.

Wrote tests/api/test_moderate.py to validate clean vs. toxic inputs.

⚙️ Setup & Installation

Clone the repo

git clone <your-repo-url>
cd task_1


Install dependencies

pip install -r requirements.txt


Run FastAPI app

uvicorn api:app --reload


Environment Variables

For Groq AI failure analysis:

export GROQ_API_KEY="your-groq-key"

🧪 Running Tests
1. Pytest (Unit + LLM Stubs)
python -m pytest --html=artifacts/report.html --self-contained-html


Runs API tests (test_moderate.py, openapi_stubs_*.py)

On failures → Groq/Ollama generate explanations in artifacts/

2. Postman / Newman API Tests
npx newman run tests/postman/collection.json -e tests/postman/environment.json \
  -r cli,html,json \
  --reporter-html-export artifacts/newman-report.html \
  --reporter-json-export artifacts/newman-report.json


Validates all API endpoints

Saves CLI, HTML, and JSON reports

3. Playwright UI Tests
python -m pytest --html=artifacts/playwright-report.html --self-contained-html tests/ui/test_ui_login.py


Executes login flow tests

Generates HTML report in artifacts/

📊 Reports & Artifacts

Playwright → artifacts/playwright-report.html

Newman → artifacts/newman-report.html & newman-report.json

Pytest (Groq/Ollama stubs) → artifacts/groq-report.html, ollama-report.html

Failure Analysis → failure_explanation_combined.md (Groq + Ollama insights)

To run all tests (API, UI, Detox, Groq, Ollama) and save reports in artifacts/, run the make_tests file.