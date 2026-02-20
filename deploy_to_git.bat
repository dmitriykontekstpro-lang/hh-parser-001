@echo off
echo ===================================================
echo 🚀 DEPLOY TO GITHUB: ONE-CLICK PUSH
echo ===================================================

echo [STATUS] Checking repository...

if not exist .git (
    echo [ERROR] Git repository not initialized! Run 'git init' first.
    pause
    exit /b
)

:: Prompt for commit message
set /p msg="Enter commit message (default: Update): "
if "%msg%"=="" set msg=Update

echo [ACTION] Adding files...
git add .

echo [ACTION] Committing...
git commit -m "%msg%"

echo [ACTION] Pushing to GitHub...
:: Check upstream
git push origin main
if %errorlevel% neq 0 (
    echo [WARN] Failed simple push. Trying with set-upstream...
    git push --set-upstream origin main
)

if %errorlevel% neq 0 (
    echo [ERROR] Failed to push to GitHub. Check your network or credentials.
    pause
    exit /b
)

echo [SUCCESS] Code deployed to GitHub!
pause
