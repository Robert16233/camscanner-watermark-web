@echo off
chcp 65001 >nul
setlocal

set "PYTHON=python"
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
  set "PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)

echo Installing dependencies if needed...
"%PYTHON%" -m pip install -r requirements.txt

echo Starting server at http://127.0.0.1:8000
start "" "http://127.0.0.1:8000"
"%PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause
