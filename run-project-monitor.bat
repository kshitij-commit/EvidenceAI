@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Create the project virtual environment first and install requirements-project.txt.
  pause
  exit /b 1
)
if not exist web\node_modules (
  echo Frontend dependencies are missing. From the project folder run:
  echo   cd web ^&^& npm install
  pause
  exit /b 1
)
start "EvidenceAI API" /D "%~dp0" "%~dp0.venv\Scripts\python.exe" -m uvicorn src.project_monitoring.api:app --host 127.0.0.1 --port 8000
cd /d "%~dp0web"
npm run dev
