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
powershell -ExecutionPolicy Bypass -File "scripts\build.ps1" -Optimize -NoTest

if %errorlevel% neq 0 (
    echo.
    echo Build failed!
    pause
    exit /b %errorlevel%
)

echo.
echo Creating Windows installer...
if exist "%PROGRAMFILES(X86)%\NSIS\makensis.exe" (
    "%PROGRAMFILES(X86)%\NSIS\makensis.exe" "%CD%\scripts\c.installer.nsi"
) else if exist "%PROGRAMFILES%\NSIS\makensis.exe" (
    "%PROGRAMFILES%\NSIS\makensis.exe" "%CD%\scripts\c.installer.nsi"
) else (
    echo.
    echo ERROR: NSIS not found!
    echo Please install NSIS from https://nsis.sourceforge.io/
    echo.
    pause
    exit /b 1
)

if %errorlevel% neq 0 (
    echo.
    echo Installer creation failed!
    pause
    exit /b %errorlevel%
)

echo.
echo ==================================================
echo SUCCESS: Windows distribution created!
echo ==================================================
echo.
echo Installer: Nikita.setup.%date%.exe
echo.
pause"