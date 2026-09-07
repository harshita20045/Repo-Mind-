@echo off
rem Start RepoMind frontend (Vite React) using npm

cd frontend
if not exist "node_modules" (
    echo Installing npm dependencies... 
    npm install
)
npm run dev
