@echo off
chcp 65001 >nul
set HOST=85.239.34.67
set USER=root
set REPO_DIR=/root/hh-parser-001

echo ===================================================
echo  DEPLOY TO SERVER (%HOST%)
echo ===================================================

echo [1/2] Pushing code to GitHub...
git add .
git commit -m "Deploy update"
git push origin main

echo [2/2] Updating server...
ssh %USER%@%HOST% "cd %REPO_DIR% && git pull origin main && docker compose up -d --build"

if %errorlevel% neq 0 (
    echo [ERROR] Failed to update server!
    pause
    exit /b
)

echo.
echo [SUCCESS] Server updated and restarted!
pause
