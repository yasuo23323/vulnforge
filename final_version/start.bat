@echo off
cls
echo ========================================
echo   VulnForge - Setup ^& Launch
echo ========================================
echo.

if not exist .env (
    copy final_version\.env.example .env
)

findstr "^OPENAI_API_KEY=sk-your-api-key-here" .env >nul
if %errorlevel%==0 (
    echo.
    set /p api_key=Enter your DeepSeek API Key: 
    if defined api_key (
        powershell -Command "(Get-Content .env) -replace 'OPENAI_API_KEY=.*', 'OPENAI_API_KEY=%api_key%' | Set-Content .env"
        echo API Key saved!
    )
)
echo.
echo Starting VulnForge...
docker compose -f final_version/docker-compose.yml up -d
echo.
echo Open http://localhost:3000 in your browser
pause
