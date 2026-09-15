@echo off
rem Start RepoMind background worker

set "VENV=.venv"
if not exist "%VENV%" (
    echo Creating virtual environment... 
    python -m venv %VENV%
)
call %VENV%\Scripts\activate

pip install -r backend/requirements.txt

python worker/worker.py
