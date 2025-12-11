@echo off
cd /d "%~dp0\.."

echo ==================================================
echo Building Nikita with PowerShell
echo ==================================================

powershell -ExecutionPolicy Bypass -File "scripts\build.ps1" -NoTest

if %errorlevel% neq 0 (
    echo Build failed!
    exit /b %errorlevel%
)

echo ==================================================
echo Creating Windows installer
echo ==================================================

if exist "%PROGRAMFILES(X86)%\NSIS\makensis.exe" (
    "%PROGRAMFILES(X86)%\NSIS\makensis.exe" "%CD%\scripts\c.installer.nsi"
) else (
    echo NSIS not found. Please install NSIS from https://nsis.sourceforge.io/
    exit /b 1
)

echo ==================================================
echo Build and installer creation completed!
echo ==================================================