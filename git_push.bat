@echo off
title Git Push - Vortex AI OS
echo ====================================================
echo             GIT PUSH TO HEERAV04/VORTEX
echo ====================================================
echo.

:: 1. Initialize repository
if not exist ".git" (
    echo [INFO] Initializing new Git repository...
    git init
    if %errorlevel% neq 0 (
        echo [ERROR] Git init failed. Make sure Git is installed and in your PATH.
        pause
        exit /b 1
    )
)

:: 2. Configure remote origin
echo [INFO] Configuring remote origin...
git remote remove origin >nul 2>&1
git remote add origin https://github.com/Heerav04/Vortex.git
if %errorlevel% neq 0 (
    echo [ERROR] Failed to add remote origin.
    pause
    exit /b 1
)

:: 3. Set branch to main
echo [INFO] Configuring branch to main...
git branch -M main

:: 4. Add all files
echo [INFO] Staging all files...
git add .
if %errorlevel% neq 0 (
    echo [ERROR] Git add failed.
    pause
    exit /b 1
)

:: 5. Commit changes
echo [INFO] Committing changes...
git commit -m "feat: configure installer URLs for Heerav04/Vortex, setup local fallback, and build landing page"
if %errorlevel% neq 0 (
    echo [WARNING] Nothing new to commit or commit failed.
)

:: 6. Push to remote
echo.
echo [INFO] Pushing changes to GitHub (Heerav04/Vortex)...
echo Note: If your remote repository already contains files (like a README or license),
echo a normal push might fail.
echo.
set /p force="Do you want to force push to overwrite remote files? (Y/N): "

if /i "%force%"=="Y" (
    echo [INFO] Performing force push...
    git push -u origin main --force
) else (
    echo [INFO] Performing normal push...
    git push -u origin main
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Push failed. 
    echo If this is a new repository, check if your credentials are set up.
    echo If the push was rejected, try pulling changes first, or run this script again and select 'Y' to force push.
) else (
    echo.
    echo ====================================================
    echo    PUSH COMPLETED SUCCESSFULLY!
    echo ====================================================
)

pause
