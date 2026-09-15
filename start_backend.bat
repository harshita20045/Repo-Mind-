@echo off
rem Start RepoMind backend (FastAPI) using uvicorn

set "VENV=.venv"
if not exist "%VENV%" (
    echo Creating virtual environment... 
    python -m venv %VENV%
)
call %VENV%\Scripts\activate

pip install -r backend/requirements.txt

uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
