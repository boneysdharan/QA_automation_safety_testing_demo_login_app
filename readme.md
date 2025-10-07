🚀 Task 1 – Automated API & UI Testing with AI-Powered Insights

This project showcases a complete automated testing workflow for a FastAPI-based app — combining API, UI, and AI-assisted validation to achieve end-to-end testing reliability.

We integrated:
🧪 Postman/Newman (API Testing)
🧠 Groq & Ollama (AI Test Generation & Failure Analysis)
🧰 Pytest (Unit + Integration Tests)
🌐 Playwright (Frontend UI Testing)
🧩 Streamlit Dashboard (Unified Test Insights)

✨ Features Implemented
✅ API Testing with Postman / Newman

Purpose: Verify correctness and resilience of REST endpoints — /api/login, /api/protected, /api/moderate.

Highlights:

Covers success + multiple negative scenarios.

Auto-generated detailed HTML & JSON reports.

Ensures backend logic is consistent and regression-safe.

🧾 Sample Test Cases Implemented

Below are a few core test cases from the project — spanning different layers and tools:

#	Test Name	Description	Tools Used	Layer	Result
1	Login Success	Validates successful login using correct credentials (admin/password123).	✅ Pytest (Login), ✅ Postman, ✅ Playwright, ✅ Groq, ✅ Ollama	Backend (Auth/API)	✅ Passed
2	Login Failure (Wrong Credentials)	Ensures login fails gracefully with invalid credentials.	✅ Pytest (Login), ✅ Postman, ✅ Playwright	Backend (Auth/API)	✅ Passed
3	Protected Route (Missing Auth Header)	Checks access denial when no authorization token is supplied.	✅ Postman, ✅ Pytest (Login), ✅ Groq, ✅ Ollama	Backend (Auth/API)	✅ Passed
4	Moderate Toxic Text	Sends offensive text to /moderate and verifies the model flags it as toxic.	✅ Pytest (Moderation), ✅ Postman	Backend (Toxicity / Model)	✅ Passed
5	Moderate Clean Text	Ensures harmless text passes moderation.	✅ Pytest (Moderation), ✅ Postman	Backend (Toxicity / Model)	✅ Passed
6	Login UI – Success Flow	Simulates a user logging in via browser; checks for dashboard load.	✅ Playwright	Frontend (UI)	✅ Passed
7	Logout Functionality	Validates that logout returns user to login page and session resets.	✅ Playwright	Frontend (UI)	✅ Passed
8	AI Failure Analyzer (Local)	Runs Ollama model to summarize any test failures locally.	✅ Ollama	Local AI (LLM Diagnostics)	✅ Passed
9	AI Failure Analyzer (Cloud)	Uses Groq model to analyze test traces in the cloud.	✅ Groq	Cloud AI (LLM Diagnostics)	✅ Passed

🧩 These represent the unified results visible in final_unified_tests.csv and the Streamlit “Test Insights” dashboard.

📁 Artifacts:
artifacts/newman-report.html
artifacts/newman-report.json

✅ UI Testing with Playwright

Purpose: Simulate real browser interactions to test frontend reliability.

Covers:

Login (success, failure, empty fields)

Logout flow

UI refresh and multi-attempt scenarios

📁 Artifacts:
artifacts/playwright-report.html

✅ Pytest-Based API Tests

Purpose: Unit + integration testing for backend logic.

Includes:

/api/login → success, invalid creds, missing fields

/api/moderate → safe vs toxic text

/api/protected → token-based auth verification

📁 Files:

tests/api/test_login.py

tests/api/test_moderate.py

📁 Reports:
artifacts/text-login-report.html
artifacts/text-moderation-report.html

✅ AI-Generated Test Stubs (Groq + Ollama)

Purpose: Automatically generate Pytest-compatible test scripts from OpenAPI specifications using local and cloud LLMs.

Benefit: Speeds up test authoring for large or frequently updated APIs.

📁 Generated Tests:

tests/generated/openapi_stubs_groq.py

tests/generated/openapi_stubs_ollama.py

📁 Reports:

artifacts/groq-report.html

artifacts/ollama-report.html

