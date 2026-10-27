# PricePulse Backend Server Startup Script
Write-Host "Starting PricePulse FastAPI Analytics Backend..." -ForegroundColor Cyan
Write-Host "Host: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Swagger Docs: http://127.0.0.1:8000/docs" -ForegroundColor Green

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Virtual environment not detected! Please run .\scripts\setup.ps1 first." -ForegroundColor Red
    exit 1
}

& .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
