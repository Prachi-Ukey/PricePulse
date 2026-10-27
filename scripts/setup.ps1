# PricePulse Automated Environment Setup Script for Windows PowerShell
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " PricePulse — Intelligent Pricing & Profit Analytics Setup" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Environment file check
if (-not (Test-Path ".env")) {
    Write-Host "[1/5] Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
} else {
    Write-Host "[1/5] .env file already present." -ForegroundColor Green
}

# 2. Python Virtual Environment Setup
if (-not (Test-Path ".venv")) {
    Write-Host "[2/5] Creating Python virtual environment in .venv..." -ForegroundColor Yellow
    python -m venv .venv
} else {
    Write-Host "[2/5] Virtual environment .venv already exists." -ForegroundColor Green
}

# 3. Install Backend Dependencies
Write-Host "[3/5] Installing backend Python dependencies..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -r backend\requirements.txt

# 4. Install Frontend Dependencies
Write-Host "[4/5] Installing frontend Node packages..." -ForegroundColor Yellow
Push-Location frontend
npm install
Pop-Location

# 5. Initialize & Seed Database
Write-Host "[5/5] Initializing SQLite database and deterministic seed data..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -c "from backend.app.database import engine, Base, SessionLocal; from backend.app.seed_data import seed_database_if_empty; Base.metadata.create_all(bind=engine); db = SessionLocal(); print(seed_database_if_empty(db, force=False)); db.close()"

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " Setup completed successfully!" -ForegroundColor Green
Write-Host " - Start Backend : .\scripts\run_backend.ps1" -ForegroundColor Cyan
Write-Host " - Start Frontend: .\scripts\run_frontend.ps1" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green
