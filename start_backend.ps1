# start_backend.ps1 – Start the FastAPI backend server
Write-Host "Starting CareerAI Backend (FastAPI)..." -ForegroundColor Cyan
Set-Location $PSScriptRoot
$env:PYTHONPATH = $PSScriptRoot
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
