$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Install dependencies using README.md first.' }
foreach ($demoPort in @(3001,8001)) {
    $probeClient = New-Object System.Net.Sockets.TcpClient
    try {
        $probeClient.Connect('127.0.0.1',$demoPort)
        throw "Port $demoPort is already in use. Stop the existing demo before starting a new one."
    } catch [System.Net.Sockets.SocketException] {
        # A refused local connection means this port is available.
    } finally { $probeClient.Dispose() }
}
$demoRoot = Join-Path $projectRoot '.demo'
New-Item -ItemType Directory -Force -Path $demoRoot | Out-Null
$sessionName = 'teacher-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + ([guid]::NewGuid().ToString('N').Substring(0,8))
$databasePath = (Join-Path $demoRoot ($sessionName + '.db')).Replace([char]92,[char]47)
$env:DATABASE_URL = 'sqlite:///' + $databasePath
$env:ENVIRONMENT = 'development'
$env:STORAGE_BACKEND = 'local'
$env:UPLOAD_DIR = Join-Path $demoRoot 'uploads'
$env:AI_ENABLED = 'false'
$env:FRONTEND_ORIGIN = 'http://localhost:3001'
$env:API_INTERNAL_URL = 'http://127.0.0.1:8001'
$apiProcess = $null
$demoLocationPushed = $false
try {
    Push-Location (Join-Path $projectRoot 'backend')
    $demoLocationPushed = $true
    & $pythonPath -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw 'Migration failed.' }
    & $pythonPath -m app.demo
    if ($LASTEXITCODE -ne 0) { throw 'Demo seed failed.' }
    $apiProcess = Start-Process -FilePath $pythonPath -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8001' -WorkingDirectory (Join-Path $projectRoot 'backend') -WindowStyle Hidden -PassThru
    Pop-Location
    $demoLocationPushed = $false
    Push-Location (Join-Path $projectRoot 'frontend')
    $demoLocationPushed = $true
    Write-Host 'Synthetic teacher demo: http://localhost:3001/login'
    Write-Host 'teacher@nexora.demo / NexoraDemo!2026. AI is disabled. Ctrl+C stops the demo.'
    npm.cmd run dev -- --port 3001
} finally {
    if ($demoLocationPushed) { Pop-Location }
    if ($apiProcess -and -not $apiProcess.HasExited) { taskkill.exe /PID $apiProcess.Id /T /F | Out-Null }
}
