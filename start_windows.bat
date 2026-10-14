@echo off
setlocal
cd /d "%~dp0backend"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 ( echo Please install Python 3.11+ from python.org & pause & exit /b 1 )
)
call ".venv\Scripts\activate.bat"
python -m pip install -r requirements-agent.txt
if errorlevel 1 ( echo Dependency install failed. Check internet access. & pause & exit /b 1 )
echo.
echo Venture Intelligence is starting at http://localhost:8000
echo Press Ctrl+C to stop.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