✅ LLM-Assisted Failure Analysis

Purpose: When tests fail, AI models (Groq & Ollama) analyze stack traces to diagnose causes and suggest quick fixes in plain English.

Example Output:

“Login test failed due to mismatched key names in JSON payload. Fix by renaming username → user_name in backend schema.”

📁 Reports:

artifacts/failure_reports/groq_failure_explanation.md

artifacts/failure_reports/ollama_failure_explanation.md

✅ Content Moderation Endpoint (/moderate)

Purpose: Detects unsafe or toxic text using Detoxify — a pre-trained content moderation model.

Use Case: Adds responsible AI layer for chat apps, forums, or review systems.

📁 File: tests/api/test_moderate.py

✅ Unified Streamlit Test Insights Dashboard

A central visual dashboard (app.py) displaying all test results and integrations in one place.

How It Works — AI Test Analysis Workflow

This section explains, in detail, how the project automatically detects test failures, sends them to LLMs (Groq cloud and Ollama local) for diagnosis, and surfaces concise, actionable fixes in the dashboard and artifacts. I’ll walk through inputs, preprocessing, prompt design, model invocation, post-processing, integration points, safeguards, and practical tips — so you (or a CI pipeline) can run this reliably.

1) High-level architecture (quick diagram)
flowchart LR
  A[Run Tests (Newman/Pytest/Playwright)] --> B[Collect Reports (JSON/HTML)]
  B --> C[Normalize & Merge Test Records]
  C --> D{Status: Passed / Failed}
  D -->|Passed| E[Store as Passed]
  D -->|Failed| F[Extract failure payloads]
  F --> G[Preprocess: scrub & summarize]
  G --> H[AI Analyzers: Groq (cloud) / Ollama (local)]
  H --> I[Parse & save explanation JSON/MD]
  I --> J[Streamlit Dashboard (Test Insights)]
  J --> K[Optional: Open GitHub issue / notify]

2) Inputs — what we capture and why

When a test fails we gather the richest, most relevant context possible so the AI has a good chance of producing a correct diagnosis.

Test metadata — test id/name, test file, tool (Newman/Pytest/Playwright/Groq/Ollama).

Execution context — CI job id, OS, Python/Node versions, timestamp, environment markers.

Assertion message / stack trace — the raw failure text (pytest longrepr, Playwright errors, request/response assertion).

HTTP request/response (when applicable) — URL, method, request headers/payload, response code, response body (with secrets removed).

Relevant log snippets & test stdout/stderr — trimmed to the most informative lines.

Report pointers — path to raw artifacts (newman JSON, pytest html, playwright html) for full context.

3) Aggregation & normalization

Before sending anything to AI we:

Collect reports: parse newman-report.json, pytest html/json, playwright html, groq/ollama result files and any failure markdowns under artifacts/failure_reports/.

Canonicalize test names: fuzzy-match similar tests (fuzzy threshold tuned — default 80) to merge tests that are the “same logical test” executed by multiple tools (e.g., Login Success executed by Newman & Playwright).

Merge statuses and tools: build a single row per canonical test listing all tools that ran it and an aggregated status (Failed if any tool failed, Passed only if all ran tools passed).

Store canonical mapping and artifacts in artifacts/ and final_unified_tests.csv for reproducibility.

This merging ensures the AI receives a consolidated picture for each failing test rather than fragmented fragments.

4) Failure detection & triage

We classify failures so AI explanations can be focused:

Assertion failure (pytest AssertionError, mismatched values)

HTTP error (4xx/5xx + unexpected body)

Timeout / Resource (test or network timeout)

UI interaction error (selector missing, element not visible)

Environment (DB not reachable, missing env var)

Flaky detection (same test intermittently passes/fails — require multiple runs)

We tag failures with a failure_type and severity (e.g., high for 500s, medium for assertion mismatch, low for flaky/timeouts).

5) AI Analysis Pipeline — the core flow
Preprocessing (always)

Scrub secrets: remove Authorization header tokens, API keys, DB credentials (regex-based).

Trim: keep the most relevant 1–3 stack frames + top 500–2000 characters of logs. If logs are too big, extract the top-N error lines and the last N lines.

