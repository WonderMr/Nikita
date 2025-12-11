@echo off
cd /d "%~dp0\.."
cls

echo ==================================================
echo Nikita Windows Distribution Builder
echo ==================================================

echo Stopping and removing existing service...
if exist ".\dist\Nikita\Nikita.exe" (
    .\dist\Nikita\Nikita.exe stop 2>nul
    .\dist\Nikita\Nikita.exe remove 2>nul
)

echo.
echo Building application with PowerShell...
echo ==================================================
powershell -ExecutionPolicy Bypass -File "scripts\build.ps1" -Optimize -NoTest

if %errorlevel% neq 0 (
    echo.
    echo ==================================================
    echo ERROR: Build failed with exit code %errorlevel%!
    echo ==================================================
    echo The build process encountered an error and cannot continue.
    echo Please check the error messages above.
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo ==================================================
echo Build completed successfully!
echo ==================================================

echo.
echo Creating Windows installer...
echo ==================================================
powershell -ExecutionPolicy Bypass -File "scripts\create-installer.ps1"

if %errorlevel% neq 0 (
    echo.
    echo ==================================================
    echo ERROR: Installer creation failed with exit code %errorlevel%!
    echo ==================================================
    echo The installer creation process encountered an error.
    echo Please check the error messages above.
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo ==================================================
echo SUCCESS: Windows distribution created!
echo ==================================================
echo.
pause