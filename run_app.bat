@echo off
title SafeRoute AI - Smarter Roads. Safer Journeys.
cd /d "%~dp0"

echo ========================================================
echo       Starting SafeRoute AI (Streamlit Web App)
echo       AI-Powered Road Hazards and Safety Mapping
echo ========================================================
echo.

set PYTHON_EXE=%~dp0.python\python.exe
set PYTHONPATH=%~dp0
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

:: Free port 8501 if previously occupied
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr :8501') do (
    taskkill /f /pid %%a >nul 2>&1
)

if not exist "%PYTHON_EXE%" (
    echo Python embeddable runtime not found in .python folder.
    echo Trying system python...
    python -m streamlit run app.py --server.headless false
) else (
    "%PYTHON_EXE%" -m streamlit run app.py --server.headless false
)

pause