Structure: build a JSON payload with fields we want the model to analyze:

{
  "test_name": "Login Success",
  "tool": "Pytest",
  "failure_type": "AssertionError",
  "assertion": "assert resp.status_code == 200",
  "request": {"method":"POST","url":"/api/login","body":"{...}"},
  "response": {"status_code":500,"body":"internal server error"},
  "stack": "Traceback (most recent call last): ...",
  "env": {"python":"3.11", "os":"windows"}
}

Prompt construction (recommended templates)

Groq (cloud) prompt — system + user

System: You are a concise test-failure analyst. Return JSON with keys:
  - likely_cause (short)
  - quick_fix (short)
  - confidence (0-1)
  - category (one of: assertion, http, env, ui, flaky, unknown)
User: Here is the failing test payload (JSON):
<PASTE THE PREPROCESSED JSON ABOVE>
Analyze and return valid JSON only.


Ollama (local) prompt (similar)

System: You are a debugging assistant that explains test failures concisely and gives a one-line code or config fix.
User: { preprocessed JSON... }
Return a JSON with fields: likely_cause, quick_fix, confidence, code_snippet (optional)


Note: Asking for structured JSON makes downstream parsing deterministic. If the model returns free text, attempt to extract the fields via simple regex and fallback to saving raw output.

Model call

Groq: POST to cloud endpoint with model=llama-3.1-8b-instant, include GROQ_API_KEY from env. Use small temperature (0.0–0.2) for deterministic answers. Timeout 30–60s.

Ollama: call ollama.chat(...) or CLI ["ollama","run","b3"] for local analysis. Timeout shorter (10–15s) for interactive dashboards.

Post-processing & persistence

Parse the JSON returned by the model into local fields.

Sanity check: Validate confidence (if present), ensure quick_fix is short and actionable. If confidence < 0.3, mark as low_confidence.

Save as artifacts/failure_reports/{test-name}_{timestamp}.md (human-readable) and as failure_explanations/{test-name}_{timestamp}.json (machine-readable).

Attach the saved file path into the canonical test's details so the dashboard can display it.

6) Example expected AI response (JSON)
{
  "likely_cause": "Backend returned 500 due to an uncaught KeyError when reading 'username' from request.",
  "quick_fix": "Validate payload keys before lookup and add fallback; e.g. use data.get('username') or add an explicit schema validation.",
  "confidence": 0.92,
  "category": "http",
  "code_snippet": "username = request.json().get('username')\nif not username: raise HTTPException(400, 'username required')"
}


We display likely_cause and quick_fix in the dashboard and optionally show code_snippet inside an expandable code block.

7) Integration points — how it hooks into the test runner
Pytest: conftest.py hook example (already present in your repo — simplified)
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        # get longrepr (failure text)
        failure_payload = build_payload_from_report(item, report)  # collects request/response/stack
        explanation = analyze_with_groq(failure_payload)   # cloud
        explanation_local = analyze_with_ollama(failure_payload)  # local
        save_explanations(item.nodeid, explanation, explanation_local)

Newman / Postman

Parse newman-report.json for failed executions and capture request/response/assertions for each failing item. Send to AI similarly.

Playwright

Capture CLI output or the HTML report failure snippets; capture the failing test name, error message, and page screenshots (path). Send textual error summary to AI, and save screenshot paths for the dashboard.

Streamlit dashboard

When user clicks a failed test in “Test Insights”, read artifacts/failure_reports/{…}.md and display it. Optionally call local Ollama live if no saved report exists (with a short timeout).

8) Heuristics, thresholds and quality controls

Fuzzy canonicalization: threshold 80 (fuzz.token_sort_ratio) for merging logically identical tests from different tools.

AI temperature: 0.0–0.2 to reduce hallucinations.

Size limits: trim logs to N chars (e.g., 4k) before sending.

Confidence/Trust gating: label suggestions low_confidence if model returns unclear answers; require human approval before auto-applying fixes.

Rate limiting: AI calls only for failed tests (not for passed ones), and in CI prefer batching or only send first N unique failures per run.

