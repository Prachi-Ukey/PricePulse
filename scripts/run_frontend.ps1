# PricePulse Frontend Development Server Startup Script
Write-Host "Starting PricePulse React/Vite Dashboard Frontend..." -ForegroundColor Cyan
Write-Host "URL: http://localhost:5173" -ForegroundColor Green

Push-Location frontend
npm run dev
Pop-Location
