# XRPL Buyer App - Desktop Mode Setup (PowerShell)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "XRPL Buyer App - Desktop Mode Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if venv exists
if (-Not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host ""
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

Write-Host ""
Write-Host "Installing/updating dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "Setup complete! Starting app..." -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

python main.py

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
