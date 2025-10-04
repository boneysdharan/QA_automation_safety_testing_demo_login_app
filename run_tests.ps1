# run_tests.ps1
New-Item -ItemType Directory -Force -Path artifacts | Out-Null

Write-Host "Starting backend..."
$backend = Start-Process uvicorn -ArgumentList "api:app --reload --host 127.0.0.1 --port 8000" `
    -PassThru `
    -RedirectStandardOutput artifacts/backend.log `
    -RedirectStandardError artifacts/backend.log
Start-Sleep -Seconds 5

Write-Host "Running Newman API tests..."
newman run tests/postman/collection.json -e tests/postman/environment.json -r cli,html,json `
    --reporter-html-export artifacts/newman-report.html `
    --reporter-json-export artifacts/newman-report.json

Write-Host "Running Playwright UI tests..."
pytest tests/ui/test_ui_login.py --html=artifacts/playwright-report.html --self-contained-html

Write-Host "Running Detox moderation tests..."
pytest tests/api/test_moderate.py --html=artifacts/detox-report.html --self-contained-html

Write-Host "Running API tests..."
pytest tests/api/ --html=artifacts/api-report.html --self-contained-html

Write-Host "Running Groq stubs..."
pytest tests/generated/openapi_stubs_groq.py --html=artifacts/groq-report.html --self-contained-html

Write-Host "Running Ollama stubs..."
pytest tests/generated/openapi_stubs_ollama.py --html=artifacts/ollama-report.html --self-contained-html

Write-Host "Stopping backend..."
Stop-Process -Id $backend.Id -Force

Write-Host "All tests completed. Reports saved in artifacts/"
