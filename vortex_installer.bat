@echo off
title Vortex AI OS - Web Installer
color 0b
echo ====================================================
echo             VORTEX AI OS - WEB INSTALLER
echo ====================================================
echo.
echo This installer will download and configure Vortex AI OS
echo on your system.
echo.
echo Destination Directory: %USERPROFILE%\VortexAI
echo.
set /p confirm="Do you want to proceed with the installation? (Y/N): "
if /i "%confirm%" neq "Y" (
    echo Installation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/5] Creating installation directory...
set "INSTALL_DIR=%USERPROFILE%\VortexAI"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: Detect if running in local test mode (i.e. if the vortex folder exists adjacent to this script)
if exist "%~dp0vortex" (
    echo [INFO] Local repository source detected.
    echo [INFO] Copying local files to %INSTALL_DIR% for local setup...
    xcopy "%~dp0vortex" "%INSTALL_DIR%\vortex" /e /i /h /y >nul
    xcopy "%~dp0website" "%INSTALL_DIR%\website" /e /i /h /y >nul
    copy "%~dp0setup.bat" "%INSTALL_DIR%\" >nul
    copy "%~dp0README.md" "%INSTALL_DIR%\" >nul
    copy "%~dp0VORTEX_ENTERPRISE_TECHNICAL_REPORT.md" "%INSTALL_DIR%\" >nul
    goto after_download
)

echo.
echo [2/5] Downloading Vortex AI OS from GitHub...
:: REPLACE THIS URL WITH YOUR ACTUAL GITHUB REPOSITORY ZIP LINK
:: Format: https://github.com/USER/REPO/archive/refs/heads/BRANCH.zip
set "REPO_ZIP_URL=https://github.com/Heerav04/Vortex/archive/refs/heads/main.zip"
set "TEMP_ZIP=%TEMP%\vortex_temp.zip"

powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%REPO_ZIP_URL%' -OutFile '%TEMP_ZIP%'"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to download the files. Please check your internet connection or the repository URL.
    pause
    exit /b 1
)

echo.
echo [3/5] Extracting files...
set "EXTRACT_TEMP=%TEMP%\vortex_extracted"
if exist "%EXTRACT_TEMP%" rmdir /s /q "%EXTRACT_TEMP%"
mkdir "%EXTRACT_TEMP%"

powershell -Command "Expand-Archive -Path '%TEMP_ZIP%' -DestinationPath '%EXTRACT_TEMP%' -Force"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to extract files.
    pause
    exit /b 1
)

:: GitHub wraps the zip contents in a folder named like '<repo-name>-<branch-name>'
:: Move the contents of that folder directly to the install directory
echo [INFO] Moving files to %INSTALL_DIR%...
for /d %%d in ("%EXTRACT_TEMP%\*") do (
    xcopy "%%d" "%INSTALL_DIR%" /e /i /h /y >nul
)

:: Clean up temp files
del "%TEMP_ZIP%"
rmdir /s /q "%EXTRACT_TEMP%"

:after_download
echo.
echo [4/5] Running Vortex Environment Setup...
cd /d "%INSTALL_DIR%"
call setup.bat
if %errorlevel% neq 0 (
    echo [ERROR] Environment setup failed.
    pause
    exit /b 1
)

echo.
echo [5/5] Creating Desktop Shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('$HOME\Desktop\Vortex AI OS.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\setup.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = 'shell32.dll,13'; $Shortcut.Save()"
if %errorlevel% neq 0 (
    echo [WARNING] Failed to create desktop shortcut.
) else (
    echo [INFO] Shortcut 'Vortex AI OS' successfully created on your Desktop.
)

echo.
echo ====================================================
echo    INSTALLATION COMPLETE!
echo    You can now run Vortex using the desktop shortcut.
echo ====================================================
echo.
pause
