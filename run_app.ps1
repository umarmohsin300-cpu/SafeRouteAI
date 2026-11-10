# SafeRoute AI Launch Script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir
$env:PYTHONPATH = $ScriptDir
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

# Free port 8501 if previously occupied
$portProcess = Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($portProcess) {
    Stop-Process -Id $portProcess -Force -ErrorAction SilentlyContinue
}

$PythonExe = Join-Path $ScriptDir ".python\python.exe"
if (Test-Path $PythonExe) {
    & $PythonExe -m streamlit run app.py
} else {
    python -m streamlit run app.py
}
