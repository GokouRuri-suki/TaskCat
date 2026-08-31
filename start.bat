@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo   TaskCat one-click launcher
echo ========================================
echo [1/2] Starting backend ...
start "TaskCat Backend" cmd /k "cd /d %~dp0fastapi && ..\.venv\Scripts\python.exe -m uvicorn src:app --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Starting GUI ...
cd /d "%~dp0java"
call mvnw.cmd javafx:run

echo.
echo GUI closed. Press Ctrl+C in the "TaskCat Backend" window to stop the server.
pause