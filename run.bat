
@echo off
cd /d "%~dp0"
set "EVIDENCEAI_PYTHON=.venv\Scripts\python.exe"
if not exist "%EVIDENCEAI_PYTHON%" (
  echo EvidenceAI virtual environment was not found.
  echo Create it with: py -m venv .venv
  echo Then install dependencies with: .venv\Scripts\python.exe -m pip install -r requirements.txt
  pause
  exit /b 1
)
"%EVIDENCEAI_PYTHON%" -c "import streamlit, pandas, plotly" >nul 2>&1
if errorlevel 1 (
  echo EvidenceAI dependencies are missing from the project virtual environment.
  echo Install them with: .venv\Scripts\python.exe -m pip install -r requirements.txt
  pause
  exit /b 1
)
"%EVIDENCEAI_PYTHON%" -m streamlit run app.py
pause
