@echo off
title Vortex AI OS Setup & Onboarding Wizard
echo ====================================================
echo      VORTEX AI OS - WINDOWS APP INSTALLER/SETUP
echo ====================================================
echo.

:: 1. Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo Please install Python 3.12+ from python.org and try again.
    pause
    exit /b 1
)

:: 2. Check virtual environment
if not exist ".venv" (
    echo [INFO] Creating Python virtual environment (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: 3. Activate virtual environment
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

:: 4. Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

:: 5. Install requirements
echo [INFO] Installing core requirements from vortex/requirements.txt...
pip install -r vortex\requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Core dependency installation failed.
    pause
    exit /b 1
)

:: 6. Install dashboard requirements
echo [INFO] Installing dashboard analytics dependencies...
pip install streamlit pandas plotly
if %errorlevel% neq 0 (
    echo [WARNING] Failed to install Streamlit dashboard requirements.
)

:: 7. Launch main program
echo [INFO] Launching Vortex AI OS Onboarding Setup Wizard...
cd vortex
python main.py
if %errorlevel% neq 0 (
    echo [ERROR] Vortex exited with error code %errorlevel%.
)

pause
