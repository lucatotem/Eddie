# Quick Setup Script for Eddie
# Run this to get everything up and running

Write-Host "🚀 Setting up Eddie..." -ForegroundColor Cyan

# Check Python
Write-Host "`n📦 Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Install Python 3.9+ first!" -ForegroundColor Red
    exit 1
}

# Check Node
Write-Host "`n📦 Checking Node..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "✅ Node found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node not found. Install Node.js 18+ first!" -ForegroundColor Red
    exit 1
}

# Setup Backend
Write-Host "`n🐍 Setting up backend..." -ForegroundColor Yellow
Set-Location backend

# Create venv if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
}

# Activate venv and install deps
Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Copy env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Cyan
    Copy-Item .env.example .env
    Write-Host "⚠️ Don't forget to fill in your Confluence credentials in backend/.env!" -ForegroundColor Yellow
}

Set-Location ..

# Setup Frontend
Write-Host "`n⚛️ Setting up frontend..." -ForegroundColor Yellow
Set-Location frontend

Write-Host "Installing npm dependencies..." -ForegroundColor Cyan
npm install

# Copy env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
}

Set-Location ..

# Done!
Write-Host "`n✨ Setup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Edit backend/.env with your Confluence credentials" -ForegroundColor White
Write-Host "2. In one terminal: cd backend; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload" -ForegroundColor White
Write-Host "3. In another terminal: cd frontend; npm run dev" -ForegroundColor White
Write-Host "4. Open http://localhost:3000" -ForegroundColor White
Write-Host "`n🎉 Happy onboarding!" -ForegroundColor Magenta
