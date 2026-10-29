@echo off
title AI Navigator - Runner
echo ========================================================
echo               Starting AI Navigator
echo ========================================================
echo.

cd /d "%~dp0"

:: Check virtual environment
if not exist "backend\venv\Scripts\python.exe" (
    echo Creating Python virtual environment in backend\venv...
    python -m venv backend\venv
    echo Installing backend dependencies...
    backend\venv\Scripts\pip install -r backend\requirements.txt
)

:: Start Backend in a separate window
echo Starting Backend API at http://127.0.0.1:8000 ...
start "AI Navigator - Backend" cmd /k "cd /d "%~dp0backend" && venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

:: Start Frontend in a separate window
echo Starting Frontend Web Server at http://127.0.0.1:5500 ...
start "AI Navigator - Frontend" cmd /k "cd /d "%~dp0frontend" && python -m http.server 5500"

:: Wait a brief moment then launch default browser
timeout /t 2 >nul
start http://localhost:5500

echo.
echo ========================================================
echo AI Navigator is running!
echo Frontend: http://localhost:5500
echo Backend:  http://127.0.0.1:8000
echo Swagger:  http://127.0.0.1:8000/docs
echo ========================================================
echo You can close this launcher window.
pause
