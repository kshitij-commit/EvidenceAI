@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Create the project virtual environment first and install requirements-project.txt.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m streamlit run project_app.py --server.port 8502
pause
