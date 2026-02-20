@echo off
set HOST=85.239.34.67
set USER=root
:: The path on server where we will clone the repo
set REPO_DIR=/root/hh-parser-001

echo ===================================================
echo ☁️ DEPLOY TO SERVER (%HOST%)
echo ===================================================

:: Ensure user can execute this script
where ssh >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] SSH command not found.
    pause
    exit /b
)

:: Prompt for confirmation
echo [WARN] This will pull the latest code from GitHub and restart the server.
echo [WARN] You may need to enter your server password (%USER%).

:: Execute remote commands
:: 1. Create directory if not exists
:: 2. Clone if empty, otherwise pull
:: 3. Run docker compose up

ssh %USER%@%HOST% "mkdir -p %REPO_DIR% && cd %REPO_DIR% && if [ ! -d .git ]; then git clone https://github.com/dmitriykontekstpro-lang/hh-parser-001.git . ; else git pull ; fi && docker compose down && docker compose up -d --build"

if %errorlevel% neq 0 (
    echo [ERROR] Failed to update server. Check SSH connection/path.
    pause
    exit /b
)

echo [SUCCESS] Server updated and restarted!
pause
