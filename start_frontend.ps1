# start_frontend.ps1 – Start the Streamlit frontend
Write-Host "Starting CareerAI Frontend (Streamlit)..." -ForegroundColor Magenta
Set-Location $PSScriptRoot
$env:PYTHONPATH = $PSScriptRoot
streamlit run frontend/app.py --server.port 8501 --server.headless false
