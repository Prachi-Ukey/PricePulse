# PricePulse Database Seeder Script
Write-Host "Seeding PricePulse Database with 100 products and >5000 transactions..." -ForegroundColor Cyan

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Virtual environment not detected! Please run .\scripts\setup.ps1 first." -ForegroundColor Red
    exit 1
}

& .\.venv\Scripts\python.exe -c "from backend.app.database import engine, Base, SessionLocal; from backend.app.seed_data import seed_database_if_empty; Base.metadata.create_all(bind=engine); db = SessionLocal(); res = seed_database_if_empty(db, force=True); print(res); db.close()"
Write-Host "Seeding complete!" -ForegroundColor Green
