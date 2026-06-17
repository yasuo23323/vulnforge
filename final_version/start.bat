@echo off
echo ========================================
echo  VulnForge - Starting...
echo ========================================
echo.
echo Step 1: Check .env file...
if not exist .env (
    echo   WARNING: .env not found! Copy .env.example to .env
    echo   and set your LLM API Key.
    echo.
    choice /c YN /m "Continue without .env? "
    if errorlevel 2 exit /b
)
echo.
echo Step 2: Starting services...
docker compose up -d
echo.
echo Step 3: Opening browser...
start http://localhost:3000
echo.
echo VulnForge is running at http://localhost:3000
echo Press any key to stop all services...
pause >nul
docker compose down
