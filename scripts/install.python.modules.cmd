@echo off
cd /d "%~dp0\.."

echo ==================================================
echo Installing Python dependencies for Nikita
echo ==================================================

if exist "requirements.win" (
    echo Installing from requirements.win...
    pip install -r requirements.win
) else (
    echo requirements.win not found, installing basic packages...
    pip install psutil requests clickhouse_driver cherrypy python-dotenv redis pyinstaller cython
)

if %errorlevel% neq 0 (
    echo Failed to install Python packages!
    exit /b %errorlevel%
)

echo ==================================================
echo Python dependencies installed successfully
echo ==================================================