9) Privacy & security

Never send environment secrets: scrub Authorization headers, cookies, connection strings, tokens.

For regulated environments, prefer Ollama (local) to keep logs on-prem.

Keep AI answers and raw logs under artifacts/ with restricted repo access or encrypted storage if needed.

10) CI / Automation pattern (recommended)

Run tests in CI (pytest, newman, playwright).

Save reports to artifacts/.

Run a “report aggregator” script that canonicalizes tests and identifies failures.

Call AI analysis only on failed tests (or only new/untriaged failures).

Save AI outputs to artifacts/failure_reports/.

Publish reports and artifacts, and optionally create a GitHub issue with AI suggestion for each new failure.

11) Human-in-the-loop best practices

Always present the AI suggestion as a recommendation — never auto-commit a fix without human confirmation.

Add a small UI action: “Create issue with this suggestion” which copies the AI explanation into a GitHub issue template so maintainers can triage.

Keep a short audit trail: who/when the AI suggested fixes and whether they were accepted.

12) Limitations & mitigation

Hallucinations: LLMs can produce plausible-but-wrong causes. Mitigate by asking for short fixes, requiring confidence and showing the underlying evidence (stack trace + request/response).

Cost & rate limits: Cloud calls to Groq/GPT can be expensive. Minimize calls: only analyze unique failing tests, not repeated identical failures across reruns.

Over-trimming: If we trim too much log context, the model may miss the cause. Prefer extracting the most informative lines (error + a couple of stack frames) instead of blind truncation.

13) Practical prompt examples (copy-paste)

Groq system + user (JSON-oriented)

System: You are a test failure analyzer. Output valid JSON with keys:
  likely_cause, quick_fix, confidence(0-1), category.
User: Analyze the following failing-test payload (JSON) and return the JSON only:
<preprocessed-json-string>


Ollama quick prompt

Test failed payload:
<preprocessed-json-string>
Explain the most likely cause and provide a one-line quick fix. Output as JSON.

14) Example end-to-end trace (concrete scenario)

pytest fails on test_login_success due to status 500.

pytest hook collects: test name, assert snippet, HTTP request & response including response body { "detail":"KeyError: 'username'" }.

Script scrubs Authorization, truncates the log and builds JSON payload.

Send payload to Groq and local Ollama.

Groq returns: likely_cause = "KeyError when fetching username", quick_fix = "Use data.get('username') or add validation".

Save to artifacts/failure_reports/test_login_success_2025-10-07.md.

Dashboard shows test row as FAILED — clicking it reveals the AI explanation + link to full logs + option to open an auto-created GitHub issue template.

Features:

✅ Consolidated view of Postman, Pytest, Playwright, Groq, Ollama

📊 Auto-generated metrics (total, passed, failed)

🧾 Filterable table with vertical scroll — no horizontal overflow

🔍 Select individual test to view:

Tools that executed it

Detailed explanation & usage context

AI analysis reports

📁 Live CSV Export:
final_unified_tests.csv

🧰 Setup & Installation
git clone <your-repo-url>
cd task_1
pip install -r requirements.txt
uvicorn api:app --reload

Environment Variables

(Optional – only if using Groq AI)

export GROQ_API_KEY="your-groq-key"

🧪 Running Tests
1️⃣ Pytest
pytest --html=artifacts/report.html --self-contained-html

2️⃣ Postman / Newman
npx newman run tests/postman/collection.json \
  -r cli,html,json \
  --reporter-html-export artifacts/newman-report.html \
  --reporter-json-export artifacts/newman-report.json

3️⃣ Playwright
pytest tests/ui/test_ui_login.py --html=artifacts/playwright-report.html --self-contained-html

📈 Reports Summary
Tool	Type	Report Path
🧩 Postman	API	artifacts/newman-report.html
🧪 Pytest	Backend	artifacts/report.html
🌐 Playwright	UI	artifacts/playwright-report.html
☁️ Groq	AI Analysis	artifacts/groq-report.html
💻 Ollama	AI Analysis	artifacts/ollama-report.html
🧠 Combined	Unified View	final_unified_tests.csv & Streamlit Dashboard