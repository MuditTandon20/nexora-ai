$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Run the setup instructions in README.md first.'
}
$backendPath = Join-Path $projectRoot 'backend'
$frontendPath = Join-Path $projectRoot 'frontend'
$apiProcess = Start-Process -FilePath $pythonPath -ArgumentList '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000' -WorkingDirectory $backendPath -WindowStyle Hidden -PassThru
try {
    Write-Host 'Nexora: http://localhost:3000. Press Ctrl+C to stop.'
    Push-Location $frontendPath
    npm.cmd run dev
} finally {
    Pop-Location
    if (-not $apiProcess.HasExited) {
        # Windows virtualenv launchers can own a child interpreter; stop this process tree.
        taskkill.exe /PID $apiProcess.Id /T /F | Out-Null
    }
}
